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
            u'順位': u'junni',
            u'コンクリート': u'konkuriito',
        }
        not_added = u'hitanposaiken'

    class kana_kanji_names_specified:
        formalized_map = {
            u'宇宙{sora}': u'sora',
            u'大地{gaia}': u'gaia',
        }
        modification_map = {
            u'宇宙{sora}': u'宇宙',
            u'大地{gaia}': u'大地',
        }

    class kana_kanji_properties_specified:
        formalized_map = {
            u'part_of{attribute}': u'attribute',
            u'hyper{_type}': u'_type',
        }
        modification_map = {
            u'part_of{attribute}': u'part_of',
            u'hyper{_type}': u'hyper',
        }

    class simple_nodenames:
        formalized_map = {
            u'John': u'john',
            u'魂': u'tamashii',
        }
        invalid_name = u'3way'
        not_added = u'詐害行為取消権'

    class simple_properties:
        formalized_map = {
            u'part_of{attribute}': u'attribute',
            u'hyper{_type}': u'_type',
        }
        modification_map = {
            u'part_of{attribute}': u'part_of',
            u'hyper{_type}': u'hyper',
        }

    class kakasi_conversion:
        desired_conversion = {
            u'抵当権': u'teitouken',
            u'国民の休日': u'kokuminnokyuujitsu',
            u'公共のベランダ': u'koukyounoberanda',
            u'範囲': u'hanni',
            u'引渡し': u'hikiwatashi',  # kanji-kana mixed
            u'引渡シ': u'hikiwatashi',  # kanji-katakana mixed
            u'とらばーゆ': u'torabaayu',
        }

    class term_mixtures:
        class terms:
            formalized_map_ja = {
                u'食道': u'shokudou',
                u'胃': u'i',
                u'小腸': u'shouchou',
                u'省庁{chuuoukanchou}': u'chuuoukanchou',
                u'大腸': u'daichou',
            }
            name_modification_map_ja = {
                u'食道': u'食道',
                u'胃': u'胃',
                u'小腸': u'小腸',
                u'省庁{chuuoukanchou}': u'省庁',
                u'大腸': u'大腸',
            }
            formalized_map_en = {
                u'esophagus': u'esophagus',
                u'stomach': u'stomach',
                u'small intestine': u'small_intestine',
                u'large intestine': u'large_intestine',
            }
        class properties:
            formalized_map = {
                u'つづく': u'tsuduku',
                u'next': u'next',
            }
        not_added = u'rectum'

    class serialization:

        class terms:
            names = [
                u'人{hito}', u'権利能力',
                u'continuous consensus',
                u'行為能力', u'順位',
                u'競売{keibai}',
            ]
            serialized = (
                u"load_options:\n"
                u"    as_property: false\n"
                u"options:\n"
                u"    romanize: true\n"
                u"terms:\n"
                u"- continuous consensus{continuous_consensus}\n"
                u"- 人{hito}\n"
                u"- 順位{junni}\n"
                u"- 競売{keibai}\n"
                u"- 権利能力{kenrinouryoku}\n"
                u"- 行為能力{kouinouryoku}\n"
            )

        class props:
            names = [u'hyper', u'status of']
            serialized = (
                u"load_options:\n"
                u"    as_property: true\n"
                u"options:\n"
                u"    romanize: false\n"
                u"terms:\n"
                u"- hyper{hyper}\n"
                u"- status of{status_of}\n"
            )


# Adding names.

@nameprovider_unit.test
def add_simple_names():
    """NameProvider.add."""
    with empty_nameprovider() as provider:

        # additions & returned values
        for name in Fixtures.simple_names.formalized_map:
            ret = provider.add(name)
            expected_formalized = Fixtures.simple_names.formalized_map[name]
            assert ret == expected_formalized

        # avoiding name conflicts
        for name in Fixtures.simple_names.formalized_map:
            with raises(nodeprovider.NameConflict):
                provider.add(name)

        # namespace & reverse lookup
        namespace = provider.ns
        for name in Fixtures.simple_names.formalized_map:
            formalized_name = Fixtures.simple_names.formalized_map[name]
            assert formalized_name in namespace
            assert getattr(namespace, formalized_name) == name
            assert provider.get_ns_identifier(name) == formalized_name

        # reference error
        with raises(nodeprovider.NameNotRegistered):
            provider.get_ns_identifier(Fixtures.simple_names.not_added)

        # property for source texts
        assert (set(provider.origin_names) ==
                set(Fixtures.simple_names.formalized_map.keys()))

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

        # additions & returned values
        for name in Fixtures.kana_kanji_names.formalized_map:
            ret = provider.add(name)
            expected_formalized = Fixtures.kana_kanji_names.formalized_map[name]
            assert ret == expected_formalized

        # avoiding name conflicts
        for name in Fixtures.kana_kanji_names.formalized_map:
            formalized_name = Fixtures.kana_kanji_names.formalized_map[name]
            with raises(nodeprovider.NameConflict):
                provider.add(name)
            with raises(nodeprovider.NameConflict):
                provider.add(formalized_name)

        # namespace & reverse lookup
        namespace = provider.ns
        for name in Fixtures.kana_kanji_names.formalized_map:
            formalized_name = Fixtures.kana_kanji_names.formalized_map[name]
            assert getattr(namespace, formalized_name) == name
            assert provider.get_ns_identifier(name) == formalized_name

        # reference error
        with raises(nodeprovider.NameNotRegistered):
            provider.get_ns_identifier(Fixtures.kana_kanji_names.not_added)

        # property for source texts
        assert (set(provider.origin_names) ==
                set(Fixtures.kana_kanji_names.formalized_map.keys()))

@nameprovider_unit.test
def handle_specified_reading_addition():
    """
    NameProvider with romanize=True, with specified kana reading.
    """
    with empty_nameprovider(romanize=True) as provider:

        # additions & returned values
        for name in Fixtures.kana_kanji_names_specified.formalized_map:
            ret = provider.add(name)
            expected_formalized = Fixtures.kana_kanji_names_specified.formalized_map[name]
            assert ret == expected_formalized

        # namespace & reverse lookup
        namespace = provider.ns
        for name in Fixtures.kana_kanji_names_specified.formalized_map:
            formalized_name = Fixtures.kana_kanji_names_specified.formalized_map[name]
            modified_name = Fixtures.kana_kanji_names_specified.modification_map[name]
            assert getattr(namespace, formalized_name) == modified_name
            assert provider.get_ns_identifier(modified_name) == formalized_name

        # additions & returned values
        for name in Fixtures.kana_kanji_properties_specified.formalized_map:
            ret = provider.add(name)
            expected_formalized = Fixtures.kana_kanji_properties_specified.formalized_map[name]
            assert ret == expected_formalized

        # namespace & reverse lookup
        namespace = provider.ns
        for name in Fixtures.kana_kanji_properties_specified.formalized_map:
            formalized_name = Fixtures.kana_kanji_properties_specified.formalized_map[name]
            modified_name = Fixtures.kana_kanji_properties_specified.modification_map[name]
            assert getattr(namespace, formalized_name) == modified_name
            assert provider.get_ns_identifier(modified_name) == formalized_name


# simple kakasi caller.
@kakasi_unit.test
def kakasi_conversion():
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

        # additions & returned values
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
            # reverse lookup
            assert provider.get_identifier_from(ret) == formalized_name
            assert provider.get_origin_name_from(ret) == name

        # avoiding name conflicts
        with raises(nodeprovider.InvalidName):
            provider.add(Fixtures.simple_nodenames.invalid_name)

        # reference error
        with raises(nodeprovider.NameNotRegistered):
            provider.get(Fixtures.simple_nodenames.invalid_name)

        with raises(nodeprovider.NodeNotRegistered):
            provider.get_identifier_from(rdflib.BNode())
        with raises(nodeprovider.NodeNotRegistered):
            provider.get_origin_name_from(rdflib.BNode())

@nodeprovider_unit.test
def add_nodes_as_properties():
    """(.*)NodeProvider.add(..., as_property=True)."""

    with empty_rdflib_nodeprovider() as provider:

        for propname in Fixtures.simple_properties.formalized_map:
            ret = provider.add(propname, as_property=True)
            propid = Fixtures.simple_properties.formalized_map[propname]
            mod_propname = Fixtures.simple_properties.modification_map[propname]
            assert isinstance(ret, provider.classes['bnode'])
            assert getattr(provider.ns, propid) == ret
            assert propid in provider.ns
            assert (
                (ret, rdflib.RDFS.label, rdflib.Literal(mod_propname))
                in list(provider.graph.triples((None, None, None)))
            )
            assert (
                (ret, rdflib.RDF.type, rdflib.RDF.Property)
                in list(provider.graph.triples((None, None, None)))
            )
            assert provider.get(mod_propname) == ret
            assert provider.get_identifier_from(ret) == propid
            assert provider.get_origin_name_from(ret) == mod_propname

@nodeprovider_unit.test
def merge_node_providers():
    """Merge multiple (.*)NodeProviders."""

    with empty_rdflib_nodeprovider(romanize=True) as provider_ja,\
         empty_rdflib_nodeprovider(romanize=False) as provider_en,\
         empty_rdflib_nodeprovider(romanize=True) as provider_prop:

        # Build each provider.
        for name in Fixtures.term_mixtures.terms.formalized_map_ja:
            provider_ja.add(name)
        for name in Fixtures.term_mixtures.terms.formalized_map_en:
            provider_en.add(name)
        for name in Fixtures.term_mixtures.properties.formalized_map:
            provider_prop.add(name, as_property=True)

        # Merge & check returned object.
        merged_provider = nodeprovider.merge_nodeproviders(
            provider_ja, provider_en, provider_prop,
        )

        assert isinstance(merged_provider, nodeprovider.RDFLibNodeProvider)

        # Check namespace integrations.

        formalized_map_all = {}
        formalized_map_all.update(Fixtures.term_mixtures.terms.formalized_map_ja)
        formalized_map_all.update(Fixtures.term_mixtures.terms.formalized_map_en)
        formalized_map_all.update(Fixtures.term_mixtures.properties.formalized_map)

        name_modification_map = {}
        name_modification_map.update(Fixtures.term_mixtures.terms.name_modification_map_ja)
        name_modification_map.update(
            {key:key for key in Fixtures.term_mixtures.terms.formalized_map_en}
        )
        name_modification_map.update(
            {key:key for key in Fixtures.term_mixtures.properties.formalized_map}
        )

        merged_ns = merged_provider.ns
        for name in formalized_map_all:

            modified_name = name_modification_map[name]
            formalized_name = formalized_map_all[name]
            assert formalized_name in merged_ns

            node = getattr(merged_ns, formalized_name)
            assert isinstance(node, merged_provider.classes['bnode'])
            assert merged_provider.get(modified_name) == node
            assert merged_provider.get_identifier_from(node) == formalized_name
            assert merged_provider.get_origin_name_from(node) == modified_name

        # Check graph integratoins.
        graph = merged_provider.graph
        triples = list(graph.triples((None, None, None)))
        ## labels
        for name in formalized_map_all:
            modified_name = name_modification_map[name]
            formalized_name = formalized_map_all[name]
            node = getattr(merged_ns, formalized_name)
            assert (node, rdflib.RDFS.label, rdflib.Literal(modified_name)) in triples
        ## properties
        for name in Fixtures.term_mixtures.properties.formalized_map:
            formalized_name = formalized_map_all[name]
            propnode = getattr(merged_ns, formalized_name)
            assert (propnode, rdflib.RDF.type, rdflib.RDF.Property) in triples

        # Check namespace management.
        for name in formalized_map_all:
            with raises(nodeprovider.NameConflict):
                merged_provider.add(name)

        # reference error
        with raises(nodeprovider.NameNotRegistered):
            merged_provider.get(Fixtures.term_mixtures.not_added)

@nodeprovider_unit.test
def serialization():
    """Serialize registered names of NodeProvider."""

    with empty_rdflib_nodeprovider(romanize=True) as np:
        for name in Fixtures.serialization.terms.names:
            np.add(name)
        assert np.serialize() == Fixtures.serialization.terms.serialized

    with empty_rdflib_nodeprovider(romanize=False) as np:
        for name in Fixtures.serialization.props.names:
            np.add(name, as_property=True)
        assert np.serialize(as_property=True) == Fixtures.serialization.props.serialized
