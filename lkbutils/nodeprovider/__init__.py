# encoding: utf-8

import re
from . import kakasicall
from lkbutils import nodemodel


class NameRegistrationError(ValueError):
    pass

class InvalidName(NameRegistrationError):
    pass

class NameConflict(NameRegistrationError):
    pass

class NameNotRegistered(KeyError):
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
        valid_name = self._valid_name_from(name)
        self._add_to_store(valid_name, name)
        return valid_name

    def _valid_name_from(self, name):
        name = self._preprocess_name(name)
        if not self._is_valid_name(name):
            raise InvalidName(u'name not acceptable: "{}"'.format(name))
        return name

    def _preprocess_name(self, name):
        if self._romanize_on:
            name = try_romanize(name)
        name = self._handle_spacing_chars(name)
        name = name.lower()
        return name

    def _handle_spacing_chars(self, name):
        return u'_'.join(name.split())

    def _is_valid_name(self, name):
        return bool(re_formal_name.match(name))

    def _add_to_store(self, name, orig_name):
        namestore = self._namestore
        if name in namestore:
            raise NameConflict(u'name already exists: "{}"'.format(name))
        namestore[name] = orig_name

    def get_ns_identifier(self, name):
        """
        Get stored identifier in NodeProvider.ns from source text.
        """
        namestore = self._namestore
        for identifier in namestore:
            if namestore[identifier] == name:
                return identifier
        raise NameNotRegistered(u'"{}" not found in namespace'.format(name))


def try_romanize(name):
    return kakasicall.romanize(name)


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

    def create_graph(self):
        """Create an empty node graph."""
        return self.depending_library.create_graph()

    def add(self, name, as_property=False):
        """
        Register a node without conflicts.
        """
        valid_name = self._add_to_namestore(name)
        node = self.create_bnode()
        registered_node = self._add_to_store(valid_name, node, label=name)
        if as_property:
            self._as_property(registered_node)
        return registered_node

    def _add_to_namestore(self, name):
        return self._nameprovider.add(name)

    def _add_to_store(self, valid_name, node, label=None):
        self._add_node_to_store(valid_name, node)
        if label is None:
            label = valid_name
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

    @property
    def classes(self):
        """class components of depending library."""
        return self.depending_library.classes()


class RDFLibNodeProvider(NodeProvider):
    """NodeProvider subclass using rdflib models."""
    depending_library = nodemodel.RDFLib()


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
