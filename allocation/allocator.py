from ortools.sat.python import cp_model


class ServerAllocationSolutionPrinter(cp_model.CpSolverSolutionCallback):

    def __init__(self, mem_alloc, cpu_alloc,
                 servers_memory, servers_cpu,
                 tasks_count, num_sols_required):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._mem_alloc = mem_alloc
        self._cpu_alloc = cpu_alloc

        self._servers = len(servers_memory)
        self._tasks_count = tasks_count

        self._servers_memory = servers_memory
        self._servers_cpu = servers_cpu

        self._num_solutions = num_sols_required
        self._solution_count = 0
        self._solutions = []

    def on_solution_callback(self):
        if self._solution_count < self._num_solutions:
            solution = []
            for s in range(self._servers):
                for t in range(self._tasks_count):
                    if self.Value(self._mem_alloc[(t, s)]) > 0 and self.Value(self._cpu_alloc[(t, s)]) > 0:
                        solution.append((t, s))

            self._solutions.append(solution)
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

    def get_solutions(self):
        return self._solutions


def enforce_mem_cpu_correlated(model, t, s, cpu_alloc, memory_alloc, tasks_cpu, tasks_memory):
    b_same = model.NewBoolVar('b_same')
    model.Add(cpu_alloc[(t, s)] == tasks_cpu[t]).OnlyEnforceIf(b_same)
    model.Add(cpu_alloc[(t, s)] != tasks_cpu[t]).OnlyEnforceIf(b_same.Not())
    model.Add(memory_alloc[(t, s)] == tasks_memory[t]).OnlyEnforceIf(b_same)
    model.Add(memory_alloc[(t, s)] == 0).OnlyEnforceIf(b_same.Not())


def enforce_cpu_allocation(model, t, s, cpu_alloc, tasks_cpu):
    b_cpu = model.NewBoolVar('b_cpu')
    # Implement b_mem == (memory_alloc[(t, s)] == tasks_memory[t])
    model.Add(cpu_alloc[(t, s)] != tasks_cpu[t]).OnlyEnforceIf(b_cpu.Not())
    model.Add(cpu_alloc[(t, s)] == tasks_cpu[t]).OnlyEnforceIf(b_cpu)
    # Memory is either 0 or tasks_memory[t]
    model.Add(cpu_alloc[(t, s)] == 0).OnlyEnforceIf(b_cpu.Not())


def enforce_mem_allocation(model, t, s, memory_alloc, tasks_memory):
    b_mem = model.NewBoolVar('b_mem')
    # Implement b_mem == (memory_alloc[(t, s)] == tasks_memory[t])
    model.Add(memory_alloc[(t, s)] != tasks_memory[t]).OnlyEnforceIf(b_mem.Not())
    model.Add(memory_alloc[(t, s)] == tasks_memory[t]).OnlyEnforceIf(b_mem)
    # Memory is either 0 or tasks_memory[t]
    model.Add(memory_alloc[(t, s)] == 0).OnlyEnforceIf(b_mem.Not())


def enforce_anti_affinity(model, cpu_alloc, task_anti_affinity, all_servers):
    for (t1, t2) in task_anti_affinity:
        for s in all_servers:
            t2_assigned = model.NewBoolVar("t2_assigned")
            model.Add(cpu_alloc[t2, s] > 0).OnlyEnforceIf(t2_assigned)
            model.Add(cpu_alloc[t2, s] == 0).OnlyEnforceIf(t2_assigned.Not())

            model.Add(cpu_alloc[t1, s] == 0).OnlyEnforceIf(t2_assigned)


def allocate_tasks_servers(servers_memory, servers_cpu,
                           tasks_memory, tasks_cpu,
                           task_anti_affinity=None,
                           num_solutions=1):

    all_servers = range(len(servers_memory))
    all_tasks = range(len(tasks_memory))

    # Creates the model.
    model = cp_model.CpModel()

    # memory_alloc[(t, s)]: task 't' runs on server 's' with memory value memory_alloc[(t, s)]
    # cpu_alloc[(t, s)]: task 't' runs on server 's' with cpu count cpu_alloc[(t, s)]
    memory_alloc = {}
    cpu_alloc = {}
    for t in all_tasks:
        for s in all_servers:
            memory_alloc[(t, s)] = model.NewIntVar(0, max(servers_memory), 'memory_alloc_s%i_t%i' % (t, s))
            cpu_alloc[(t, s)] = model.NewIntVar(0, max(servers_cpu), 'cpu_alloc_s%i_t%i' % (t, s))

    # Make sure memory allocation is exact per task
    # (Otherwise may be split between servers, e.g. S1 will get T0 with 1GB and S2 will get T0 with the rest 3GB)
    for t in all_tasks:
        for s in all_servers:
            enforce_mem_allocation(model, t, s, memory_alloc, tasks_memory)
            enforce_cpu_allocation(model, t, s, cpu_alloc, tasks_cpu)

    # Each task can run only on one server
    for t in all_tasks:
        model.Add(sum(memory_alloc[(t, s)] for s in all_servers) == tasks_memory[t])
        model.Add(sum(cpu_alloc[(t, s)] for s in all_servers) == tasks_cpu[t])

    # Each server can run only tasks smaller than the the total amount of memory
    for s in all_servers:
        model.Add(sum(memory_alloc[(t, s)] for t in all_tasks) <= servers_memory[s])
        model.Add(sum(cpu_alloc[(t, s)] for t in all_tasks) <= servers_cpu[s])

    for t in all_tasks:
        for s in all_servers:
            enforce_mem_cpu_correlated(model, t, s, cpu_alloc, memory_alloc, tasks_cpu, tasks_memory)

    if task_anti_affinity:
        enforce_anti_affinity(model, cpu_alloc, task_anti_affinity, all_servers)

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    # Display the first five solutions.

    solution_printer = ServerAllocationSolutionPrinter(memory_alloc, cpu_alloc,
                                                       servers_memory, servers_cpu,
                                                       len(tasks_memory), num_solutions)
    status = solver.SearchForAllSolutions(model, solution_printer)
    solutions = solution_printer.get_solutions()

    #print('Solve status: %s' % solver.StatusName(status))
    #if status == cp_model.OPTIMAL:
    #    print('Optimal objective value: %i' % solver.ObjectiveValue())

    # Statistics.
    #print()
    #print('Statistics')
    #print('  - conflicts       : %i' % solver.NumConflicts())
    #print('  - branches        : %i' % solver.NumBranches())
    #print('  - wall time       : %f s' % solver.WallTime())
    #print('  - solutions found : %i' % solution_printer.solution_count())

    return solutions

