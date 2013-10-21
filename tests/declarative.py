# encoding: utf-8

from attest import (
    Tests, assert_hook,
    contextmanager,
)
from lkbutils import declarative


termloader_unit = Tests()


@contextmanager
def new_rdflib_termloader(**options):
    try:
        yield declarative.RDFLibTermLoader(**options)
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
