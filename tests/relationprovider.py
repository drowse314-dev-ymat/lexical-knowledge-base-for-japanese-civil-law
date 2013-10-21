# encoding: utf-8

from attest import (
    Tests, assert_hook,
    contextmanager, raises,
)
from lkbutils import relationprovider


relationchecker_unit = Tests()


@contextmanager
def empty_relationchecker(**options):
    try:
        yield relationprovider.RelationChecker(**options)
    finally:
        pass


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
