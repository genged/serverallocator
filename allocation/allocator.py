import itertools
from dataclasses import dataclass
from typing import List, Dict

from ortools.sat.python import cp_model


def enforce_resources_correlated(model, t, s, r1, r2, alloc, tasks):
    b_same = model.NewBoolVar('b_same_%s_%s' % (r1, r2))
    model.Add(alloc[(t, s, r1)] == tasks[r1][t]).OnlyEnforceIf(b_same)
    model.Add(alloc[(t, s, r1)] != tasks[r1][t]).OnlyEnforceIf(b_same.Not())

    model.Add(alloc[(t, s, r2)] == tasks[r2][t]).OnlyEnforceIf(b_same)
    model.Add(alloc[(t, s, r2)] == 0).OnlyEnforceIf(b_same.Not())


def enforce_mem_cpu_correlated(model, t, s, cpu_alloc, memory_alloc, tasks_cpu, tasks_memory):
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

    if not servers or not tasks:
        raise ValueError("Incorrect arguments passed")

    for rlist1, rlist2 in itertools.combinations(servers.values(), 2):
        if len(rlist1) != len(rlist2):
            raise ValueError("Servers CPU and Memory should be of the same length")

    all_servers = range(max(len(v) for k, v in servers.items()))
    all_tasks = range(max(len(v) for k, v in tasks.items()))
    all_resources = servers.keys()
    # Creates the model.
    model = cp_model.CpModel()

    # resource_alloc[(t, s, r)]: task 't' runs on server 's' with resource 'r' has value resource_alloc[(t, s, r)]
    resource_alloc = {}
    for t in all_tasks:
        for s in all_servers:
            for r in all_resources:
                resource_alloc[(t, s, r)] = model.NewIntVar(0, max(servers[r]),
                                                            'resource_alloc_t%i_s%i_r%s' % (t, s, r))

    # Make sure memory allocation is exact per task
    # (Otherwise may be split between servers, e.g. S1 will get T0 with 1GB and S2 will get T0 with the rest 3GB)
    for t in all_tasks:
        for s in all_servers:
            for r in all_resources:
                enforce_resource_allocation(model, r, t, s, resource_alloc, tasks)

    # Each task can run only on one server
    for t in all_tasks:
        for r in all_resources:
            model.Add(sum(resource_alloc[(t, s, r)] for s in all_servers) == tasks[r][t])

    # Each server can run only tasks smaller than the the total amount of memory
    for s in all_servers:
        for r in all_resources:
            model.Add(sum(resource_alloc[(t, s, r)] for t in all_tasks) <= servers[r][s])

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
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for s in all_servers:
            for t in all_tasks:
                if all(solver.Value(resource_alloc[(t, s, r)]) > 0 for r in all_resources):
                    solution.append((t, s))

    solutions = [solution]

    # print('Solve status: %s' % solver.StatusName(status))
    #
    # print()
    # print('Statistics')
    # print('  - conflicts       : %i' % solver.NumConflicts())
    # print('  - branches        : %i' % solver.NumBranches())
    # print('  - wall time       : %f s' % solver.WallTime())

    return solutions

# ----


@dataclass
class AllocationResource:
    memory: int
    cpu: int
    disk: int


@dataclass
class Server(AllocationResource):
    name: str = None
    antiAffinityLabels: List[str] = None


@dataclass
class App(AllocationResource):
    name: str = None
    antiAffinityLabels: List[str] = None


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

        allocations = allocate_tasks_servers(servers, apps, minimize=self.minimize)
        #
        # for alloc in allocations:
        #     for s in itertools.groupby(alloc, lambda x: x[1]):
        #         node_id = s[0]
        #         node_data = servers[node_id]
        #         print("Server %s - %s (Mem %s, CPU %s)" % (node_id, node_data.name,
        #                                                    node_data.memory, node_data.cpu))
        #         allocation_dict[node_data.name] = {
        #             "apps": []
        #         }
        #         for t in s[1]:
        #             task_id = t[0]
        #             task_data = data_dict["apps"][task_id]
        #             allocation_dict[node_data["name"]]["apps"].append(task_data["name"])
        #             print("\tApp %s - %s (Mem %s, CPU %s)" % (task_id, task_data["name"],
        #                                                       task_data["resources"]["memory"], task_data["resources"]["cpu"]))
        #

        return allocations



if __name__ == "__main__":
    allocator = Allocator([Server(32, 12, 1000)], [App(12, 2, 1000)])
    print(allocator.allocate())

