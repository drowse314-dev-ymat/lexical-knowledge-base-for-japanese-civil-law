# encoding: utf-8

import re
from . import kakasicall


class NameRegistrationError(ValueError):
    pass

class InvalidName(NameRegistrationError):
    pass

class NameConflict(NameRegistrationError):
    pass


re_formal_name = re.compile(u'^[^\W\d]\w+$')


class NameProvider(object):
    """
    Manages unique names & name references.
    """

    def __init__(self, romanize=False):
        """
        Manages unique names & name references.

        Options:
            * romanize: try to make valid names by
                        romanizing kana/kanji names.
        """
        self._romanize_on = romanize
        self._namestore = {}
        self._namestore_attr_proxy = DictAccessor(self._namestore)

    @property
    def ns(self):
        """Namespace for registered names."""
        return self._namestore_attr_proxy

    def add(self, name):
        """
        Register a name without conflicts.

        Some preprocessing is done before assignment:
            * Snake case for spaces
            * Lower
            * Character validation
        """
        valid_name = self._valid_name_from(name)
        self._add_to_store(valid_name, name)
        return valid_name

    def _valid_name_from(self, name):
        name = self._preprocess_name(name)
        if not self._is_valid_name(name):
            raise InvalidName(u'name not acceptable: "{}"'.format(name))
        return name

    def _preprocess_name(self, name):
        if self._romanize_on:
            name = try_romanize(name)
        name = self._handle_spacing_chars(name)
        name = name.lower()
        return name

    def _handle_spacing_chars(self, name):
        return u'_'.join(name.split())

    def _is_valid_name(self, name):
        return bool(re_formal_name.match(name))

    def _add_to_store(self, name, orig_name):
        namestore = self._namestore
        if name in namestore:
            raise NameConflict(u'name already exists: "{}"'.format(name))
        namestore[name] = orig_name


def try_romanize(name):
    return kakasicall.romanize(name)


class DictAccessor(object):
    """Expands a dict for attribute-style access."""

    def __init__(self, d):
        self._dict = d

    def __getattr__(self, name):
        try:
            res = self._dict[name]
        except KeyError:
            res = object.__getattribute__(self, name)
        return res

    def __contains__(self, key):
        return dict.__contains__(self._dict, key)
