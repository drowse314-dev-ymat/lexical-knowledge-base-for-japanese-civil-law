# encoding: utf-8

from attest import (
    Tests, assert_hook,
    raises,
)
import networkx
import rdflib
from lkbutils import nodemodel


APIs = [
    'create_graph',
    'create_node', 'create_literal',
    'link', 'link_label', 'extend', 'type_property',
    'label_text',
    'classes',
    'to_networkx',
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


class Fixture(object):
    """Test fixture namespace."""

    class NS(object):
        pass

    sample_names = NS()
    sample_names.namespace = u'http://example.com/ymat/2013/10/18/nodecreate_test/'
    sample_names.for_nodes = [
        u'john', u'kay', u'lee', u'mat', u'nai',
    ]
    sample_names.for_literals = [
        u'alen', u'beth', u'coo', u'dee', 88,
    ]

    graph_sample = NS()
    graph_sample.node_terms = [
        u'node1', u'node2', u'node3',
        #  u'Property',  # reserved
    ]
    graph_sample.property_terms = [
        u'prop1', u'prop2',
        #  u'type', u'label',  # reserved
    ]
    graph_sample.terms = (
        graph_sample.node_terms + graph_sample.property_terms
    )
    graph_sample.property_definitions = [
        (u'prop1', u'type', u'Property'),
        (u'prop2', u'type', u'Property'),
    ]
    graph_sample.relations = [
        (u'node1', u'prop1', u'node2'),
        (u'node1', u'prop1', u'node3'),
        (u'node2', u'prop2', u'node3'),
    ]
    graph_sample.rdflib_nodes = NS()
    for __t in graph_sample.terms:
        setattr(graph_sample.rdflib_nodes, __t, rdflib.BNode())
    graph_sample.rdflib_nodes.type = rdflib.RDF.type
    graph_sample.rdflib_nodes.Property = rdflib.RDF.Property
    graph_sample.rdflib_nodes.label = rdflib.RDFS.label
    graph_sample.rdflib_graph = rdflib.Graph()
    for __t in graph_sample.terms:
        graph_sample.rdflib_graph.add((getattr(graph_sample.rdflib_nodes, __t),
                                       graph_sample.rdflib_nodes.label,
                                       rdflib.Literal(__t)))
    for __s,__p,__o in (graph_sample.relations + graph_sample.property_definitions):
        graph_sample.rdflib_graph.add((getattr(graph_sample.rdflib_nodes, __s),
                                       getattr(graph_sample.rdflib_nodes, __p),
                                       getattr(graph_sample.rdflib_nodes, __o)))


@rdflib_nodemodel_unit.test
def create_node():
    """Check creations of RDF nodes dependent on rdflib."""

    bnode = rdflib_model.create_node()
    assert isinstance(bnode, rdflib.BNode)

    refs = [
        rdflib_model.create_node(name=name, ns=Fixture.sample_names.namespace)
        for name in Fixture.sample_names.for_nodes
    ]
    for node in refs:
        assert isinstance(node, rdflib.URIRef)

    literals = [
        rdflib_model.create_literal(data)
        for data in Fixture.sample_names.for_literals
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
def get_label_test():
    """Retrieve label text from graph dependent on rdflib."""
    g = rdflib.Graph()
    node = rdflib.BNode()
    label = rdflib.Literal(u'something')
    g.add((node, rdflib.RDFS.label, label))
    assert rdflib_model.label_text(g, node) == u'something'

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

@rdflib_nodemodel_unit.test
def toplevel_to_networkx():
    """lkbutils.rdflib_to_networkx is available."""
    from lkbutils import rdflib_to_networkx

    rdflib_graph = Fixture.graph_sample.rdflib_graph
    converted_on_toplevel = rdflib_to_networkx(rdflib_graph)
    converted_on_instance = rdflib_model.to_networkx(rdflib_graph)

    # equality of nodes, edges + adge attributes
    assert converted_on_toplevel.nodes() == converted_on_instance.nodes()
    assert (list(networkx.generate_edgelist(converted_on_toplevel)) ==
            list(networkx.generate_edgelist(converted_on_instance)))

@rdflib_nodemodel_unit.test
def convert_to_networkx():
    """Check model conversion to NetworkX DiGraph."""

    rdflib_graph = Fixture.graph_sample.rdflib_graph
    nx_graph = rdflib_model.to_networkx(rdflib_graph)

    assert isinstance(nx_graph, networkx.DiGraph)
    assert set(nx_graph.nodes()) == set(Fixture.graph_sample.node_terms)

    nx_graph_edges = []
    for src in nx_graph:
        for dest in nx_graph[src]:
            attrs = nx_graph[src][dest]
            if u'label' in attrs:
                link = nx_graph[src][dest][u'label']
                nx_graph_edges.append((src, link, dest))
    assert set(nx_graph_edges) == set(Fixture.graph_sample.relations)
