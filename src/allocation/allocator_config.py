import pathlib
from pathlib import Path
import io
import yaml
import humanfriendly
import itertools
import cerberus

__all__ = ["parse_config"]

BYTES_IN_GiB = 1024 ** 3


class ConfigException(Exception):
    pass


def mem_to_gib(mem_str: str) -> int:
    return humanfriendly.parse_size(mem_str) // BYTES_IN_GiB


def validate_config(config_data: dict):
    with io.open(pathlib.Path(__file__).parent / "config_schema.yml") as config_schema_f:
        config_schema = config_schema_f.read()
    schema = yaml.load(config_schema)
    v = cerberus.Validator()
    return v.validate(config_data, schema), v.errors


def _transform_config(config_data: dict) -> tuple:
    ret, errors = validate_config(config_data)
    if not ret:
        raise ConfigException("Invalid config file: %s" % str(errors))

    nodes = config_data["nodes"]
    apps = config_data["apps"]
    nodes_cpu = []
    nodes_memory = []
    for node in nodes:
        resources = node["resources"]
        nodes_cpu.append(resources["cpu"])
        nodes_memory.append(mem_to_gib(resources["memory"]))

    apps_memory = []
    apps_cpu = []
    labels = {}
    for app_id, app in enumerate(apps):
        app_name = app["name"]
        resources = app["resources"]
        apps_cpu.append(resources["cpu"])
        apps_memory.append(mem_to_gib(resources["memory"]))
        if app.get("antiAffinityLabels", None):
            for label in app["antiAffinityLabels"]:
                if not labels.get(label, None):
                    labels[label] = [(app_name, app_id)]
                else:
                    labels[label].append((app_name, app_id))

    task_anti_affinity = []
    for key in labels.keys():
        idlist = [app_id for (app_name, app_id) in labels[key]]
        task_anti_affinity.extend(list(itertools.combinations(idlist, 2)))

    return nodes_cpu, nodes_memory, apps_cpu, apps_memory, task_anti_affinity, config_data


def parse_config(yaml_path: Path) -> tuple:
    with yaml_path.open() as stream:
        try:
            return _transform_config(yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            raise ConfigException(exc)


if __name__ == "__main__":
    nodes_cpu, nodes_memory, \
        apps_cpu, apps_memory, \
        task_anti_affinity, data_dict = parse_config(Path("resources_complex.yml"))

    print("Nodes CPU", nodes_cpu)
    print("Nodes Mem", nodes_memory)
    print("Apps CPU", apps_cpu)
    print("Apps Mem", apps_memory)
    print("Anti Affinity", task_anti_affinity)

