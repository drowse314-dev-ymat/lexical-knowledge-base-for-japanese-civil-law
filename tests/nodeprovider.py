# encoding: utf-8

from attest import (
    Tests, assert_hook,
    contextmanager, raises,
)
from lkbutils import nodeprovider
from lkbutils.nodeprovider import kakasicall


nameprovider_unit = Tests()
kakasi_unit = Tests()


@contextmanager
def empty_nameprovider(romanize=False):
    try:
        yield nodeprovider.NameProvider(romanize=romanize)
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
