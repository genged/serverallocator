from pathlib import Path
import yaml
import humanfriendly
import itertools


class ConfigException(Exception):
    pass


def parse_config(yaml_dict: dict) -> tuple:
    nodes = yaml_dict["nodes"]
    apps = yaml_dict["apps"]
    nodes_cpu = []
    nodes_memory = []
    for node in nodes:
        resources = node["resources"]
        nodes_cpu.append(resources["cpu"])
        nodes_memory.append(mem_to_gib(resources["memory"]))

    apps_memory = []
    apps_cpu = []
    labels = {}
    for id, app in enumerate(apps):
        app_name = app["name"]
        resources = app["resources"]
        apps_cpu.append(resources["cpu"])
        apps_memory.append(mem_to_gib(resources["memory"]))
        if app.get("antiAffinityLabels", None):
            for label in app["antiAffinityLabels"]:
                if not labels.get(label, None):
                    labels[label] = [(app_name, id)]
                else:
                    labels[label].append((app_name, id))

    task_anti_affinity = []
    for key in labels.keys():
        idlist = [id for (app_name, id) in labels[key]]
        task_anti_affinity.extend(list(itertools.combinations(idlist, 2)))

    return nodes_cpu, nodes_memory, apps_cpu, apps_memory, task_anti_affinity, yaml_dict


def mem_to_gib(mem_str: str) -> int:
    BYTES_IN_GiB = 1024 ** 3
    return humanfriendly.parse_size(mem_str) // BYTES_IN_GiB


def get_config_data(yaml_path: Path) -> tuple:
    with yaml_path.open() as stream:
        try:
            return parse_config(yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            raise ConfigException(exc)


if __name__ == "__main__":
    nodes_cpu, nodes_memory, \
        apps_cpu, apps_memory, \
        task_anti_affinity = get_config_data(Path("resources.yml"))

    print("Nodes CPU", nodes_cpu)
    print("Nodes Mem", nodes_memory)
    print("Apps CPU", apps_cpu)
    print("Apps Mem", apps_memory)
    print("Anti Affinity", task_anti_affinity)

