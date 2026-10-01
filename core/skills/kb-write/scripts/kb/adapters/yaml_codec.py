import yaml


class NoteLoader(yaml.SafeLoader):
    pass


NoteLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in resolvers if tag != 'tag:yaml.org,2002:timestamp']
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ValueError('YAML keys must be distinct strings')
        result[key] = loader.construct_object(value_node)
    return result


NoteLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_frontmatter(text: str) -> dict:
    try:
        value = yaml.load(text, Loader=NoteLoader)
    except yaml.YAMLError as error:
        raise ValueError('Invalid YAML frontmatter') from error
    if not isinstance(value, dict):
        raise ValueError('Frontmatter must be a mapping')
    return value
