import unittest
from allocation import allocator


servers = [allocator.Server(32, 10, 1000), allocator.Server(32, 12, 1000),
           allocator.Server(32, 8, 1000), allocator.Server(16, 12, 1000)]

tasks = [allocator.App(4, 2, 10), allocator.App(8, 4, 10),
         allocator.App(12, 12, 10), allocator.App(16, 8, 10),
         allocator.App(2, 1, 10), allocator.App(8, 2, 10),
         allocator.App(16, 4, 10), allocator.App(10, 4, 10),
         allocator.App(4, 2, 10), allocator.App(8, 2, 10)]

task_anti_affinity = [(1, 4), (3, 7), (3, 4), (6, 8)]


class TestAllocator(unittest.TestCase):
    def test_allocate_tasks_servers(self):
        alloc = allocator.Allocator(servers, tasks)
        self.assertEqual([[(0, 0),
                           (5, 0),
                           (6, 0),
                           (8, 0),
                           (3, 1),
                           (7, 1),
                           (1, 2),
                           (4, 2),
                           (9, 2),
                           (2, 3)]], alloc.allocate())

    def test_allocate_tasks_servers_single_server_task(self):
        alloc = allocator.Allocator([allocator.Server(32, 16, 1000)], [allocator.App(12, 12, 500)])
        self.assertEqual([[(0, 0)]], alloc.allocate())

    def test_allocate_tasks_servers_more_servers(self):
        alloc = allocator.Allocator([allocator.Server(32, 16, 1000), allocator.Server(32, 16, 1000)],
                                    [allocator.App(12, 12, 500)])
        result = alloc.allocate()
        self.assertTrue(result == [[(0, 0)]] or result == [[(0, 1)]])

    def test_allocate_tasks_servers_more_tasks(self):
        alloc = allocator.Allocator([allocator.Server(32, 16, 1000)],
                                    [allocator.App(4, 4, 100), allocator.App(4, 4, 100), allocator.App(4, 4, 100)])
        result = alloc.allocate()
        self.assertEqual([[(0, 0), (1, 0), (2, 0)]], result)

    def test_allocate_tasks_servers_not_enough_cpu(self):
        alloc = allocator.Allocator([allocator.Server(8, 16, 1000)],
                                    [allocator.App(4, 4, 100), allocator.App(4, 4, 100), allocator.App(4, 4, 100)])
        result = alloc.allocate()
        self.assertEqual([[]], result)

    def test_allocate_tasks_servers_not_enough_mem(self):
        alloc = allocator.Allocator([allocator.Server(8, 16, 1000)],
                                    [allocator.App(4, 12, 100), allocator.App(4, 12, 100), allocator.App(4, 4, 100)])
        result = alloc.allocate()
        self.assertEqual([[]], result)

