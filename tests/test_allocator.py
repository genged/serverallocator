from allocation.allocator import Server, App, Allocator

s1 = Server(32, 16, 1000, name="s1")
s2 = Server(32, 16, 1000, name="s2")


def test_allocate_tasks_servers_single_server_task():
    _a = App(12, 12, 500)
    alloc = Allocator([s1], [_a])
    res = alloc.allocate()

    expected = [
        {
            "node": s1,
            "apps": [_a]
        }
    ]

    assert expected == res


def test_allocate_tasks_servers_more_servers():
    a1 = App(12, 12, 500, name="a1")

    alloc = Allocator([s1, s2], [a1])
    expected1 = [{
        "node": s1,
        "apps": [a1]
    }]
    expected2 = [{
        "node": s2,
        "apps": [a1]
    }]
    assert alloc.allocate() in [expected1, expected2]


def test_allocate_tasks_servers_more_tasks():
    a1 = App(4, 4, 500, name="a1")
    a2 = App(4, 4, 100, name="a2")
    a3 = App(4, 4, 100, name="a3")
    alloc = Allocator([s1], [a1, a2, a3])
    expected = [
        {
            "node": s1,
            "apps": [a1, a2, a3]
        }
    ]
    res = alloc.allocate()
    assert expected == res


def test_allocate_tasks_servers_not_enough_cpu():
    server = Server(8, 16, 1000)
    a1 = App(4, 4, 100)
    a2 = App(4, 4, 100)
    a3 = App(4, 4, 100)
    alloc = Allocator([server],
                      [a1, a2, a3])
    result = alloc.allocate()
    assert [] == result


def test_allocate_tasks_servers_not_enough_mem():
    alloc = Allocator([Server(8, 16, 1000)],
                      [App(4, 12, 100), App(4, 12, 100), App(4, 4, 100)])
    result = alloc.allocate()
    assert [] == result


def test_anti_affinity_cannot_allocate_on_same_server():
    alloc = Allocator([Server(128, 24, 1000)],
                      [App(2, 4, 10, antiAffinityLabels=["label-1"]), App(4, 8, 10, antiAffinityLabels=["label-1"])])
    result = alloc.allocate()
    assert [] == result


if __name__ == "__main__":
    import pytest
    pytest.main()
