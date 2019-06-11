import yaml
import argparse
import itertools
from pathlib import Path

from allocation.allocation_config import get_config_data
from allocation.allocator import allocate_tasks_servers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resources-file', type=Path, help='Resources file path', required=True)
    parser.add_argument('--allocation-file', type=Path, help='Allocations file path', required=True)
    p = parser.parse_args()

    nodes_cpu, nodes_memory, \
        apps_cpu, apps_memory, \
        task_anti_affinity, \
        data_dict = get_config_data(p.resources_file)

    allocations = allocate_tasks_servers(nodes_memory, nodes_cpu, apps_memory, apps_cpu,
                                         num_solutions=task_anti_affinity)

    allocation_dict = {}
    for alloc in allocations:
        for s in itertools.groupby(alloc, lambda x: x[1]):
            node_id = s[0]
            node_data = data_dict["nodes"][node_id]
            print("Server %s - %s (Mem %s, CPU %s)" % (node_id, node_data["name"],
                                                       node_data["resources"]["memory"], node_data["resources"]["cpu"]))
            allocation_dict[node_data["name"]] = {
                "apps": []
            }
            for t in s[1]:
                task_id = t[0]
                task_data = data_dict["apps"][task_id]
                allocation_dict[node_data["name"]]["apps"].append(task_data["name"])
                print("\tApp %s - %s (Mem %s, CPU %s)" % (task_id, task_data["name"],
                                                          task_data["resources"]["memory"], task_data["resources"]["cpu"]))

    print(allocation_dict)
    with p.allocation_file.open(mode='w') as af:
        af.write(yaml.dump(allocation_dict))


if __name__ == '__main__':
    main()