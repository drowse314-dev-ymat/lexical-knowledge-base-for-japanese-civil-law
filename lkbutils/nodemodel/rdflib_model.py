# encoding: utf-8

import rdflib
from .base import NodeModel


class RDFLib(NodeModel):

    def create_graph(self):
        return rdflib.Graph()

    def create_node(self, name=None, ns=None):
        if name is None:
            return rdflib.BNode()
        if ns is not None:
            name = ns + name
        return rdflib.URIRef(name)

    def create_literal(self, data):
        return rdflib.Literal(data)

    def link_label(self, graph, node, label_text):
        self.link(graph, node, rdflib.RDFS.label, self.create_literal(label_text))

    def type_property(self, graph, node):
        self.extend(graph, node, rdflib.RDF.Property)

    def extend(self, graph, node, supernode):
        self.link(graph, node, rdflib.RDF.type, supernode)

    def link(self, graph, src, relation, dest):
        graph.add(
            (src, relation, dest)
        )

    def classes(self):
        return dict(
            graph=rdflib.Graph,
            bnode=rdflib.BNode, uriref=rdflib.URIRef,
            literal=rdflib.Literal,
        )
