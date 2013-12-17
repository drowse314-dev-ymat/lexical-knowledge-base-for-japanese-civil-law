# encoding: utf-8

from attest import (
    Tests, assert_hook,
    raises, contextmanager,
)
import rdflib
from lkbutils import declarative
from lkbutils.relationprovider import RedundantRelation, Cyclic


termloader_unit = Tests()
relationloader_unit = Tests()


@contextmanager
def new_rdflib_termloader(**options):
    try:
        yield declarative.RDFLibTermLoader(**options)
    finally:
        pass

@contextmanager
def new_rdflib_relationloader(**options):
    try:
        yield declarative.RDFLibRelationLoader(**options)
    finally:
        pass


class Fixtures(object):
    """Namespace for fixtures."""

    class NS(object):
        pass

    # law terms
    law_terms = NS()
    law_terms.flat = [
        u'抵当権', u'質権', u'詐害行為取消権', u'制限行為能力者',
    ]
    law_terms.struct = {
        u'権利': [
            {u'物権': [u'抵当権', u'質権']},
            {u'請求権': [u'詐害行為取消権']},
        ],
        u'人': [u'制限行為能力者'],
    }
    law_terms.identifiers = {
        u'teitouken': u'抵当権',
        u'shichiken': u'質権',
        u'sagaikouitorikeshiken': u'詐害行為取消権',
        u'seigenkouinouryokumono': u'制限行為能力者',
    }

    # general properties
    basic_properties = NS()
    basic_properties.flat = [
        u'hyper', u'part_of{attribute}', u'contrary',
    ]
    basic_properties.identifiers = {
        u'hyper': u'hyper',
        u'attribute': u'part_of',
        u'contrary': u'contrary',
    }

    # japanese prefectures
    jp_prefectures = NS()
    jp_prefectures.flat_yaml = (
        u"terms:\n"
        u"    - 京都\n"
        u"    - 奈良\n"
        u"    - 島根\n"
        u"    - 神奈川\n"
        u"    - 福島\n"
    )
    jp_prefectures.struct_yaml = (
        u"terms:\n"
        u"    府:\n"
        u"        政令指定都市がある:\n"
        u"            - 京都\n"
        u"    県:\n"
        u"        政令指定都市がある:\n"
        u"            - 神奈川\n"
        u"        ない:\n"
        u"            - 奈良\n"
        u"            - 島根\n"
        u"            - 福島\n"
    )
    jp_prefectures.identifiers = {
        u'kyouto': u'京都',
        u'nara': u'奈良',
        u'shimane': u'島根',
        u'kanagawa': u'神奈川',
        u'fukushima': u'福島',
    }

    # predicate-style python funcs
    python_predicates = NS()
    python_predicates.yaml = (
        u"options:\n"
        u"    as_property: yes\n"
        u"terms:\n"
        u"    - isinstance{_type}\n"
        u"    - issubclass\n"
        u"    - hasattr{_has}\n"
    )
    python_predicates.identifiers = {
        u'_type': u'isinstance',
        u'issubclass': u'issubclass',
        u'_has': u'hasattr',
    }

    # world & japanese rivers
    world_rivers = NS()
    world_rivers.definition_yaml = (
        u"options:\n"
        u"    romanize: yes\n"
        u"terms:\n"
        u"    egypt:\n"
        u"        - nile\n"
        u"    brazil:\n"
        u"        - amazon\n"
        u"    china:\n"
        u"        - 長江\n"
        u"    japan:\n"
        u"        中部地方:\n"
        u"            - 信濃川\n"
    )
    world_rivers.identifiers = {
        u'nile': u'nile', u'amazon': u'amazon',
        u'choukou': u'長江', u'shinanokawa': u'信濃川',
    }
    world_rivers.prop_definition_yaml = (
        u"options:\n"
        u"    romanize: yes\n"
        u"load_options:\n"
        u"    as_property: yes\n"
        u"terms:\n"
        u"    - longer than\n"
        u"    - wider than\n"
    )
    world_rivers.prop_identifiers = {
        u'longer_than': u'longer than',
        u'wider_than': u'wider than',
    }

    # 出世魚
    shusse_uo = NS()
    shusse_uo.core_relation = u'shusse_uo'
    shusse_uo.core_relation_identifier = u'shusse'
    shusse_uo.terms = [
        u'shusse',
        u'wakashi', u'inada', u'warasa', u'buri',
    ]
    shusse_uo.relation_pairs = [
        (u'wakashi', u'inada'),
        (u'inada', u'warasa'),
        (u'warasa', u'buri'),
    ]
    shusse_uo.additions = NS()
    shusse_uo.additions.addcycle = [(u'buri', u'wakashi')]
    shusse_uo.additions.redundant = [(u'warasa', u'buri')]

    # US geo. relation configs
    us_geo_rel_cfg = NS()
    us_geo_rel_cfg.yaml = (
        u"options:\n"
        u"    dry: yes\n"
        u"    nointerlinks: no\n"
        u"    acyclic: no\n"
        u"relations:\n"
        u"    next_to:\n"
        u"        options:\n"
        u"            acyclic: yes\n"
        u"        pairs:\n"
        u"            南:\n"
        u"                - missisippi arkansas\n"
        u"            北西:\n"
        u"                - washington oregon\n"
        u"    far_from:\n"
        u"        options:\n"
        u"            dry: no\n"
        u"        pairs:\n"
        u"            - alabama nebraska\n"
    )
    us_geo_rel_cfg.relations = NS()
    us_geo_rel_cfg.relations.next_to = u'next_to'
    us_geo_rel_cfg.relations.far_from = u'far_from'
    us_geo_rel_cfg.expects = NS()
    us_geo_rel_cfg.expects.attr_casts = {
        u'relation': unicode,
        u'options': dict,
        u'pairs': set,
    }
    us_geo_rel_cfg.expects.next_to = {
        u'relation': u'next_to',
        u'options': {u'dry': True, u'nointerlinks': False, u'acyclic': True},
        u'pairs': [
            (u'washington', u'oregon'),
            (u'missisippi', u'arkansas'),
        ],
    }
    us_geo_rel_cfg.expects.far_from = {
        u'relation': u'far_from',
        u'options': {u'dry': False, u'nointerlinks': False, u'acyclic': False},
        u'pairs': [
            (u'alabama', u'nebraska'),
        ],
    }

    # US geo. relation definitions
    def_us_geo_rels = NS()
    def_us_geo_rels.terms = [
        u'next_to',
        u'tikai',
        u'missisippi', u'arkansas', u'tennessee', u'alabama',
    ]
    def_us_geo_rels.definition_yaml = (
        u"options:\n"
        u"    dry: yes\n"
        u"    nointerlinks: yes\n"
        u"    acyclic: no\n"
        u"relations:\n"
        u"    next_to:\n"
        u"        options:\n"
        u"            acyclic: yes\n"
        u"        pairs:\n"
        u"            南:\n"
        u"                - missisippi arkansas\n"
        u"                - arkansas tennessee\n"
        u"                - tennessee alabama\n"
        u"    tikai:\n"
        u"        pairs:\n"
        u"            - missisippi arkansas\n"
        u"            - arkansas tennessee\n"
        u"            - tennessee alabama\n"
    )
    def_us_geo_rels.relations = NS()
    def_us_geo_rels.relations.next_to = u'next_to'
    def_us_geo_rels.relations.tikai = u'tikai'
    def_us_geo_rels.relation_pairs = [
        (u'missisippi', u'arkansas'),
        (u'arkansas', u'tennessee'),
        (u'tennessee', u'alabama'),
    ]
    def_us_geo_rels.additions = NS()
    def_us_geo_rels.additions.redundant = [(u'missisippi', u'arkansas')]
    def_us_geo_rels.additions.addcycle = [(u'alabama', u'missisippi')]


def rdflib_getlabel(graph, node):
    return list(graph.objects(subject=node, predicate=rdflib.RDFS.label))[0].value


@termloader_unit.test
def load_terms_from_data():
    """Load terms directly from data."""

    # flat
    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load(Fixtures.law_terms.flat)
        ns = termloader.ns
        graph = termloader.graph
        for id_label in Fixtures.law_terms.identifiers:
            node = getattr(ns, id_label)
            assert id_label in ns
            assert isinstance(node, rdflib.BNode)
            assert (rdflib_getlabel(graph, node) ==
                    Fixtures.law_terms.identifiers[id_label])

    # structured
    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load(Fixtures.law_terms.struct)
        ns = termloader.ns
        graph = termloader.graph
        for id_label in Fixtures.law_terms.identifiers:
            node = getattr(ns, id_label)
            assert id_label in ns
            assert isinstance(node, rdflib.BNode)
            assert (rdflib_getlabel(graph, node) ==
                    Fixtures.law_terms.identifiers[id_label])

    # properties
    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load(Fixtures.basic_properties.flat, as_property=True)
        ns = termloader.ns
        graph = termloader.graph
        triples = list(termloader.graph.triples((None, None, None)))
        for id_label in Fixtures.basic_properties.identifiers:
            node = getattr(ns, id_label)
            assert id_label in ns
            assert isinstance(node, rdflib.BNode)
            assert (rdflib_getlabel(graph, node) ==
                    Fixtures.basic_properties.identifiers[id_label])
            assert (node, rdflib.RDF.type, rdflib.RDF.Property) in triples

@termloader_unit.test
def load_terms_from_yaml():
    """Load terms from YAML representation."""

    # flat
    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load_yaml(Fixtures.jp_prefectures.flat_yaml)
        ns = termloader.ns
        graph = termloader.graph
        for id_label in Fixtures.jp_prefectures.identifiers:
            node = getattr(ns, id_label)
            assert id_label in ns
            assert isinstance(node, rdflib.BNode)
            assert (rdflib_getlabel(graph, node) ==
                    Fixtures.jp_prefectures.identifiers[id_label])

    # structured
    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load_yaml(Fixtures.jp_prefectures.struct_yaml)
        ns = termloader.ns
        graph = termloader.graph
        for id_label in Fixtures.jp_prefectures.identifiers:
            node = getattr(ns, id_label)
            assert id_label in ns
            assert isinstance(getattr(ns, id_label), rdflib.BNode)
            assert (rdflib_getlabel(graph, node) ==
                    Fixtures.jp_prefectures.identifiers[id_label])

    # properties
    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load_yaml(Fixtures.python_predicates.yaml)
        ns = termloader.ns
        graph = termloader.graph
        triples = list(termloader.graph.triples((None, None, None)))
        for id_label in Fixtures.python_predicates.identifiers:
            node = getattr(ns, id_label)
            assert id_label in ns
            assert isinstance(node, rdflib.BNode)
            assert (rdflib_getlabel(graph, node) ==
                    Fixtures.python_predicates.identifiers[id_label])
            assert (node, rdflib.RDF.type, rdflib.RDF.Property) in triples

@termloader_unit.test
def load_terms_from_yaml_on_demand():
    """Load terms from YAML representation using declarative.load_terms."""
    termloader = declarative.rdflib_load_terms(Fixtures.world_rivers.definition_yaml)
    ns = termloader.ns
    graph = termloader.graph
    for id_label in Fixtures.world_rivers.identifiers:
        node = getattr(ns, id_label)
        assert id_label in ns
        assert isinstance(node, rdflib.BNode)
        assert (rdflib_getlabel(graph, node) ==
                Fixtures.world_rivers.identifiers[id_label])

@termloader_unit.test
def load_properties_from_yaml_on_demand():
    """Load properties from YAML representation using declarative.load_terms."""
    termloader = declarative.rdflib_load_terms(Fixtures.world_rivers.prop_definition_yaml)
    ns = termloader.ns
    graph = termloader.graph
    triples = list(graph.triples((None, None, None)))
    for id_label in Fixtures.world_rivers.prop_identifiers:
        node = getattr(ns, id_label)
        assert id_label in ns
        assert isinstance(node, rdflib.BNode)
        assert (rdflib_getlabel(graph, node) ==
                Fixtures.world_rivers.prop_identifiers[id_label])
        assert (node, rdflib.RDF.type, rdflib.RDF.Property) in triples

@termloader_unit.test
def toplevel_termloader():
    """lkbutils.declarative.load_terms is accessible from top-level."""
    from lkbutils import rdflib_load_terms


class MockRDFLibNamespace(object):

    def __init__(self, names):
        self.namespace = self.create_ns(names)

    @property
    def ns(self):
        return self.namespace

    def create_ns(self, names):
        class NS:
            pass
        ns = NS()
        for name in names:
            setattr(ns, name, rdflib.BNode())
        return ns


@relationloader_unit.test
def load_relations_from_data():
    """Load node relations directly from structured data."""

    nodeprovider = MockRDFLibNamespace(Fixtures.shusse_uo.terms)

    with new_rdflib_relationloader(nodeprovider=nodeprovider,
                                   relation=Fixtures.shusse_uo.core_relation_identifier,
                                   dry=True, acyclic=True) as relloader:
        relloader.load(Fixtures.shusse_uo.relation_pairs)
        triples = list(relloader.graph.triples((None, None, None)))
        for relsrc, reldest in Fixtures.shusse_uo.relation_pairs:
            noderel = (getattr(nodeprovider.ns, relsrc),
                       nodeprovider.ns.shusse,
                       getattr(nodeprovider.ns, reldest))
            assert noderel in triples

        with raises(Cyclic):
            relloader.load(Fixtures.shusse_uo.additions.addcycle)
        with raises(RedundantRelation):
            relloader.load(Fixtures.shusse_uo.additions.redundant)

@relationloader_unit.test
def relation_configs_from_yaml():
    """
    Parse YAML representation & generate configs. to create RelationLoader.
    """
    # mapping {relation => config}
    relation_definitions = declarative.rdflib_load_relcfg(Fixtures.us_geo_rel_cfg.yaml)

    config_attr_casts = Fixtures.us_geo_rel_cfg.expects.attr_casts

    parsed_next_to_cfg = relation_definitions[Fixtures.us_geo_rel_cfg.relations.next_to]
    for config_attr in config_attr_casts:
        cast = config_attr_casts[config_attr]
        assert (
            cast(parsed_next_to_cfg[config_attr]) ==
            cast(Fixtures.us_geo_rel_cfg.expects.next_to[config_attr])
        )

    parsed_far_from_cfg = relation_definitions[Fixtures.us_geo_rel_cfg.relations.far_from]
    for config_attr in config_attr_casts:
        cast = config_attr_casts[config_attr]
        assert (
            cast(parsed_far_from_cfg[config_attr]) ==
            cast(Fixtures.us_geo_rel_cfg.expects.far_from[config_attr])
        )

@relationloader_unit.test
def load_relations_from_yaml():
    """Load node relations from YAML representation."""

    nodeprovider = MockRDFLibNamespace(Fixtures.def_us_geo_rels.terms)

    relloaders = declarative.rdflib_load_relations(
        Fixtures.def_us_geo_rels.definition_yaml,
        nodeprovider=nodeprovider,
    )
    relloader_next_to = relloaders[Fixtures.def_us_geo_rels.relations.next_to]
    relloader_tikai = relloaders[Fixtures.def_us_geo_rels.relations.tikai]

    # pairs loaded

    triples_next_to = list(relloader_next_to.graph.triples((None, None, None)))
    for relsrc, reldest in Fixtures.def_us_geo_rels.relation_pairs:
        noderel = (getattr(nodeprovider.ns, relsrc),
                   nodeprovider.ns.next_to,
                   getattr(nodeprovider.ns, reldest))
        assert noderel in triples_next_to

    triples_tikai = list(relloader_tikai.graph.triples((None, None, None)))
    for relsrc, reldest in Fixtures.def_us_geo_rels.relation_pairs:
        noderel = (getattr(nodeprovider.ns, relsrc),
                   nodeprovider.ns.tikai,
                   getattr(nodeprovider.ns, reldest))
        assert noderel in triples_tikai

    # rules

    with raises(RedundantRelation):
        relloader_next_to.load(Fixtures.def_us_geo_rels.additions.redundant)
    with raises(Cyclic):
        relloader_next_to.load(Fixtures.def_us_geo_rels.additions.addcycle)

    with raises(RedundantRelation):
        relloader_tikai.load(Fixtures.def_us_geo_rels.additions.redundant)
    relloader_tikai.load(Fixtures.def_us_geo_rels.additions.addcycle)

@relationloader_unit.test
def toplevel_relationloader():
    """lkbutils.declarative.load_relations is accessible from top-level."""
    from lkbutils import rdflib_load_relations
