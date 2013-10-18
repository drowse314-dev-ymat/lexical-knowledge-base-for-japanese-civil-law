# encoding: utf-8

import rdflib


def create_rdflib_graph():
    """Create an RDF Graph modeled in rdflib."""
    return rdflib.Graph()

def create_rdflib_node(name=None, ns=None):
    """Create an RDF Resource node modeled in rdflib."""
    if name is None:
        return rdflib.BNode()
    if ns is not None:
        name = ns + name
    return rdflib.URIRef(name)

def create_rdflib_literal(data):
    """Create an RDF Literal node modeled in rdflib."""
    return rdflib.Literal(data)

def link_rdflib_label(graph, node, label_text):
    """Create a RDFS.label link from node to literal label node in rdflib."""
    graph.add(
        (node, rdflib.RDFS.label, create_rdflib_literal(label_text))
    )

def rdflib_classes():
    """References to rdflib component classes."""
    return dict(
        graph=rdflib.Graph,
        bnode=rdflib.BNode, uriref=rdflib.URIRef,
        literal=rdflib.Literal,
    )
