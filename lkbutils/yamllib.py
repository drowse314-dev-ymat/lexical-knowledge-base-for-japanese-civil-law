# encoding: utf-8

import yaml


def parse_yaml(yaml_data):
    """Parse YAML stiring by PyYAML."""
    data = yaml.load(yaml_data)
    if data is None:
        return {}
    return data

def fancydump(data, encoding='utf8'):
    """
    Dump to a verbose YAML string by PyYAML.
    """
    yamlstr = yaml.safe_dump(
        data,
        indent=4,
        allow_unicode=True,
        default_flow_style=False,
    )
    return yamlstr.decode(encoding)
