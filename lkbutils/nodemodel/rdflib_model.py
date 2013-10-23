# encoding: utf-8

import rdflib
import networkx
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

    def label_text(self, graph, node):
        return graph.label(node).value

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

    def to_networkx(self, graph):
        nx_graph = networkx.DiGraph()

        property_nodes = self._property_nodes(graph)

        node_terms = self._node_terms_for_nx(graph, property_nodes=property_nodes)
        nx_graph.add_nodes_from(node_terms)

        for property_node in property_nodes:
            nx_graph.add_edges_from(self._relations_for_nx(graph, property_node))

        return nx_graph

    def _property_nodes(self, graph):
        return [
            prop for prop
            in graph.subjects(
                predicate=rdflib.RDF.type,
                object=rdflib.RDF.Property
            )
        ]

    def _node_terms_for_nx(self, graph, property_nodes=tuple()):
        # only labeled nodes except properties are node terms
        node_terms = []
        generator = self._pairs_of_relation(graph, rdflib.RDFS.label)
        for node, label_literal in generator:
            if node not in property_nodes:
                node_terms.append(label_literal.value)
        return node_terms

    def _relations_for_nx(self, graph, property_node):
        relations = []
        relation_label = self.label_text(graph, property_node)
        generator = self._pairs_of_relation(graph, property_node, as_label=True)
        for src, dest in generator:
            relations.append((src, dest, {u'label': relation_label}))
        return relations

    def _pairs_of_relation(self, graph, property_node, as_label=False):
        for src, dest in graph.subject_objects(property_node):
            if as_label:
                src, dest = (
                    self.label_text(graph, src),
                    self.label_text(graph, dest)
                )
            yield src, dest
