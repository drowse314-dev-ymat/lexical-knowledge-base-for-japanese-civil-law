# encoding: utf-8

from attest import (
    Tests, assert_hook,
    raises, contextmanager,
)
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


@termloader_unit.test
def load_terms_from_data():
    """Load terms directly from data."""

    import rdflib

    # flat list
    flat_terms = [
        u'抵当権', u'質権', u'詐害行為取消権', u'制限行為能力者',
    ]
    # structured
    structured_terms = {
        u'権利': [
            {u'物権': [u'抵当権', u'質権']},
            {u'請求権': [u'詐害行為取消権']},
        ],
        u'人': [u'制限行為能力者'],
    }
    identifiers = [
        u'teitouken',
        u'shichiken',
        u'sagaikouitorikeshiken',
        u'seigenkouinouryokumono',
    ]

    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load(flat_terms)
        ns = termloader.ns
        for id_label in identifiers:
            assert id_label in ns
            assert isinstance(getattr(ns, id_label), rdflib.BNode)

    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load(structured_terms)
        ns = termloader.ns
        for id_label in identifiers:
            assert id_label in ns
            assert isinstance(getattr(ns, id_label), rdflib.BNode)

    # properties
    props = [
        u'hyper', u'part_of', u'contrary',
    ]
    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load(props, as_property=True)
        ns = termloader.ns
        tripes = list(termloader.graph.triples((None, None, None)))
        for id_label in props:
            assert id_label in ns
            assert isinstance(getattr(ns, id_label), rdflib.BNode)
            assert (getattr(ns, id_label), rdflib.RDF.type, rdflib.RDF.Property)

@termloader_unit.test
def load_terms_from_yaml():
    """Load terms from YAML representation."""

    import rdflib

    # flat list
    flat_terms_yaml = u"""\
terms:
    - 京都
    - 奈良
    - 島根
    - 神奈川
    - 福島\
"""

    # structured
    structured_terms_yaml = u"""\
terms:
    府:
        政令指定都市がある:
            - 京都
    県:
        政令指定都市がある:
            - 神奈川
        ない:
            - 奈良
            - 島根
            - 福島\
"""

    identifiers = [
        u'kyouto',
        u'nara',
        u'shimane',
        u'kanagawa',
        u'fukushima',
    ]

    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load_yaml(flat_terms_yaml)
        ns = termloader.ns
        for id_label in identifiers:
            assert id_label in ns
            assert isinstance(getattr(ns, id_label), rdflib.BNode)

    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load_yaml(structured_terms_yaml)
        ns = termloader.ns
        for id_label in identifiers:
            assert id_label in ns
            assert isinstance(getattr(ns, id_label), rdflib.BNode)

    # properties
    props_yaml = u"""\
options:
    as_property: yes
terms:
    - isinstance
    - issubclass
    - hasattr\
"""

    identifiers = [
        u'isinstance', u'issubclass', u'hasattr',
    ]

    with new_rdflib_termloader(romanize=True) as termloader:
        termloader.load_yaml(props_yaml)
        ns = termloader.ns
        tripes = list(termloader.graph.triples((None, None, None)))
        for id_label in identifiers:
            assert id_label in ns
            assert isinstance(getattr(ns, id_label), rdflib.BNode)
            assert (getattr(ns, id_label), rdflib.RDF.type, rdflib.RDF.Property)


class MockRDFLibNamespace(object):

    def __init__(self, names):
        self.namespace = self.create_ns(names)

    @property
    def ns(self):
        return self.namespace

    def create_ns(self, names):
        import rdflib
        class NS:
            pass
        ns = NS()
        for name in names:
            setattr(ns, name, rdflib.BNode())
        return ns


@relationloader_unit.test
def load_relations_from_data():
    """Load node relations directly from structured data."""

    import rdflib

    nodeprovider = MockRDFLibNamespace(
        [
            u'shusse_uo',
            u'wakashi', u'inada', u'warasa', u'buri',
        ]
    )
    relations = [
        (u'wakashi', u'inada'),
        (u'inada', u'warasa'),
        (u'warasa', u'buri'),
    ]

    with new_rdflib_relationloader(
        nodeprovider=nodeprovider, relation=u'shusse_uo',
        dry=True, acyclic=True,
    ) as relloader:
        relloader.load(relations)
        triples = list(relloader.graph.triples((None, None, None)))
        for relsrc, reldest in relations:
            noderel = (
                getattr(nodeprovider.ns, relsrc),
                nodeprovider.ns.shusse_uo,
                getattr(nodeprovider.ns, reldest),
            )
            assert noderel in triples

        with raises(Cyclic):
            relloader.load([(u'buri', u'wakashi')])
        with raises(RedundantRelation):
            relloader.load([(u'warasa', u'buri')])

@relationloader_unit.test
def relation_configs_from_yaml():
    """
    Parse YAML representation & generate configs. to create RelationLoader.
    """

    yaml_data = u"""\
options:
    dry: yes
    nointerlinks: no
    acyclic: no
relations:
    next_to:
        options:
            acyclic: yes
        pairs:
            南:
                - missisippi arkansas
            北西:
                - washington oregon
    far_from:
        options:
            dry: no
        pairs:
            - alabama nebraska
"""

    relation_definitions = declarative.load_relcfg(yaml_data)

    expected_next_to_cfg = {
        u'relation': u'next_to',
        u'options': {u'dry': True, u'nointerlinks': False, u'acyclic': True},
        u'pairs': [
            (u'washington', u'oregon'),
            (u'missisippi', u'arkansas'),
        ],
    }
    parsed_next_to_cgf = relation_definitions[u'next_to']
    for key in (u'relation', u'options'):
        assert parsed_next_to_cgf[key] == expected_next_to_cfg[key]
    assert (
        set(parsed_next_to_cgf[u'pairs']) ==
        set(expected_next_to_cfg[u'pairs'])
    )

    expected_far_from_cfg = {
        u'relation': u'far_from',
        u'options': {u'dry': False, u'nointerlinks': False, u'acyclic': False},
        u'pairs': [
            (u'alabama', u'nebraska'),
        ],
    }
    parsed_far_from_cgf = relation_definitions[u'far_from']
    for key in (u'relation', u'options'):
        assert parsed_far_from_cgf[key] == expected_far_from_cfg[key]
    assert (
        set(parsed_far_from_cgf[u'pairs']) ==
        set(expected_far_from_cfg[u'pairs'])
    )

@relationloader_unit.test
def load_relations_from_yaml():
    """Load node relations from YAML representation."""

    import rdflib

    terms = [
        u'next_to',
        u'tikai',
        u'missisippi', u'arkansas', u'tennessee', u'alabama',
    ]

    nodeprovider = MockRDFLibNamespace(terms)

    relations_yaml = u"""\
options:
    dry: yes
    nointerlinks: yes
    acyclic: no
relations:
    next_to:
        options:
            acyclic: yes
        pairs:
            南:
                - missisippi arkansas
                - arkansas tennessee
                - tennessee alabama
    tikai:
        pairs:
            - missisippi arkansas
            - arkansas tennessee
            - tennessee alabama
"""

    relations_next_to = [
        (u'missisippi', u'next_to', u'arkansas'),
        (u'arkansas', u'next_to', u'tennessee'),
        (u'tennessee', u'next_to', u'alabama'),
    ]
    relations_tikai = [
        (u'missisippi', u'tikai', u'arkansas'),
        (u'arkansas', u'tikai', u'tennessee'),
        (u'tennessee', u'tikai', u'alabama'),
    ]

    relloaders = declarative.load_relations(relations_yaml, nodeprovider=nodeprovider)

    relloader_next_to = relloaders[u'next_to']
    relloader_tikai = relloaders[u'tikai']

    # pairs loaded

    triples_next_to = list(relloader_next_to.graph.triples((None, None, None)))
    for relsrc, relprop, reldest in relations_next_to:
        noderel = (
            getattr(nodeprovider.ns, relsrc),
            getattr(nodeprovider.ns, relprop),
            getattr(nodeprovider.ns, reldest),
        )
        assert noderel in triples_next_to

    triples_tikai = list(relloader_tikai.graph.triples((None, None, None)))
    for relsrc, relprop, reldest in relations_tikai:
        noderel = (
            getattr(nodeprovider.ns, relsrc),
            getattr(nodeprovider.ns, relprop),
            getattr(nodeprovider.ns, reldest),
        )
        assert noderel in triples_tikai

    # rules
    with raises(Cyclic):
        relloader_next_to.load([(u'alabama', u'missisippi')])
    relloader_tikai.load([(u'alabama', u'missisippi')])
