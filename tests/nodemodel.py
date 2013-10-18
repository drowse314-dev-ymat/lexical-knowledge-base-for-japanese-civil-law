# encoding: utf-8

from attest import (
    Tests, assert_hook,
)
import rdflib
from lkbutils import nodemodel


rdflib_nodemodel_unit = Tests()
rdflib_model = nodemodel.RDFLib()

# node creaters dependent on rdflib.
@rdflib_nodemodel_unit.test
def create_node():
    """Check creations of RDF nodes dependent on rdflib."""
    namespace = u'http://example.com/ymat/2013/10/18/nodecreate_test/'
    names = [
        u'john', u'kay', u'lee', u'mat', u'nai',
    ]
    literals = [
        u'alen', u'beth', u'coo', u'dee', 88,
    ]

    bnode = rdflib_model.create_node()
    assert isinstance(bnode, rdflib.BNode)

    refs = [
        rdflib_model.create_node(name=name, ns=namespace)
        for name in names
    ]
    for node in refs:
        assert isinstance(node, rdflib.URIRef)

    literals = [
        rdflib_model.create_literal(data)
        for data in literals
    ]
    for node in literals:
        assert isinstance(node, rdflib.Literal)

@rdflib_nodemodel_unit.test
def create_graph():
    """Check creations of RDF graph dependent on rdflib."""
    graph = rdflib_model.create_graph()
    assert isinstance(graph, rdflib.Graph)

@rdflib_nodemodel_unit.test
def create_label():
    """
    Check linking some RDF node to a literal with RDFS:label dependent on rdflib.
    """
    g = rdflib.Graph()
    node = rdflib.BNode()
    rdflib_model.link_label(g, node, u'label')
    assert (
        list(g.triples((None, None, None)))[0] ==
            node, rdflib.RDFS.label, rdflib.Literal(u'label')
    )

@rdflib_nodemodel_unit.test
def create_property():
    """
    Check setting some RDF node as an RDF:Property dependent on rdflib.
    """
    g = rdflib.Graph()
    node = rdflib.BNode()
    rdflib_model.type_property(g, node)
    assert (
        list(g.triples((None, None, None)))[0] ==
            node, rdflib.RDF.type, rdflib.RDF.Property
    )
