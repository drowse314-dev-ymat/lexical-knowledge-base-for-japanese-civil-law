# encoding: utf-8

from lkbutils import yamllib, RDFLibNodeProvider, RDFLibRelationProvider
from lkbutils.relationprovider import Cyclic


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

    @property
    def nodeprovider(self):
        """Proxy to TermLoader._nodeprovider."""
        return self._nodeprovider

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
        data = yamllib.parse_yaml(yaml_data)
        data_terms = data.get(u'terms', [])
        data_options = data.get(u'options', {})
        self.load(data_terms, **data_options)

    def _addterm(self, name, as_property):
        self._nodeprovider.add(name, as_property=as_property)


class RDFLibTermLoader(TermLoader):
    """TermLoader subclass using RDFLibNodeProvider."""
    nodeprovider_class = RDFLibNodeProvider


class YamlTermConfigLoader(object):
    """Utility for loading YAML term configurations."""

    @classmethod
    def load_yaml(klass, yaml_data):
        """
        Load a YAML to get configs. for TermLoaders.

        SampleFormat:
            +++++++++++++++++++++
            # YAML
            options:
                romanize: yes
            load_options:
                as_property: no
            terms:
                subcategory1:
                    - term1
                    - term2
                subcategory2:
                    - term3
                ...
            +++++++++++++++++++++
        """
        data = yamllib.parse_yaml(yaml_data)
        data_options = data.get(u'options', {})
        term_loader = klass._create_termloader(**data_options)

        data_terms = data.get(u'terms', [])
        data_load_options = data.get(u'load_options', {})
        term_loader.load(data_terms, **data_load_options)

        return term_loader

    @classmethod
    def _create_termloader(klass, **options):
        return klass.loader_class(**options)


class RDFLibYamlTermConfigLoader(YamlTermConfigLoader):
    """YamlTermConfigLoader using RDFLibTermLoader."""
    loader_class = RDFLibTermLoader


rdflib_load_terms = RDFLibYamlTermConfigLoader.load_yaml


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
        src_node, dest_node = self._get_node(src), self._get_node(dest)
        try:
            self._relation_provider.add(src_node, dest_node)
        except Cyclic as cyclic_err:
            self._handle_cyclic_error(cyclic_err)

    def _get_node(self, identifier):
        return getattr(self._nodeprovider.ns, identifier)

    def _handle_cyclic_error(self, cyclic_err):
        mod_relation = self._get_original_name(cyclic_err.relation)
        mod_path = [
            self._get_original_name(node)
            for node in cyclic_err.path
        ]
        raise Cyclic(mod_path, relation=mod_relation)

    def _get_original_name(self, node):
        nodeprovider = self._nodeprovider
        if not hasattr(nodeprovider, 'get_identifier_from'):
            return node
        return nodeprovider.get_origin_name_from(node)


class RDFLibRelationLoader(RelationLoader):
    """RelationLoader subclass using RDFLibRelationProvider."""
    relationprovider_class = RDFLibRelationProvider


class YamlRelationConfigLoader(object):
    """Utility for loading YAML relation configurations."""

    @classmethod
    def load_yaml(klass, yaml_data):
        """
        Load a YAML to get configs. for RelationLoaders.

        SampleFormat:
            +++++++++++++++++++++
            # YAML
            options:  # yaml-global options
                dry: yes
                nointerlinks: yes
                acyclic: yes
            relations:
                relation1:
                    options:  # override for specific relation
                        dry: no
                    pairs:
                        subcategory1:
                            - term1 term2
                            - term2 term3
                        subcategory2:
                            - term3 term4
                        ...
                relation2:
                    ...
            +++++++++++++++++++++
        """
        data = yamllib.parse_yaml(yaml_data)
        base_options = data.get(u'options', {})
        relations = data.get(u'relations', {})
        configs = {}
        for relation in relations:
            configs[relation] = klass._create_config(
                relation,
                relations[relation],
                base_options.copy()
            )
        return configs

    @classmethod
    def relation_providers_from(klass, yaml_data, nodeprovider=None):
        """Parse config YAML, create {relation => RelationLoader} map."""
        configs = klass.load_yaml(yaml_data)
        return {
            relation: klass._create_loader(configs[relation], nodeprovider)
            for relation in configs
        }

    @classmethod
    def _create_config(klass, relation, data, base_options):

        config_override = data.get(u'options', {})
        base_options.update(config_override)

        data_pairs = data.get(u'pairs', [])
        pairs = [
            klass._parse_pair(pair_repr)
            for pair_repr in leaves_from_struct(data_pairs)
        ]

        return {
            u'relation': relation,
            u'options': base_options,
            u'pairs': pairs,
        }

    @classmethod
    def _parse_pair(klass, pair_repr):
        return tuple(pair_repr.split(u' '))

    @classmethod
    def _create_loader(klass, loader_config, nodeprovider):
        relation = loader_config.get(u'relation')
        options = loader_config.get(u'options', {})
        relation_loader = klass.loader_class(
            nodeprovider=nodeprovider,
            relation=relation,
            **options
        )
        pairs = loader_config.get(u'pairs', [])
        relation_loader.load(pairs)
        return relation_loader


class RDFLibYamlRelationConfigLoader(YamlRelationConfigLoader):
    """YamlRelationConfigLoader using RDFLibRelationLoader."""
    loader_class = RDFLibRelationLoader


rdflib_load_relcfg = RDFLibYamlRelationConfigLoader.load_yaml
rdflib_load_relations = RDFLibYamlRelationConfigLoader.relation_providers_from
