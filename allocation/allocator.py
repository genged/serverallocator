import itertools
import string
import random

from dataclasses import dataclass, field
from typing import List, Dict

# ortools are not in requirements.txt
from ortools.sat.python import cp_model


def enforce_resources_correlated(model, t, s, r1, r2, alloc, tasks):
    # no puppy will die if t-> task, s-> server
    # give docstrings with types
    b_same = model.NewBoolVar('b_same_%s_%s' % (r1, r2))
    model.Add(alloc[(t, s, r1)] == tasks[r1][t]).OnlyEnforceIf(b_same)
    model.Add(alloc[(t, s, r1)] != tasks[r1][t]).OnlyEnforceIf(b_same.Not())

    model.Add(alloc[(t, s, r2)] == tasks[r2][t]).OnlyEnforceIf(b_same)
    model.Add(alloc[(t, s, r2)] == 0).OnlyEnforceIf(b_same.Not())


def enforce_mem_cpu_correlated(model, t, s, cpu_alloc, memory_alloc, tasks_cpu, tasks_memory):
    # this one and above are pretty similar...
    # no puppy will die if t-> task, s-> server
    b_same = model.NewBoolVar('b_same')
    model.Add(cpu_alloc[(t, s)] == tasks_cpu[t]).OnlyEnforceIf(b_same)
    model.Add(cpu_alloc[(t, s)] != tasks_cpu[t]).OnlyEnforceIf(b_same.Not())

    model.Add(memory_alloc[(t, s)] == tasks_memory[t]).OnlyEnforceIf(b_same)
    model.Add(memory_alloc[(t, s)] == 0).OnlyEnforceIf(b_same.Not())


def enforce_resource_allocation(model, resource, task, server, alloc, tasks):
    b_resource = model.NewBoolVar('b_resource')
    idx = (task, server, resource)
    # Implement b_resource == (alloc[(t, s, r)] == tasks[r][t])
    model.Add(alloc[idx] != tasks[resource][task]).OnlyEnforceIf(b_resource.Not())
    model.Add(alloc[idx] == tasks[resource][task]).OnlyEnforceIf(b_resource)
    # Resource is either 0 or tasks[resource][task]
    model.Add(alloc[idx] == 0).OnlyEnforceIf(b_resource.Not())


def enforce_anti_affinity(model, alloc, task_anti_affinity, all_servers, all_resources):
    # 1. give meaningful variable names: no puppy will die if variable will be named 'server' instead of 's'
    # 2. arrow anti-pattern: too many nested for-s. use itertools.product
    # 3. no puppy will die if t-> task, s-> server
    for (t1, t2) in task_anti_affinity:
        for s in all_servers:
            for r in all_resources:
                t2_assigned = model.NewBoolVar("t2_assigned_%s" % r)
                model.Add(alloc[t2, s, r] > 0).OnlyEnforceIf(t2_assigned)
                model.Add(alloc[t2, s, r] == 0).OnlyEnforceIf(t2_assigned.Not())

                model.Add(alloc[t1, s, r] == 0).OnlyEnforceIf(t2_assigned)


def allocate_tasks_servers(servers: Dict[str, List],
                           tasks: Dict[str, List],
                           task_anti_affinity=None,
                           minimize=True):
    # too long function...

    if not servers or not tasks:
        raise ValueError("Incorrect arguments passed")

    # what is '2'? and why '2'?
    for rlist1, rlist2 in itertools.combinations(servers.values(), 2):
        if len(rlist1) != len(rlist2):
            raise ValueError("Servers CPU and Memory should be of the same length")

    # .values() is enouph
    all_servers = range(max(len(v) for k, v in servers.items()))
    # .values() is enouph
    all_tasks = range(max(len(v) for k, v in tasks.items()))
    all_resources = servers.keys()
    # Creates the model.
    model = cp_model.CpModel()

    # resource_alloc[(t, s, r)]: task 't' runs on server 's' with resource 'r' has value resource_alloc[(t, s, r)]
    resource_alloc = {}
    # 1.try to use itertools. its more laconic. and no arrow anti-pattern
    #   for task, server, resource in product(all_tasks, all_servers, all_resources)
    # 2. you're lucky that every list size < 100....
    # 3. no puppy will die if t-> task, s-> server
    for t in all_tasks:
        for s in all_servers:
            for r in all_resources:
                resource_alloc[(t, s, r)] = model.NewIntVar(0, max(servers[r]),
                                                            'resource_alloc_t%i_s%i_r%s' % (t, s, r))

    # Make sure memory allocation is exact per task
    # (Otherwise may be split between servers, e.g. S1 will get T0 with 1GB and S2 will get T0 with the rest 3GB)
    # 1. try to use itertools. its more laconic. and no arrow anti-pattern
    # 2. you're lucky that every list size < 100....
    # 3. no puppy will die if t-> task, s-> server
    # 4. gi've comment why do you need two different loops: this one and one above
    for t in all_tasks:
        for s in all_servers:
            for r in all_resources:
                enforce_resource_allocation(model, r, t, s, resource_alloc, tasks)

    # Each task can run only on one server
    # try to use itertools. its more laconic. and no arrow anti-pattern
    # 2. you're lucky that every list size < 100....
    # 3. no puppy will die if t-> task, r-> resource
    for t in all_tasks:
        for r in all_resources:
            model.Add(sum(resource_alloc[(t, s, r)] for s in all_servers) == tasks[r][t])

    # Each server can run only tasks smaller than the the total amount of memory
    # 1. try to use itertools. its more laconic. and no arrow anti-pattern
    # 2. you're lucky that every list size < 100....

    for s in all_servers:
        for r in all_resources:
            model.Add(sum(resource_alloc[(t, s, r)] for t in all_tasks) <= servers[r][s])

    # try to use itertools. its more laconic. and no arrow anti-pattern
    # 2. you're lucky that every list size < 100....
    # 3. no puppy will die if t-> task, s-> server
    # 4. what is the purpose of the loop?
    for t in all_tasks:
        for s in all_servers:
            for (r1, r2) in itertools.combinations(all_resources, 2):
                enforce_resources_correlated(model, t, s, r1, r2, resource_alloc, tasks)

    if task_anti_affinity:
        enforce_anti_affinity(model, resource_alloc, task_anti_affinity, all_servers, all_resources)

    if minimize:
        server_allocated = [model.NewBoolVar('server_allocated_%i' % s) for s in all_servers]
        for s in all_servers:
            for r in all_resources:
                model.Add(sum(resource_alloc[(t, s, r)] for t in all_tasks) > 0).OnlyEnforceIf(server_allocated[s])
                model.Add(sum(resource_alloc[(t, s, r)] for t in all_tasks) <= 0).OnlyEnforceIf(server_allocated[s].Not())

        model.Add(sum(server_allocated) <= len(all_servers))
        model.Minimize(sum(server_allocated))

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0

    status = solver.Solve(model)
    solution = []
    # avoid arrow AP: if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}: return xyz
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # try to use itertools. its more laconic. and no arrow anti-pattern
        for s in all_servers:
            for t in all_tasks:
                # but not here - really hard to understand. I'd do follings as:
                #   for resource in all_resources:
                #       if solver.Value(resource_alloc[(task, server, resource)]) <= 0:
                #          break
                #   else:
                #       # all is OK
                #       solution.append((t, s))
                if all(solver.Value(resource_alloc[(t, s, r)]) > 0 for r in all_resources):
                    solution.append((t, s))

    # print('Solve status: %s' % solver.StatusName(status))
    #
    # print()
    # print('Statistics')
    # print('  - conflicts       : %i' % solver.NumConflicts())
    # print('  - branches        : %i' % solver.NumBranches())
    # print('  - wall time       : %f s' % solver.WallTime())

    return solution

# ----


@dataclass
class AllocationResource:
    memory: int
    cpu: int
    disk: int


def random_name(prefix="name", name_len=10):
    letters = string.ascii_lowercase
    rand_str = ''.join(random.choices(letters, k=name_len))
    return "%s-%s" % (prefix, rand_str)


# well, looks like there's not too much "payload" (BL) un the function
# maybe just use: random_server_name = partial(random_name, "server")
def random_server_name(prefix="server"):
    return random_name(prefix)


# well, looks like there's not too much "payload" (BL) un the function
# maybe just use: random_server_name = partial(random_name, "app")
def random_app_name(prefix="app"):
    return random_name(prefix)


@dataclass
class Server(AllocationResource):
    name: str = field(default_factory=random_server_name)


@dataclass
class App(AllocationResource):
    name: str = field(default_factory=random_app_name)
    antiAffinityLabels: List[str] = field(default=None)


class Allocator:
    def __init__(self, servers: List[Server], apps: List[App], minimize=True):
        self.servers = servers
        self.apps = apps
        self.minimize = minimize

    def allocate(self):
        servers = {}
        for field_name in AllocationResource.__dataclass_fields__.keys():
            servers[field_name] = [getattr(s, field_name) for s in self.servers]

        apps = {}
        for field_name in AllocationResource.__dataclass_fields__.keys():
            apps[field_name] = [getattr(a, field_name) for a in self.apps]

        # Create anti-affinity pairs of tasks (tasks that cannot run on the same server)
        # E.g. [(1,2), (4,6)] - App 1 and 2 cannot run on same server, App 4 and 6 cannot run on same server
        task_anti_affinity = []
        labels = {}
        for appid, app in enumerate(self.apps):
            if app.antiAffinityLabels:
                for label in app.antiAffinityLabels:
                    labels.setdefault(label, []).append(appid)

        if labels:
            for app_list in labels.values():
                task_anti_affinity.extend(list(itertools.combinations(app_list, 2)))

        alloc = allocate_tasks_servers(servers, apps, minimize=self.minimize, task_anti_affinity=task_anti_affinity)
        res = []

        def get_node(app_node_tuple: tuple):
            return app_node_tuple[1]

        def get_app(app_node_tuple: tuple):
            return app_node_tuple[0]

        for node in itertools.groupby(alloc, get_node):
            res_alloc = {}
            node_id = node[0]
            node_tuples = node[1]
            node_data = self.servers[node_id]

            apps = [get_app(app_node_tuple) for app_node_tuple in node_tuples]
            res_alloc["node"] = node_data
            res_alloc["apps"] = [self.apps[app_id] for app_id in apps]
            res.append(res_alloc)

        return res



if __name__ == "__main__":
    allocator = Allocator([Server(32, 12, 1000)], [App(12, 2, 1000)])
    print(allocator.allocate())

