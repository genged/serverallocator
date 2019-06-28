from pathlib import Path

from allocation import allocator_config

DATA_PATH = Path(__file__).parent / "data"

def test_small_resources():
    nodes_cpu, nodes_memory, \
        apps_cpu, apps_memory, \
        task_anti_affinity, _ = allocator_config.parse_config(DATA_PATH / "resources_simple.yml")

    assert nodes_cpu == [24]
    assert nodes_memory == [64]
    assert apps_cpu == [2]
    assert apps_memory == [4]


def test_incomplete_resources():
    with pytest.raises(allocator_config.ConfigException) as e:
        nodes_cpu, nodes_memory, \
            apps_cpu, apps_memory, \
            task_anti_affinity, _ = allocator_config.parse_config(DATA_PATH / "resources_no_memory.yml")

    assert "Invalid config file" in str(e.value)


def test_complex_resources():
    nodes_cpu, nodes_memory, \
        apps_cpu, apps_memory, \
        task_anti_affinity, _ = allocator_config.parse_config(DATA_PATH / "resources_complex.yml")

    assert [24, 24, 24, 24] == nodes_cpu
    assert [(8, 9), (8, 10), (9, 10)] == task_anti_affinity


if __name__ == "__main__":
    import pytest
    pytest.main()
