# encoding: utf-8

import re
from . import kakasicall
from lkbutils import nodemodel, yamllib


class NameRegistrationError(ValueError):
    def __init__(self, message, encoding='utf8'):
        super(NameRegistrationError, self).__init__(message.encode(encoding))

class InvalidName(NameRegistrationError):
    pass

class NameConflict(NameRegistrationError):
    pass

class NameNotRegistered(KeyError):
    pass

class NodeNotRegistered(ValueError):
    pass


re_formal_name = re.compile(u'^[^\W\d](?:\w+)?$')


class NameProvider(object):
    """
    Manages unique names & name references.
    """

    def __init__(self, romanize=False):
        """
        Manages unique names & name references.

        Options:
            * romanize: try to make valid names by
                        romanizing kana/kanji names.
        """
        self._romanize_on = romanize
        self._namestore = {}
        self._namestore_attr_proxy = DictAccessor(self._namestore)

    @property
    def ns(self):
        """Namespace for registered names."""
        return self._namestore_attr_proxy

    @property
    def origin_names(self):
        """Given original names used to create identifiers."""
        return self._namestore.values()

    def add(self, name):
        """
        Register a name without conflicts.

        Some preprocessing is done before assignment:
            * Snake case for spaces
            * Lower
            * Character validation
        """
        mod_name, valid_name = self._valid_name_from(name)
        self._add_to_store(valid_name, mod_name)
        return valid_name

    def _valid_name_from(self, name):
        name, valid_name = self._preprocess_name(name)
        if not self._is_valid_name(valid_name):
            raise InvalidName(u'name not acceptable: "{}" from "{}"'.format(valid_name, name))
        return name, valid_name

    def _preprocess_name(self, name):
        orig_name = name
        if self._romanize_on:
            mod_name, name = try_romanize(name)
            orig_name = mod_name
        name = self._handle_spacing_chars(name)
        name = name.lower()
        return orig_name, name

    def _handle_spacing_chars(self, name):
        return u'_'.join(name.split())

    def _is_valid_name(self, name):
        return bool(re_formal_name.match(name))

    def _add_to_store(self, name, orig_name):
        namestore = self._namestore
        if name in namestore:
            raise NameConflict(
                u'name already exists for "{}": "{}" from "{}"'.format(
                    namestore[name],
                    name, orig_name
                )
            )
        namestore[name] = orig_name

    def get_ns_identifier(self, name):
        """
        Get stored identifier in NameProvider.ns from source text.
        """
        namestore = self._namestore
        for identifier in namestore:
            if namestore[identifier] == name:
                return identifier
        raise NameNotRegistered(u'"{}" not found in namespace'.format(name))


re_specified_reading = re.compile(u'^(?P<name>.+){(?P<reading>.+)}$')

def try_romanize(name):
    match_specified = re_specified_reading.match(name)
    if match_specified:
        matchmap = match_specified.groupdict()
        return matchmap[u'name'], matchmap[u'reading']
    else:
        return name, kakasicall.romanize(name)


class NodeProvider(object):
    """
    Manages unique nodes, refs. to labels.
    """

    def __init__(self, romanize=False):
        """
        Manages unique nodes, refs. to labels.

        Options:
            * romanize: 'romanize' option for internal NameProvider.
        """
        self._nameprovider = NameProvider(romanize=romanize)
        self._nodestore = {}
        self._nodestore_attr_proxy = DictAccessor(self._nodestore)
        self._graph = self.create_graph()

    @property
    def ns(self):
        """Namespace for registered nodes."""
        return self._nodestore_attr_proxy

    @property
    def graph(self):
        """Entire nodes graph."""
        return self._graph

    @property
    def nameprovider(self):
        """Proxy to NodeProvider._nameprovider."""
        return self._nameprovider

    def create_graph(self):
        """Create an empty node graph."""
        return self.depending_library.create_graph()

    def add(self, name, as_property=False):
        """
        Register a node without conflicts.
        """
        valid_name = self._add_to_namestore(name)
        node = self.create_bnode()
        registered_node = self._add_to_store(valid_name, node)
        if as_property:
            self._as_property(registered_node)
        return registered_node

    def _add_to_namestore(self, name):
        return self._nameprovider.add(name)

    def _add_to_store(self, valid_name, node):
        self._add_node_to_store(valid_name, node)
        label = getattr(self._nameprovider.ns, valid_name)
        self.label(self.graph, node, label)
        return node

    def _add_node_to_store(self, name, node):
        self._nodestore[name] = node

    def label(self, graph, node, valid_name):
        """
        Create label link from node to literal label node.
        """
        return self.depending_library.link_label(graph, node, valid_name)

    def create_bnode(self):
        """
        Create blank node, with the reference to label with given name.
        """
        return self.depending_library.create_node()

    def _as_property(self, node):
        self.type_property(self.graph, node)

    def type_property(self, graph, node):
        """Set the node type as property/relation."""
        return self.depending_library.type_property(graph, node)

    def get(self, name):
        """Get node stored in NodeProvider.ns from label."""
        identifier = self._nameprovider.get_ns_identifier(name)
        return getattr(self.ns, identifier)

    def get_identifier_from(self, node):
        """
        Get stored identifier in NodeProvider.ns from node object.
        """
        nodestore = self._nodestore
        for identifier in nodestore:
            if nodestore[identifier] == node:
                return identifier
        raise NodeNotRegistered(u'"{}" not found in namespace'.format(node))

    def get_origin_name_from(self, node):
        """
        Get origin name in NameProvider.ns which was used to create the node object.
        """
        return getattr(self.nameprovider.ns, self.get_identifier_from(node))

    @property
    def classes(self):
        """class components of depending library."""
        return self.depending_library.classes()

    def _merge(self, provider):
        """Merge all information from another provider."""
        self._merge_names(provider)
        self._merge_nodes(provider)
        self._merge_graph(provider)

    def _merge_names(self, provider):
        my_identifiers = self._nameprovider._namestore
        your_identifiers = provider._nameprovider._namestore
        conflicts = set(my_identifiers).intersection(set(your_identifiers))
        if conflicts:
            confmap = {}
            for key in conflicts:
                confmap[key] = [my_identifiers[key], your_identifiers[key]]
            raise NameConflict(u'name conflicts while merging: {}'.format(
                u', '.join(
                    [u'"{}": {{{}}}'.format(key, u','.join(confmap[key]))
                     for key in confmap]
                )
            ))
        my_identifiers.update(your_identifiers)
    def _merge_nodes(self, provider):
        # directly merge nodes set to keep node identities.
        self._nodestore.update(provider._nodestore)
    def _merge_graph(self, provider):
        self._graph += provider.graph

    def serialize(self, as_property=False):
        """Serialize terms information as YAML."""
        name_map = {}
        name_map[u'options'] = dict(
            romanize=self.nameprovider._romanize_on
        )
        name_map[u'load_options'] = dict(
            as_property=as_property
        )
        ns = self.nameprovider._namestore
        name_map[u'terms'] = [
            u'{}{{{}}}'.format(ns[key], key)
            for key in sorted(ns)
        ]
        return yamllib.fancydump(name_map)


class RDFLibNodeProvider(NodeProvider):
    """NodeProvider subclass using rdflib models."""
    depending_library = nodemodel.RDFLib()


def merge_nodeproviders(*nodeproviders):
    """
    Create a term-mixed NodeProvider from multiple instances.
    """
    # General checks.
    if len(nodeproviders) == 0:
        return None
    elif len(nodeproviders) == 1:
        return nodeproviders[0]
    if not len(set(type(np) for np in nodeproviders)) == 1:
        raise TypeError('inconsistent provider types')

    provider_class = type(nodeproviders[0])
    new_provider = provider_class(romanize=True)

    for provider in nodeproviders:
        new_provider._merge(provider)

    return new_provider


class DictAccessor(object):
    """Expands a dict for attribute-style access."""

    def __init__(self, d):
        self._dict = d

    def __getattr__(self, name):
        try:
            res = self._dict[name]
        except KeyError:
            res = object.__getattribute__(self, name)
        return res

    def __contains__(self, key):
        return dict.__contains__(self._dict, key)
