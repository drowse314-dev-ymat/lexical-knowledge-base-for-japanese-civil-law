# encoding: utf-8

from attest import (
    Tests, assert_hook,
    contextmanager, raises,
)
from lkbutils import nodeprovider
from lkbutils.nodeprovider import kakasicall
from lkbutils.nodeprovider import nodemodel


nameprovider_unit = Tests()
kakasi_unit = Tests()
nodemodel_unit = Tests()
nodeprovider_unit = Tests()


@contextmanager
def empty_nameprovider(romanize=False):
    try:
        yield nodeprovider.NameProvider(romanize=romanize)
    finally:
        pass

@contextmanager
def empty_rdflib_nodeprovider(romanize=True):
    try:
        yield nodeprovider.RDFLibNodeProvider(
            romanize=romanize,
        )
    finally:
        pass


# Adding names.

@nameprovider_unit.test
def add_simple_names():
    """NameProvider.add."""
    with empty_nameprovider() as provider:

        ret_john = provider.add(u'John')
        assert ret_john == u'john'

        ret_ken = provider.add(u'Ken')
        assert ret_ken == u'ken'

        ret_yumi = provider.add(u'Yumi is waiting at the door')
        assert ret_yumi == u'yumi_is_waiting_at_the_door'

        with raises(nodeprovider.NameConflict):
            provider.add(u'John')
        with raises(nodeprovider.NameConflict):
            provider.add(u'ken')

        namespace = provider.ns
        assert u'john' in namespace
        assert namespace.john == u'John'
        assert u'ken' in namespace
        assert namespace.ken == u'Ken'
        assert u'yumi_is_waiting_at_the_door' in namespace
        assert namespace.yumi_is_waiting_at_the_door == u'Yumi is waiting at the door'

        assert provider.get_ns_identifier(u'John') == u'john'
        assert provider.get_ns_identifier(u'Yumi is waiting at the door') == u'yumi_is_waiting_at_the_door'
        with raises(nodeprovider.NameNotRegistered):
            provider.get_ns_identifier(u'poupou')

@nameprovider_unit.test
def add_invalid_names():
    """NameProvider.add refuses invalid names."""
    with empty_nameprovider() as provider:
        with raises(nodeprovider.InvalidName):
            provider.add(u'3way')
        with raises(nodeprovider.InvalidName):
            provider.add(u'魂')
        with raises(nodeprovider.InvalidName):
            provider.add(u"I'm fine")

@nameprovider_unit.test
def handle_kana_name_addition():
    """
    NameProvider with romanize=True accepts kanji/kana names.
    """
    with empty_nameprovider(romanize=True) as provider:

        ret_soul =  provider.add(u'魂')
        assert ret_soul == u'tamashii'
        ret_teitou =  provider.add(u'抵当権')
        assert ret_teitou == u'teitouken'
        ret_hojo =  provider.add(u'補助開始の審判')
        assert ret_hojo == u'hojokaishinoshinpan'
        with raises(nodeprovider.NameConflict):
            provider.add(u'teitouken')

        namespace = provider.ns
        assert namespace.tamashii == u'魂'
        assert namespace.teitouken == u'抵当権'
        assert namespace.hojokaishinoshinpan == u'補助開始の審判'

        assert provider.get_ns_identifier(u'魂') == u'tamashii'
        assert provider.get_ns_identifier(u'補助開始の審判') == u'hojokaishinoshinpan'
        with raises(nodeprovider.NameNotRegistered):
            provider.get_ns_identifier(u'hitanposaiken')


# simple kakasi caller.
@kakasi_unit.test
def kakasi_conversino():
    """Roughly check kakasi conversion."""
    desired_yomi = {
        u'抵当権': u'teitouken',
        u'国民の休日': u'kokuminnokyuujitsu',
        u'公共のベランダ': u'koukyounoberanda',
    }

    for target in desired_yomi:
        yomi = desired_yomi[target]
        assert kakasicall.romanize(target) == yomi


# node creaters dependent on 3rd party modules.
@nodemodel_unit.test
def create_node():
    """Check creations of RDF nodes dependent on 3rd party modules."""
    namespace = u'http://example.com/ymat/2013/10/18/nodecreate_test/'
    names = [
        u'john', u'kay', u'lee', u'mat', u'nai',
    ]
    literals = [
        u'alen', u'beth', u'coo', u'dee', 88,
    ]

    import rdflib

    rdflib_bnode = nodemodel.create_rdflib_node()
    assert isinstance(rdflib_bnode, rdflib.BNode)

    rdflib_refs = [
        nodemodel.create_rdflib_node(name=name, ns=namespace)
        for name in names
    ]
    for node in rdflib_refs:
        assert isinstance(node, rdflib.URIRef)

    rdflib_literals = [
        nodemodel.create_rdflib_literal(data)
        for data in literals
    ]
    for node in rdflib_literals:
        assert isinstance(node, rdflib.Literal)

@nodemodel_unit.test
def create_graph():
    """Check creations of RDF graph dependent on 3rd party modules."""
    import rdflib
    rdflib_graph = nodemodel.create_rdflib_graph()
    assert isinstance(rdflib_graph, rdflib.Graph)

@nodemodel_unit.test
def create_label():
    """
    Check linking some RDF node to a literal with RDFS:label dependent on 3rd party modules.
    """
    import rdflib
    g = rdflib.Graph()
    node = rdflib.BNode()
    nodemodel.link_rdflib_label(g, node, u'label')
    assert (
        list(g.triples((None, None, None)))[0] ==
            node, rdflib.RDFS.label, rdflib.Literal(u'label')
    )


# Adding nodes.

@nodeprovider_unit.test
def nodeprovider_on_toplevel():
    """NodeProvider subclasses are accessible on pkg's toplevel ns."""
    from lkbutils import RDFLibNodeProvider

@nodeprovider_unit.test
def add_nodes():
    """(.*)NodeProvider.add."""
    import rdflib

    with empty_rdflib_nodeprovider() as provider:

        ret_john = provider.add(u'John')
        assert isinstance(ret_john, provider.classes['bnode'])
        assert provider.ns.john == ret_john
        assert u'john' in provider.ns
        assert (
            (provider.ns.john, rdflib.RDFS.label, rdflib.Literal(u'john'))
            in list(provider.graph.triples((None, None, None)))
        )
        assert provider.get(u'John') == provider.ns.john

        with raises(nodeprovider.InvalidName):
            provider.add(u'3way')

        ret_soul =  provider.add(u'魂')
        assert isinstance(ret_soul, provider.classes['bnode'])
        assert provider.ns.tamashii == ret_soul
        assert u'tamashii' in provider.ns
        assert (
            (provider.ns.tamashii, rdflib.RDFS.label, rdflib.Literal(u'tamashii'))
            in list(provider.graph.triples((None, None, None)))
        )
        assert provider.get(u'魂') == provider.ns.tamashii

        with raises(nodeprovider.NameNotRegistered):
            provider.get(u'詐害行為取消権')
