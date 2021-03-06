# encoding: utf-8

from attest import (
    Tests, assert_hook,
    contextmanager, raises,
)
import rdflib
from lkbutils import relationprovider


relationchecker_unit = Tests()
relationprovider_unit = Tests()


@contextmanager
def empty_relationchecker(**options):
    try:
        yield relationprovider.RelationChecker(**options)
    finally:
        pass

@contextmanager
def empty_rdflib_relationprivider(**options):
    try:
        yield relationprovider.RDFLibRelationProvider(**options)
    finally:
        pass


class Fixtures:

    class acyclic:
        pairs = [
            (u'Kanagawa', u'Tokyo'),
            (u'Tokyo', u'Saitama'),
            (u'Saitama', u'Gumma'),
            (u'Gumma', u'Nagano'),
            (u'Nagano', u'Yamanashi'),
            (u'Nagano', u'Toyama'),
            (u'Nagano', u'Gifu'),
            (u'Yamanashi', u'Kanagawa'),
        ]

    class serialization:
        names = [
            u'Ueno', u'Akihabara',
            u'Harajuku', u'Yoyogi',
            u'Komagome', u'Tabata',
            u'Shinagawa', u'Osaki',
            u'Mejiro', u'Takadanobaba',
        ]
        dummy_nodes = {name: rdflib.BNode() for name in names}
        pairs = [
            (u'Ueno', u'Akihabara'),
            (u'Harajuku', u'Yoyogi'),
            (u'Komagome', u'Tabata'),
            (u'Shinagawa', u'Osaki'),
            (u'Mejiro', u'Takadanobaba'),
        ]
        opts = dict(
            dry=True,
            acyclic=True,
        )
        serialized = (
            u"options:\n"
            u"    acyclic: true\n"
            u"    dry: true\n"
            u"    nointerlinks: false\n"
            u"pairs:\n"
            u"- Harajuku Yoyogi\n"
            u"- Komagome Tabata\n"
            u"- Mejiro Takadanobaba\n"
            u"- Shinagawa Osaki\n"
            u"- Ueno Akihabara\n"
        )


# relation rules checker 

@relationchecker_unit.test
def relation_name():
    """Property for relation descriptor."""
    with empty_relationchecker(relation=u'myrelation') as relchkr:
        assert relchkr.relation == u'myrelation'

@relationchecker_unit.test
def dry_links():
    """Do not repeat same relations."""

    with empty_relationchecker(relation=u'next_to') as relchkr:
        ret_add_first = relchkr.add(u'Tokyo', u'Saitama')
        assert ret_add_first == (u'Tokyo', u'Saitama')
        ret_add_second = relchkr.add(u'Tokyo', u'Saitama')
        assert ret_add_second == (u'Tokyo', u'Saitama')

    with empty_relationchecker(relation=u'next_to', dry=True) as relchkr:
        ret_add = relchkr.add(u'Tokyo', u'Saitama')
        assert ret_add == (u'Tokyo', u'Saitama')
        with raises(relationprovider.RedundantRelation):
            relchkr.add(u'Tokyo', u'Saitama')

@relationchecker_unit.test
def no_interlinks():
    """Do not create interlinks under the same relation."""

    with empty_relationchecker(relation=u'next_to') as relchkr:
        ret_add = relchkr.add(u'Yamanashi', u'Tokyo')
        assert ret_add == (u'Yamanashi', u'Tokyo')
        ret_add_inverse = relchkr.add(u'Tokyo', u'Yamanashi')
        assert ret_add_inverse == (u'Tokyo', u'Yamanashi')

    with empty_relationchecker(relation=u'next_to', nointerlinks=True) as relchkr:
        ret_add = relchkr.add(u'Yamanashi', u'Tokyo')
        assert ret_add == (u'Yamanashi', u'Tokyo')
        with raises(relationprovider.InterLink):
            relchkr.add(u'Tokyo', u'Yamanashi')

@relationchecker_unit.test
def acyclic_graph():
    """Do not create cycles under the same relation."""

    pairs = Fixtures.acyclic.pairs

    with empty_relationchecker(relation=u'next_to') as relchkr:
        for pair in pairs:
            ret = relchkr.add(*pair)
            assert ret == tuple(pair)

    with empty_relationchecker(relation=u'next_to', acyclic=True) as relchkr:
        for pair in pairs[:-1]:
            ret = relchkr.add(*pair)
            assert ret == tuple(pair)
        with raises(relationprovider.Cyclic):
            relchkr.add(*pairs[-1])

@relationchecker_unit.test
def mixed_rules():
    """Keep multiple rules."""

    # Note that if a graph is acyclic, it does not contains interlinks!

    # dry & acyclic
    with empty_relationchecker(relation=u'next_to', dry=True, acyclic=True) as relchkr:
        relchkr.add(u'Tokushima', u'Kouchi')
        with raises(relationprovider.RedundantRelation):
            relchkr.add(u'Tokushima', u'Kouchi')
    with empty_relationchecker(relation=u'next_to', dry=True, acyclic=True) as relchkr:
        relchkr.add(u'Tokushima', u'Kouchi')
        relchkr.add(u'Kouchi', u'Ehime')
        with raises(relationprovider.Cyclic):
            relchkr.add(u'Ehime', u'Tokushima')

    # dry & no interlinks
    with empty_relationchecker(relation=u'next_to', dry=True, nointerlinks=True) as relchkr:
        relchkr.add(u'Shimane', u'Yamaguchi')
        with raises(relationprovider.RedundantRelation):
            relchkr.add(u'Shimane', u'Yamaguchi')
    with empty_relationchecker(relation=u'next_to', dry=True, nointerlinks=True) as relchkr:
        relchkr.add(u'Shimane', u'Yamaguchi')
        relchkr.add(u'Hiroshima', u'Yamaguchi')
        with raises(relationprovider.InterLink):
            relchkr.add(u'Yamaguchi', u'Hiroshima')


# Adding relations under policies.

@relationprovider_unit.test
def relationprovider_on_toplevel():
    """RelationProvider subclasses are accessible on pkg's toplevel ns."""
    from lkbutils import RDFLibRelationProvider

@relationprovider_unit.test
def add_relations():
    """(.*)RelationProvider.add / with no restrictions."""

    hyper = rdflib.RDF.type
    node_root = rdflib.BNode()
    node_left = rdflib.BNode()
    node_right = rdflib.BNode()

    with empty_rdflib_relationprivider(relation=hyper) as provider:
        ret_l2root = provider.add(node_left, node_root)
        ret_r2root = provider.add(node_right, node_root)
        assert ret_l2root == (node_left, node_root)
        assert ret_r2root == (node_right, node_root)

        triples = list(provider.graph.triples((None, None, None)))

        assert (node_left, hyper, node_root) in triples
        assert (node_right, hyper, node_root) in triples

    # with identifier (options acceptance only)
    with empty_rdflib_relationprivider(relation=hyper) as provider:
        ret_l2root = provider.add(
            node_left, node_root,
            src_id=u'left', dest_id=u'right',
        )
        assert ret_r2root == (node_right, node_root)
        assert (
            (node_left, hyper, node_root)
            in list(provider.graph.triples((None, None, None)))
        )

@relationprovider_unit.test
def add_relations_with_rules():
    """(.*)RelationProvider.add / with some restrictions."""

    hyper = rdflib.RDF.type
    context = dict(
        relation=hyper,
        dry=True, acyclic=True, nointerlinks=True,
    )

    unique_nodes = [rdflib.BNode() for i in range(5)]

    # dry
    with empty_rdflib_relationprivider(**context) as provider:
        provider.add(unique_nodes[0], unique_nodes[1])
        with raises(relationprovider.RedundantRelation):
            provider.add(unique_nodes[0], unique_nodes[1])

    # no-interlinks
    with empty_rdflib_relationprivider(**context) as provider:
        provider.add(unique_nodes[0], unique_nodes[1])
        with raises(relationprovider.InterLink):
            provider.add(unique_nodes[1], unique_nodes[0])

    # acyclic
    with empty_rdflib_relationprivider(**context) as provider:
        provider.add(unique_nodes[0], unique_nodes[1])
        provider.add(unique_nodes[1], unique_nodes[4])
        provider.add(unique_nodes[4], unique_nodes[2])
        with raises(relationprovider.Cyclic):
            provider.add(unique_nodes[2], unique_nodes[0])

    # acyclic + identifier labels
    entries = [
        u'Kagoshima',
        u'Miyazaki',
        u'Ohita',
        u'Fukuoka',
        u'Kumamoto',
    ]
    data = {e: rdflib.BNode() for e in entries}
    with empty_rdflib_relationprivider(**context) as provider:
        for src, dest in zip(entries, entries[1:]):
            provider.add(
                data[src], data[dest],
                src_id=src, dest_id=dest,
            )

        kumamoto = u'Kumamoto'
        kagoshima = u'Kagoshima'
        with raises(relationprovider.Cyclic) as error:
            provider.add(
                data[kumamoto], data[kagoshima],
                src_id=kumamoto, dest_id=kagoshima,
            )

        error_prepend = u'cyclic path found on "{}": '.format(hyper)
        empty, error_prepend, path = error.custom_msg.partition(error_prepend)
        traced_path = path.split(u' -> ')
        assert set(traced_path) == set(entries)

@relationprovider_unit.test
def providers_noconflict():
    """Check given relation providers have no conflicts on pairs."""

    nodes = [rdflib.BNode() for i in range(8)]

    pairs_1 = [
        (nodes[0], nodes[1]),
        (nodes[2], nodes[3]),
    ]
    pairs_2 = [
        (nodes[4], nodes[5]),
        (nodes[6], nodes[7]),
    ]

    with empty_rdflib_relationprivider(relation=rdflib.RDF.type) as provider_r1, \
         empty_rdflib_relationprivider(relation=rdflib.RDF.type) as provider_r2:

        for p1 in pairs_1:
            provider_r1.add(*p1)
        for p2 in pairs_2:
            provider_r2.add(*p2)

        assert (relationprovider.noconflict_providers([provider_r1, provider_r2]) ==
                set(pairs_1 + pairs_2))

        provider_r1.add(*pairs_2[0])

        with raises(relationprovider.RedundantRelation) as error:
            relationprovider.noconflict_providers([provider_r1, provider_r2])
        assert error.src == pairs_2[0][0]
        assert error.dest == pairs_2[0][1]

@relationprovider_unit.test
def serialization():
    """Serialize registered relations into a YAML."""
    relation = rdflib.BNode()
    nodes = Fixtures.serialization.dummy_nodes

    with empty_rdflib_relationprivider(relation=relation,
                                       **Fixtures.serialization.opts) as rp:

        for pair in Fixtures.serialization.pairs:
            src, dest = pair
            nodepair = (nodes[src], nodes[dest])
            rp.add(
                nodepair[0], nodepair[1],
                src_id=src, dest_id=dest,
            )

        assert rp.serialize() == Fixtures.serialization.serialized
