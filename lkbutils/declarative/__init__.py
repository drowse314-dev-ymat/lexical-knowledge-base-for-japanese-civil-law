# encoding: utf-8

import yaml
from lkbutils import RDFLibNodeProvider, RDFLibRelationProvider


def parse_yaml(yaml_data):
    """Parse YAML stiring by PyYAML."""
    return yaml.load(yaml_data)

def leaves_from_struct(data):
    """
    Traverse/generate structured data.

        data: list or dict is acceptable / any dict
              structure will be ignored, thus every list
              in deepest levels is enumerated as term list.
    """
    if isinstance(data, unicode):
        yield data
    elif isinstance(data, str):
        yield unicode(data)
    elif isinstance(data, list):
        for child in data:
            for item in leaves_from_struct(child):
                yield item
    elif isinstance(data, dict):
        for child in data.values():
            for item in leaves_from_struct(child):
                yield item
    else:
        raise TypeError(
            u'invalid data type: {}({})'.format(
                type(data), data
            )
        )


class TermLoader(object):
    """Loads term definitions."""

    def __init__(self, **options):
        """Loads term definitions."""
        self._nodeprovider = self.get_node_provider(**options)

    @property
    def ns(self):
        """Proxy to TermLoader._nodeprovider.ns."""
        return self._nodeprovider.ns

    @property
    def graph(self):
        """Proxy to TermLoader._nodeprovider.graph."""
        return self._nodeprovider.graph

    def get_node_provider(self, **options):
        """Delegate NodeProvider creation to subclasses."""
        return self.nodeprovider_class(**options)

    def load(self, data, as_property=False):
        """
        Load terms from data.

        data: list or dict is acceptable / any dict
              structure will be ignored, thus every list
              in deepest levels is loaded as term list.
        as_property: load terms as properties.
        """
        for term in leaves_from_struct(data):
            self._addterm(term, as_property)

    def load_yaml(self, yaml_data):
        """
        Load terms from YAML representation.

        SampleFormat:
            +++++++++++++++++++++
            # YAML
            options:
                as_property: yes
            terms:
                subcategory1:
                    - term1
                    - term2
                subcategory2:
                    - term3
                ...
            +++++++++++++++++++++
        See RDFLibTermLoader.load for options.
        """
        data = parse_yaml(yaml_data)
        data_terms = data.get(u'terms', [])
        data_options = data.get(u'options', {})
        self.load(data_terms, **data_options)

    def _addterm(self, name, as_property):
        self._nodeprovider.add(name, as_property=as_property)


class RDFLibTermLoader(TermLoader):
    """TermLoader subclass using RDFLibNodeProvider."""
    nodeprovider_class = RDFLibNodeProvider


class RelationLoader(object):
    """Loads relation definitions."""

    def __init__(self, nodeprovider=None, relation=None, **graph_options):
        relation_node = getattr(nodeprovider.ns, relation)
        self._relation_provider = self.create_relation_provider(
            relation=relation_node,
            **graph_options
        )
        self._nodeprovider = nodeprovider

    @property
    def graph(self):
        """Proxy to self._relation_provider.graph."""
        return self._relation_provider.graph

    def create_relation_provider(self, **options):
        """Delegate RelationProvider creation to subclasses."""
        return self.relationprovider_class(**options)

    def load(self, pairs):
        """
        Load terms from list of pairs.

        pairs: list of pairs: (src, dest) whose elements are
               names provided by the given node provider.
        """
        for src, dest in pairs:
            self._register_relation(src, dest)

    def _register_relation(self, src, dest):
        self._relation_provider.add(self._get_node(src), self._get_node(dest))

    def _get_node(self, identifier):
        return getattr(self._nodeprovider.ns, identifier)


class RDFLibRelationLoader(RelationLoader):
    """RelationLoader subclass using RDFLibRelationProvider."""
    relationprovider_class = RDFLibRelationProvider
