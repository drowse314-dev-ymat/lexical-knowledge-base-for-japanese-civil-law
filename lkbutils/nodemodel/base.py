# encoding: utf-8

import abc


def with_metaclass(meta, bases=(object, )):
    return meta('NewBase', bases, {})


class NodeModel(with_metaclass(abc.ABCMeta)):
    """RDF node modeling API."""

    @abc.abstractmethod
    def create_graph(self):
        """Create an RDF Graph."""
        pass

    @abc.abstractmethod
    def create_node(self, name=None, ns=None):
        """Create an RDF Resource node."""
        pass

    @abc.abstractmethod
    def create_literal(self, data):
        """Create an RDF literal node."""
        pass

    @abc.abstractmethod
    def link_label(self, graph, node, label_text):
        """Create an RDFS.label link from node to literal label node."""
        pass

    @abc.abstractmethod
    def label_text(self, graph, node):
        """
        Retrieve label text of the node from RDFS.label destination literal node.
        """
        pass

    @abc.abstractmethod
    def type_property(self, graph, node):
        """Set a node type to RDF:Property."""
        pass

    @abc.abstractmethod
    def extend(self, graph, node, supernode):
        """Create an RDFS.type link from node to supernode."""
        pass

    @abc.abstractmethod
    def link(self, graph, src, relation, dest):
        """Create an arbitrary property link from node to dest."""
        pass

    @abc.abstractmethod
    def classes(self):
        """References to depending library component classes."""
        pass

    @abc.abstractmethod
    def to_networkx(self, graph):
        """Generate a DiGraph instance of networkx from given graph model."""
        pass
