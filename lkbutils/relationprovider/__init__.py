# encoding: utf-8

import collections


class RedundantRelation(ValueError):
    pass

class InterLink(ValueError):
    pass

class Cyclic(ValueError):
    def __init__(self, path, relation=u'?'):
        self.msg = u'cyclic path found on "{}": {}'.format(
            relation,
            u' -> '.join(path),
        )
    def __str__(self):
        return self.msg


class RelationChecker(object):
    """
    Help create a graph of a single relation under a set of rules.
    """

    def __init__(self, relation=None,
                 dry=False, nointerlinks=False, acyclic=False):
        """
        Help create a graph of a single relation under a set of rules.

        Options:
            * relation: used for RelationChecker.relation property.
            * dry: do not duplicate same links.
            * noninterlinks: do not create interlinks.
            * acyclic: do not create cycle.
        """
        self._relation = relation
        self._links = collections.defaultdict(list)

        self._dry = dry
        self._nointerlinks = nointerlinks
        self._acyclic = acyclic

    @property
    def relation(self):
        """Topic relation."""
        return self._relation

    def add(self, src, dest):
        """Add a link from src to dest."""
        if self._dry:
            self._check_dry(src, dest)
        if self._nointerlinks:
            self._check_nointerlinks(src, dest)
        if self._acyclic:
            self._check_acyclic(src, dest)

        self._links[src].append(dest)
        return (src, dest)

    def _check_dry(self, src, dest):
        if dest in self._links[src]:
            raise RedundantRelation(
                u'link exists: {} -> {}'.format(src, dest)
            )

    def _check_nointerlinks(self, src, dest):
        if src in self._links[dest]:
            raise InterLink(
                u'inverse link found against {} -> {}'.format(src, dest)
            )

    def _check_acyclic(self, src, dest):
        links = self._links.copy()
        links[src].append(dest)

        def visit(node):
            ancestors.append(node)

            for linked_node in links[node]:
                if linked_node in ancestors:
                    raise Cyclic(
                        ancestors + [linked_node],
                        relation=self.relation,
                    )
                if linked_node not in visited:
                    visit(linked_node)

            ancestors.remove(node)
            visited.add(node)

        ancestors = []
        visited = set()

        for node in links.keys():
            if node not in visited:
                visit(node)
