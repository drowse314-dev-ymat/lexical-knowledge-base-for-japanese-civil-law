# encoding: utf-8

import collections
from lkbutils import nodemodel


class RedundantRelation(ValueError):
    pass

class InterLink(ValueError):
    pass

class Cyclic(ValueError):

    def __init__(self, path, relation=u'?', encoding='utf-8'):
        self.path = path
        self.relation = relation
        self.custom_msg = self.mkmsg(path, relation)
        super(Cyclic, self).__init__(self.custom_msg.encode(encoding))

    def mkmsg(self, path, relation):
        return u'cyclic path found on "{}": {}'.format(
            relation,
            u' -> '.join(path),
        )


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


class RelationProvider(object):
    """
    Manages a consistent relation graph.
    """

    def __init__(self, relation=None,
                 dry=False, nointerlinks=False, acyclic=False):
        """
        Manages a consistent relation graph.

        Options:
            relation: object used for linking nodes in the
                      underlying graph model.
            dry, nointerlinks, acyclic:
                options for connection rules / see RelationChecker.
        """
        self._relation = relation
        self._graph = self.create_graph()

        self._relation_checker = RelationChecker(
            relation=relation,
            dry=dry, nointerlinks=nointerlinks, acyclic=acyclic,
        )

    @property
    def graph(self):
        """Entire nodes graph."""
        return self._graph

    def create_graph(self):
        """Create an empty node graph."""
        return self.depending_library.create_graph()

    def add(self, src, dest, src_id=None, dest_id=None):
        """
        Add a link from src to dest.

        Options:
            src_id/dest_id: Used for identifying src/dest nodes,
                            internally for RelationProvider._relation_checker.
                            For efficiency & error trace message.
        """
        self._check_link(src, dest, src_id=src_id, dest_id=dest_id)
        self.link(src, dest)
        return (src, dest)

    def _check_link(self, src, dest, src_id=None, dest_id=None):
        """Check link validity against the rules."""
        if src_id is not None:
            src = src_id
        if dest_id is not None:
            dest = dest_id
        self._relation_checker.add(src, dest)

    def link(self, src, dest):
        """Create a link with RelationProvider.relation."""
        self.depending_library.link(self.graph, src, self._relation, dest)


class RDFLibRelationProvider(RelationProvider):
    """RelationProvider subclass using rdflib models."""
    depending_library = nodemodel.RDFLib()
