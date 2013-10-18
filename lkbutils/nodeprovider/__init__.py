# encoding: utf-8

import re
from . import kakasicall, nodemodel


class NameRegistrationError(ValueError):
    pass

class InvalidName(NameRegistrationError):
    pass

class NameConflict(NameRegistrationError):
    pass


re_formal_name = re.compile(u'^[^\W\d]\w+$')


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
        raise NotImplementedError('create_graph must be implemented in subclasses')

    def add(self, name):
        """
        Register a node without conflicts.
        """
        valid_name = self._add_to_namestore(name)
        node = self.create_bnode()
        registered_node = self._add_to_store(valid_name, node)
        return registered_node

    def _add_to_namestore(self, name):
        return self._nameprovider.add(name)

    def _add_to_store(self, valid_name, node):
        self._add_node_to_store(valid_name, node)
        self.label(self.graph, node, valid_name)
        return node

    def _add_node_to_store(self, name, node):
        self._nodestore[name] = node

    def label(self, graph, node, valid_name):
        """
        Create label link from node to literal label node..
        """
        raise NotImplementedError('label must be implemented in subclasses')

    def create_bnode(self):
        """
        Create blank node, with the reference to label with given name.
        """
        raise NotImplementedError('create_bnode must be implemented in subclasses')


class RDFLibNodeProvider(NodeProvider):
    """NodeProvider subclass using rdflib models."""

    classes = nodemodel.rdflib_classes()

    def create_graph(self):
        return nodemodel.create_rdflib_graph()

    def create_bnode(self):
        return nodemodel.create_rdflib_node()

    def label(self, graph, node, label_text):
        nodemodel.link_rdflib_label(graph, node, label_text)


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
