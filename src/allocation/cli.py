#!/usr/bin/env python

import sys
import yaml
import argparse
import itertools
from pathlib import Path

from . import allocator_config
from . import allocator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resources-file', type=Path, help='Resources file path', required=True)
    parser.add_argument('--allocation-file', type=Path, help='Allocations file path', required=False)
    p = parser.parse_args()

    nodes_cpu, nodes_memory, \
        apps_cpu, apps_memory, \
        task_anti_affinity, \
        data_dict = allocator_config.parse_config(p.resources_file)

    nodes = {
        "memory": nodes_memory,
        "cpu": nodes_cpu
    }
    apps = {
        "memory": apps_memory,
        "cpu": apps_cpu
    }

    allocation = allocator.allocate_tasks_servers(nodes, apps,
                                                  task_anti_affinity=task_anti_affinity)

    allocation_dict = {}
    for s in itertools.groupby(allocation, lambda x: x[1]):
        node_id = s[0]
        node_data = data_dict["nodes"][node_id]
        allocation_dict[node_data["name"]] = {
            "apps": []
        }
        for t in s[1]:
            task_id = t[0]
            task_data = data_dict["apps"][task_id]
            allocation_dict[node_data["name"]]["apps"].append(task_data["name"])

    allocation_file = p.allocation_file
    if not allocation_file:
        allocation_file = sys.stdout

    with allocation_file as af:
        af.write(yaml.dump(allocation_dict))


if __name__ == '__main__':
    main()