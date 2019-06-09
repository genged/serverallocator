from ortools.sat.python import cp_model


class ServerAllocationSolutionPrinter(cp_model.CpSolverSolutionCallback):

    def __init__(self, mem_alloc, cpu_alloc,
                 servers_memory, servers_cpu,
                 tasks, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._mem_alloc = mem_alloc
        self._cpu_alloc = cpu_alloc

        self._servers = len(servers_memory)
        self._tasks = tasks

        self._servers_memory = servers_memory
        self._servers_cpu = servers_cpu

        self._solutions = set(sols)
        self._solution_count = 0

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print("Solution", self._solution_count)
            for s in range(self._servers):
                print("Server ", s, "(Mem %s, CPU %s)" % (self._servers_memory[s], self._servers_cpu[s]))
                for t in range(self._tasks):
                    if self.Value(self._mem_alloc[(t, s)]) > 0 and self.Value(self._cpu_alloc[(t, s)]) > 0:
                        print("\tTask ", t,
                              "(Mem %s, CPU %s)" % (self.Value(self._mem_alloc[(t, s)]), self.Value(self._cpu_alloc[(t, s)])))
            print()

        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def main():
    # Data.
    servers = 4
    servers_memory = [
        32, 48, 32, 16
    ]
    servers_cpu = [
        10, 12, 8, 12
    ]
    tasks = 10
    tasks_memory = [
        4, 8,  12, 16, 2,
        8, 16, 10, 4,  8
    ]
    tasks_cpu = [
        2, 4,  12, 8, 1,
        2, 4,  4,  2, 2
    ]

    #    t1 t2 t3
    # s1 4  0
    # s2 0  8
    # s3 0  0

    all_servers = range(servers)
    all_tasks = range(tasks)

    # Creates the model.
    model = cp_model.CpModel()

    # allocation[(t, s)]: task 't' runs on server 's'.
    memory_alloc = {}
    cpu_alloc = {}
    for t in all_tasks:
        for s in all_servers:
            memory_alloc[(t, s)] = model.NewIntVar(0, max(servers_memory), 'memory_alloc_s%i_t%i' % (t, s))
            cpu_alloc[(t, s)] = model.NewIntVar(0, max(servers_cpu), 'cpu_alloc_s%i_t%i' % (t, s))

    # Each task can run only on one server
    for t in all_tasks:
        model.Add(sum(memory_alloc[(t, s)] for s in all_servers) == tasks_memory[t])
        model.Add(sum(cpu_alloc[(t, s)] for s in all_servers) == tasks_cpu[t])

    # Make sure memory allocation is exact per task
    # (Otherwise may be split between servers, e.g. S1 will get T0 with 1GB and S2 will get T0 with the rest 3GB)
    for t in all_tasks:
        for s in all_servers:
            b_mem = model.NewBoolVar('b_mem')
            # Implement b_mem == (memory_alloc[(t, s)] == tasks_memory[t])
            model.Add(memory_alloc[(t, s)] != tasks_memory[t]).OnlyEnforceIf(b_mem.Not())
            model.Add(memory_alloc[(t, s)] == tasks_memory[t]).OnlyEnforceIf(b_mem)

            # Memory is either 0 or tasks_memory[t]
            model.Add(memory_alloc[(t, s)] == 0).OnlyEnforceIf(b_mem.Not())

            # ----

            b_cpu = model.NewBoolVar('b_cpu')
            # Implement b_mem == (memory_alloc[(t, s)] == tasks_memory[t])
            model.Add(cpu_alloc[(t, s)] != tasks_cpu[t]).OnlyEnforceIf(b_cpu.Not())
            model.Add(cpu_alloc[(t, s)] == tasks_cpu[t]).OnlyEnforceIf(b_cpu)

            # Memory is either 0 or tasks_memory[t]
            model.Add(cpu_alloc[(t, s)] == 0).OnlyEnforceIf(b_cpu.Not())

    # Each server can run only tasks smaller than the the total amount of memory
    for s in all_servers:
        model.Add(sum(memory_alloc[(t, s)] for t in all_tasks) <= servers_memory[s])
        model.Add(sum(cpu_alloc[(t, s)] for t in all_tasks) <= servers_cpu[s])

    for t in all_tasks:
        for s in all_servers:
            b_same = model.NewBoolVar('b_same')
            model.Add(cpu_alloc[(t, s)] == tasks_cpu[t]).OnlyEnforceIf(b_same)
            model.Add(cpu_alloc[(t, s)] != tasks_cpu[t]).OnlyEnforceIf(b_same.Not())

            model.Add(memory_alloc[(t, s)] == tasks_memory[t]).OnlyEnforceIf(b_same)
            model.Add(memory_alloc[(t, s)] == 0).OnlyEnforceIf(b_same.Not())

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0
    # Display the first five solutions.
    a_few_solutions = range(2)
    solution_printer = ServerAllocationSolutionPrinter(memory_alloc, cpu_alloc,
                                                       servers_memory, servers_cpu,
                                                       tasks, a_few_solutions)
    solver.SearchForAllSolutions(model, solution_printer)

    # Statistics.
    print()
    print('Statistics')
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - wall time       : %f s' % solver.WallTime())
    print('  - solutions found : %i' % solution_printer.solution_count())


if __name__ == '__main__':
    main()