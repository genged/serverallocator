from pathlib import Path
# not in requirements
import yaml
# not in requirements
import humanfriendly
# should be before 3rd parties
import itertools


class ConfigException(Exception):
    pass


def parse_config(yaml_dict: dict) -> tuple:
    # remove 'yaml' from variable name - who cares it is yaml?
    # too long function...
    nodes = yaml_dict["nodes"]
    apps = yaml_dict["apps"]
    # variable namespace clash....
    nodes_cpu = []
    # variable namespace clash....
    nodes_memory = []
    for node in nodes:
        resources = node["resources"]
        nodes_cpu.append(resources["cpu"])
        nodes_memory.append(mem_to_gib(resources["memory"]))

    # variable namespace clash....
    apps_memory = []
    # variable namespace clash....
    apps_cpu = []
    labels = {}
    # id is builtin
    for id, app in enumerate(apps):
        app_name = app["name"]
        resources = app["resources"]
        apps_cpu.append(resources["cpu"])
        apps_memory.append(mem_to_gib(resources["memory"]))
        # if "antiAffinityLabels" not in app:
        #   continue
        if app.get("antiAffinityLabels", None):
            for label in app["antiAffinityLabels"]:
                # if labels was 'defaultdict(list)' following 'if-else' is useless
                # labels[label].append((app_name, id))
                if not labels.get(label, None):
                    labels[label] = [(app_name, id)]
                else:
                    labels[label].append((app_name, id))
    # variable namespace clash....
    task_anti_affinity = []
    # why not just:
    # for values inj labels.values():
    #   idlist = [idx for (app_name, idx) in values]
    for key in labels.keys():
        # id is builtin...
        # is that guaranteed that ID in value is unique?
        idlist = [id for (app_name, id) in labels[key]]
        task_anti_affinity.extend(list(itertools.combinations(idlist, 2)))

    # too many returned values - use data class or namedtuple
    return nodes_cpu, nodes_memory, apps_cpu, apps_memory, task_anti_affinity, yaml_dict


def mem_to_gib(mem_str: str) -> int:
    # this is constant - > remove to outer scope
    BYTES_IN_GiB = 1024 ** 3
    # 1. the only usage of humanfriendly is here... why not just re.match().groupdict() ?
    # 2. assert result is positive (or at least non-zero)
    return humanfriendly.parse_size(mem_str) // BYTES_IN_GiB


def get_config_data(yaml_path: Path) -> tuple:
    with yaml_path.open() as stream:
        try:
            return parse_config(yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            # 1. wrap exception with 'from exc'
            # 2. IOSError/IOError
            raise ConfigException(exc)


if __name__ == "__main__":
    # main function is missing
    nodes_cpu, nodes_memory, \
        apps_cpu, apps_memory, \
        task_anti_affinity = get_config_data(Path("resources.yml"))

    print("Nodes CPU", nodes_cpu)
    print("Nodes Mem", nodes_memory)
    print("Apps CPU", apps_cpu)
    print("Apps Mem", apps_memory)
    print("Anti Affinity", task_anti_affinity)

