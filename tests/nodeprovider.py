# encoding: utf-8

from attest import (
    Tests, assert_hook,
    contextmanager, raises,
)
from lkbutils import nodeprovider
from lkbutils.nodeprovider import kakasicall


nameprovider_unit = Tests()
kakasi_unit = Tests()
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
            (provider.ns.john, rdflib.RDFS.label, rdflib.Literal(u'John'))
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
            (provider.ns.tamashii, rdflib.RDFS.label, rdflib.Literal(u'魂'))
            in list(provider.graph.triples((None, None, None)))
        )
        assert provider.get(u'魂') == provider.ns.tamashii

        with raises(nodeprovider.NameNotRegistered):
            provider.get(u'詐害行為取消権')

@nodeprovider_unit.test
def add_nodes_as_properties():
    """(.*)NodeProvider.add(..., as_property=True)."""

    import rdflib

    with empty_rdflib_nodeprovider() as provider:

        ret_part_of = provider.add(u'part_of', as_property=True)
        assert isinstance(ret_part_of, provider.classes['bnode'])
        assert provider.ns.part_of == ret_part_of
        assert u'part_of' in provider.ns
        assert (
            (provider.ns.part_of, rdflib.RDFS.label, rdflib.Literal(u'part_of'))
            in list(provider.graph.triples((None, None, None)))
        )
        assert (
            (provider.ns.part_of, rdflib.RDF.type, rdflib.RDF.Property)
            in list(provider.graph.triples((None, None, None)))
        )
        assert provider.get(u'part_of') == provider.ns.part_of

        ret_hyper = provider.add(u'hyper', as_property=True)
        assert isinstance(ret_hyper, provider.classes['bnode'])
        assert provider.ns.hyper == ret_hyper
        assert u'hyper' in provider.ns
        assert (
            (provider.ns.hyper, rdflib.RDFS.label, rdflib.Literal(u'hyper'))
            in list(provider.graph.triples((None, None, None)))
        )
        assert (
            (provider.ns.hyper, rdflib.RDF.type, rdflib.RDF.Property)
            in list(provider.graph.triples((None, None, None)))
        )
        assert provider.get(u'hyper') == provider.ns.hyper
