# encoding: utf-8

from attest import (
    Tests, assert_hook,
    raises,
)
import rdflib
from lkbutils import nodemodel


APIs = [
    'create_graph',
    'create_node', 'create_literal',
    'link', 'link_label', 'extend', 'type_property',
    'classes',
]

# NodeModel spec.
nodemodel_unit = Tests()

@nodemodel_unit.test
def nodemodel_spec():
    """Check NodeModel's subclass spec."""
    for missing in APIs:
        insuccifient_attrs = APIs[:]
        insuccifient_attrs.remove(missing)
        dict_attrs = {name: lambda self: self for name in insuccifient_attrs}
        NewNodeModel = type('NewNodeModel', (nodemodel.base.NodeModel, ), dict_attrs)
        with raises(TypeError):
            model = NewNodeModel()


rdflib_nodemodel_unit = Tests()
rdflib_model = nodemodel.RDFLib()

# node creaters dependent on rdflib.
@rdflib_nodemodel_unit.test
def api_managed():
    """NodeModel's API is kept managed..."""
    for name in dir(rdflib_model):
        if not name.startswith('_'):
            assert name in APIs

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

@rdflib_nodemodel_unit.test
def extend():
    """
    Check linking some RDF node to a literal with RDF:type dependent on rdflib.
    """
    g = rdflib.Graph()
    node = rdflib.BNode()
    supernode = rdflib.BNode()
    rdflib_model.extend(g, node, supernode)
    assert (
        (node, rdflib.RDF.type, supernode) in
        list(g.triples((None, None, None)))
    )

@rdflib_nodemodel_unit.test
def create_link():
    """
    Check linking an RDF node pair with an arbitrary property on rdflib.
    """
    g = rdflib.Graph()
    node_src = rdflib.BNode()
    node_dest = rdflib.BNode()
    node_property = rdflib.BNode()
    g.add((node_property, rdflib.RDF.type, rdflib.RDF.Property))

    rdflib_model.link(g, node_src, node_property, node_dest)
    assert (
        (node_src, node_property, node_dest) in
        list(g.triples((None, None, None)))
    )
