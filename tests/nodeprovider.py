# encoding: utf-8

from attest import (
    Tests, assert_hook,
    contextmanager, raises,
)
import rdflib
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


class Fixtures:
    """Namespace for test fixtures."""

    class simple_names:
        formalized_map = {
            u'John': u'john',
            u'Ken': u'ken',
            u'Yumi is waiting at the door': u'yumi_is_waiting_at_the_door',
        }
        not_added = u'poupou'
        invalid_names = [
            u'3way',
            u'魂',
            u"I'm fine",
        ]

    class kana_kanji_names:
        formalized_map = {
            u'魂': u'tamashii',
            u'抵当権': u'teitouken',
            u'補助開始の審判': u'hojokaishinoshinpan',
        }
        not_added = u'hitanposaiken'

    class simple_nodenames:
        formalized_map = {
            u'John': u'john',
            u'魂': u'tamashii',
        }
        invalid_name = u'3way'
        not_added = u'詐害行為取消権'

    class simple_properties:
        names = [u'part_of', u'hyper']

    class kakasi_conversion:
        desired_conversion = {
            u'抵当権': u'teitouken',
            u'国民の休日': u'kokuminnokyuujitsu',
            u'公共のベランダ': u'koukyounoberanda',
        }


# Adding names.

@nameprovider_unit.test
def add_simple_names():
    """NameProvider.add."""
    with empty_nameprovider() as provider:

        for name in Fixtures.simple_names.formalized_map:
            ret = provider.add(name)
            expected_formalized = Fixtures.simple_names.formalized_map[name]
            assert ret == expected_formalized

        for name in Fixtures.simple_names.formalized_map:
            with raises(nodeprovider.NameConflict):
                provider.add(name)

        namespace = provider.ns
        for name in Fixtures.simple_names.formalized_map:
            formalized_name = Fixtures.simple_names.formalized_map[name]
            assert formalized_name in namespace
            assert getattr(namespace, formalized_name) == name
            assert provider.get_ns_identifier(name) == formalized_name

        with raises(nodeprovider.NameNotRegistered):
            provider.get_ns_identifier(Fixtures.simple_names.not_added)

@nameprovider_unit.test
def add_invalid_names():
    """NameProvider.add refuses invalid names."""
    with empty_nameprovider() as provider:
        for invalid_name in Fixtures.simple_names.invalid_names:
            with raises(nodeprovider.InvalidName):
                provider.add(invalid_name)

@nameprovider_unit.test
def handle_kana_name_addition():
    """
    NameProvider with romanize=True accepts kanji/kana names.
    """
    with empty_nameprovider(romanize=True) as provider:

        for name in Fixtures.kana_kanji_names.formalized_map:
            ret = provider.add(name)
            expected_formalized = Fixtures.kana_kanji_names.formalized_map[name]
            assert ret == expected_formalized

        for name in Fixtures.kana_kanji_names.formalized_map:
            formalized_name = Fixtures.kana_kanji_names.formalized_map[name]
            with raises(nodeprovider.NameConflict):
                provider.add(name)
            with raises(nodeprovider.NameConflict):
                provider.add(formalized_name)

        namespace = provider.ns
        for name in Fixtures.kana_kanji_names.formalized_map:
            formalized_name = Fixtures.kana_kanji_names.formalized_map[name]
            assert getattr(namespace, formalized_name) == name
            assert provider.get_ns_identifier(name) == formalized_name

        with raises(nodeprovider.NameNotRegistered):
            provider.get_ns_identifier(Fixtures.kana_kanji_names.not_added)


# simple kakasi caller.
@kakasi_unit.test
def kakasi_conversino():
    """Roughly check kakasi conversion."""
    for target in Fixtures.kakasi_conversion.desired_conversion:
        yomi = Fixtures.kakasi_conversion.desired_conversion[target]
        assert kakasicall.romanize(target) == yomi


# Adding nodes.

@nodeprovider_unit.test
def nodeprovider_on_toplevel():
    """NodeProvider subclasses are accessible on pkg's toplevel ns."""
    from lkbutils import RDFLibNodeProvider

@nodeprovider_unit.test
def add_nodes():
    """(.*)NodeProvider.add."""

    with empty_rdflib_nodeprovider() as provider:

        for name in Fixtures.simple_nodenames.formalized_map:
            ret = provider.add(name)
            formalized_name = Fixtures.simple_nodenames.formalized_map[name]
            assert isinstance(ret, provider.classes['bnode'])
            assert getattr(provider.ns, formalized_name) == ret
            assert formalized_name in provider.ns
            assert (
                (ret, rdflib.RDFS.label, rdflib.Literal(name))
                in list(provider.graph.triples((None, None, None)))
            )
            assert provider.get(name) == ret

        with raises(nodeprovider.InvalidName):
            provider.add(Fixtures.simple_nodenames.invalid_name)

        with raises(nodeprovider.NameNotRegistered):
            provider.get(Fixtures.simple_nodenames.invalid_name)


@nodeprovider_unit.test
def add_nodes_as_properties():
    """(.*)NodeProvider.add(..., as_property=True)."""

    with empty_rdflib_nodeprovider() as provider:

        for propname in Fixtures.simple_properties.names:
            ret = provider.add(propname, as_property=True)
            assert isinstance(ret, provider.classes['bnode'])
            assert getattr(provider.ns, propname) == ret
            assert propname in provider.ns
            assert (
                (ret, rdflib.RDFS.label, rdflib.Literal(propname))
                in list(provider.graph.triples((None, None, None)))
            )
            assert (
                (ret, rdflib.RDF.type, rdflib.RDF.Property)
                in list(provider.graph.triples((None, None, None)))
            )
            assert provider.get(propname) == ret
