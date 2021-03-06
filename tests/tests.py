# # Sample Data
# servers_memory = [
#     32, 32, 32, 16
# ]
# servers_cpu = [
#     10, 12, 8, 12
# ]
# tasks_memory = [
#     4, 8,  12, 16, 2,
#     8, 16, 10, 4,  8
# ]
# tasks_cpu = [
#     2, 4,  12, 8, 1,
#     2, 4,  4,  2, 2
# ]
# task_anti_affinity = [(1, 4), (3, 7), (3, 4), (6, 8)]
if __name__ == "__main__":
    from src.allocation import allocator
    alloc = allocator.Allocator([allocator.Server(32, 16, 1000)], [allocator.App(12, 12, 500)])
    print(alloc.allocate())


