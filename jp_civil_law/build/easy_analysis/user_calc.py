# encoding: utf-8

import sys
import math
import itertools
import argparse
import networkx as nx
import logbook
from . import casedata as data
from . import casemaker
from . import similarity as sim
from . import pagerank as pr
from . import termexpand as tex
from . import syntaxscore as stx


def termmap(all_terms, logscale=False):
    def _map(termset, label=None):
        return casemaker.as_dist_map(
            termset, all_terms, fill=1.0,
            logscale=logscale,
        ), termset
    return _map

def fn_idfweight(nx_graph, allterms, interpole=True, preinterpole=False, sqrt=False):
    if preinterpole:
        idfs = casemaker.idfmap_with_interpolation(nx_graph)
    else:
        idfs = data.idfmap()
    cache = {}
    def _map(termset, label=None):
        if label in cache:
            return cache[label], termset
        wtmap = dict.fromkeys(allterms, 0.0)
        for key in wtmap:
            if key in idfs:
                idfval = idfs[key]
                if sqrt:
                    idfval = math.sqrt(idfval)
                wtmap[key] = idfval
            elif interpole:
                nei_scores = [
                    idfs[node] for node
                    in nx.all_neighbors(nx_graph, key)
                    if node in idfs
                ]
                if sqrt:
                    nei_scores = [math.sqrt(v) for v in nei_scores]
                if nei_scores:
                    wtmap[key] = float(sum(nei_scores)) / float(len(nei_scores))
        cache[label] = wtmap
        return wtmap, termset
    return _map

def fn_centrality(nx_graph, preproc=lambda x: x, method=nx.betweenness_centrality):
    graph_copy = nx_graph.copy()
    graph_copy = preproc(graph_copy)
    def _distribution(featured_nodes, label=None):
        return method(graph_copy), featured_nodes
    return _distribution

def fn_multiply(mapper_a, mapper_b):
    def _map(termset, label=None):
        map_a, modterms_a = mapper_a(termset, label=label)
        map_b, modterms_b = mapper_b(modterms_a, label=label)
        assert set(map_a.keys()) == set(map_b.keys()), \
               (u','.join(set(map_a.keys()).difference(set(map_b.keys()))) +
                u'|' +
                u','.join(set(map_b.keys()).difference(set(map_a.keys())))).encode('utf-8')
        mulmap = {}
        for key in map_a:
            mulmap[key] = map_a[key] * map_b[key]
        return mulmap, modterms_b
    return _map

def fn_inverse(mapper):
    def _map(termset, label=None):
        mapped, modterms = mapper(termset, label=label)
        invmap = {}
        for key in mapped:
            orig = mapped[key]
            if orig == 0.0:
                invmap[key] = orig
            else:
                invmap[key] = 1.0 / mapped[key]
        return invmap, modterms
    return _map

def fn_expand(nx_graph, allterms, amplify=False, lower_expands=False):
    cache = {}
    def _expand(termset, key):
        termset = tuple(sorted(set(termset)))
        if termset not in cache:
            print(u'term expanding: {}...'.format(key))
            expand, scoremap = tex.populate(
                termset, nx_graph,
                methods=tex.all_methods,
            )
            cache[termset] = expand, scoremap
        expand, scoremap = cache[termset]
        return expand, scoremap

    def _map(termset, label=None):
        expand, scoremap = _expand(termset, label)
        distmap =  casemaker.as_dist_map(
            expand, allterms, fill=1.0,
        )
        if amplify:
            for term in scoremap:
                distmap[term] *= scoremap[term]
        if lower_expands:
            for term in termset:
                distmap[term] *= 0.5
        return distmap, expand
    return _map

def fn_syntax(allterms, raw_titles, raw_sents):
    def _map(termset, label=None):
        if label.startswith(u'q'):
            subject=True
        else:
            subject=False
        stx_score = stx.syntaxscore(
            termset,
            raw_titles[label],
            raw_sents[label],
            subject=subject,
        )
        distmap =  casemaker.as_dist_map(
            termset, allterms, fill=1.0,
        )
        for term in stx_score:
            distmap[term] *= stx_score[term]
        return distmap, termset
    return _map

def labeled_weights(terms, mapped):
    score_labels = []
    for term in terms:
        score_labels.append(u'{}/{}'.format(term, mapped.get(term, 0.0)))
    return score_labels

def fn_display(mapper, raw_titles, raw_sents):
    def _map(termset, label=None):
        mapped, modterms = mapper(termset, label=label)
        score_labels = labeled_weights(modterms, mapped)
        # print(u'{}:'.format(label))
        # print(u'==================')
        # print(u'Title: {}'.format(raw_titles[label]))
        # print(u'==================')
        # print(u'Content: {}'.format(u'/'.join(raw_sents[label])))
        # print(u'==================')
        # print(u', '.join(score_labels))
        # print(u'')
        return mapped, modterms
    return _map

def fn_cutoff_right():
    def _relmap(key_a, rankmap_a, key_b, rankmap_b):
        rankmap_b = rankmap_b.copy()
        for term, weight_a in rankmap_a.iteritems():
            rankmap_b[term] *= weight_a
        return rankmap_a, rankmap_b
    return _relmap


def fn_double(mapper):
    singlecache = {}
    def _map(key, termset):
        if key not in singlecache:
            mapped, modterms = mapper(termset, label=key)
            singlecache[key] = mapped, modterms
        return singlecache[key]
    def _jmap(key_a, termset_a, key_b, termset_b):
        mapped_a, modterms_a = _map(key_a, termset_a)
        mapped_b, modterms_b = _map(key_b, termset_b)
        return mapped_a, modterms_a, mapped_b, modterms_b
    return _jmap

def fn_joint_multiply(mapper_x, mapper_y):
    def _jmap(key_a, termset_a, key_b, termset_b):
        map_xa, modterms_xa, map_xb, modterms_xb = mapper_x(key_a, termset_a, key_b, termset_b)
        map_ya, modterms_ya, map_yb, modterms_yb = mapper_y(key_a, modterms_xa, key_b, modterms_xb)
        assert set(map_xa.keys()) == set(map_ya.keys()), u','.join(set(map_xa.keys()).symmetric_difference(set(map_ya.keys()))).encode('utf-8')
        assert set(map_xb.keys()) == set(map_yb.keys())
        mulmap_a = {}
        mulmap_b = {}
        for key in map_xa:
            mulmap_a[key] = map_xa[key] * map_ya[key]
        for key in map_xb:
            mulmap_b[key] = map_xb[key] * map_yb[key]
        return mulmap_a, modterms_yb, mulmap_b, modterms_yb
    return _jmap

def fn_joint_cutoff_art(jmapper, by_multiplication=True, reverse=False, termsets=None):
    answermap = data.answermap

    def _filter(map_filtered, terms_filtered, map_base, terms_base):
        map_filtered = map_filtered.copy()
        terms_filtered = list(terms_filtered[:])
        if by_multiplication:
            for term, weight_base in map_base.iteritems():
                map_filtered[term] *= weight_base
        else:
            for term in map_filtered.keys():
                if map_base[term] == 0.0:
                    map_filtered[term] = 0.0
            terms_filtered = [t for t in terms_filtered if t in terms_base]
        return map_filtered, tuple(terms_filtered)

    def _jmap(key_a, termset_a, key_b, termset_b):
        map_a, modterms_a, map_b, modterms_b = jmapper(key_a, termset_a, key_b, termset_b)
        a_is_art = not key_a.startswith(u'q')
        b_is_art = not key_b.startswith(u'q')
        if reverse:
            a_is_art = not a_is_art
            b_is_art = not b_is_art
        if a_is_art and not b_is_art:
            map_a, modterms_a = _filter(map_a, modterms_a, map_b, modterms_b)
        elif b_is_art and not a_is_art:
            map_b, modterms_b = _filter(map_b, modterms_b, map_a, modterms_a)

        # if a_is_art and not b_is_art and key_a in answermap[key_b]:
        #     print(u'==========')
        #     print(u'{}/{} : {}/{}'.format(
        #         key_b, u','.join(termsets[key_b]),
        #         key_a, u','.join(termsets[key_a]),
        #     ))
        #     print(u'F{}: {}'.format(key_a, u','.join(labeled_weights(modterms_a, map_a))))
        #     print(u'F{}: {}'.format(key_b, u','.join(labeled_weights(modterms_b, map_b))))
        #     print(u'==========')
        # elif not a_is_art and b_is_art and key_b in answermap[key_a]:
        #     print(u'==========')
        #     print(u'{}/{} : {}/{}'.format(
        #         key_a, u','.join(termsets[key_a]),
        #         key_b, u','.join(termsets[key_b]),
        #     ))
        #     print(u'F{}: {}'.format(key_a, u','.join(labeled_weights(modterms_a, map_a))))
        #     print(u'F{}: {}'.format(key_b, u','.join(labeled_weights(modterms_b, map_b))))
        #     print(u'==========')


        return map_a, modterms_a, map_b, modterms_b
    return _jmap

def fn_joint_idfonly(allterms, single_idfmapper, idfonly='a'):
    if idfonly not in ('q', 'a', 'qa'):
        raise ValueError('pick from {q, a, qa}')
    idf_to_a = 'a' in idfonly
    idf_to_q = 'q' in idfonly
    def _jmap(key_a, termset_a, key_b, termset_b):
        a_is_art = not key_a.startswith(u'q')
        b_is_art = not key_b.startswith(u'q')
        map_to_a = (a_is_art and idf_to_a) or (not a_is_art and idf_to_q)
        map_to_b = (b_is_art and idf_to_a) or (not b_is_art and idf_to_a)

        map_a = dict.fromkeys(allterms, 0.0)
        map_a.update(dict.fromkeys(termset_a, 1.0))
        if map_to_a:
            comp_map_a, termset_a = single_idfmapper(termset_a, label=key_a)
            map_a.update(comp_map_a)

        map_b = dict.fromkeys(allterms, 0.0)
        map_b.update(dict.fromkeys(termset_b, 1.0))
        if map_to_b:
            comp_map_b, termset_b = single_idfmapper(termset_b, label=key_b)
            map_b.update(comp_map_b)

        return map_a, termset_a, map_b, termset_b
    return _jmap

def linkrater(nx_graph, allterms):
    _graph = nx_graph.to_undirected()
    cache = {}
    def _neighbours(term):
        if term not in cache:
            if term not in _graph:
                linked = tuple()
            else:
                linked = nx.all_neighbors(_graph, term)
            cache[term] = linked
        return cache[term]

    def _factor(base_terms, checked_terms, expanded):
        base_set = set(base_terms)
        checked_set = set(checked_terms)
        targets = base_set.intersection(checked_set)
        targets = targets.intersection(expanded)
        factor = {}
        for term in targets:
            neis = set(_neighbours(term))
            neis_in_base = base_set.intersection(neis)
            neis_in_checked = checked_set.intersection(neis)
            if not neis_in_checked:
                if not neis_in_base:
                    factor[term] = 1.0
                else:
                    factor[term] = 0.0
                continue
            overlap = neis_in_base.intersection(neis_in_checked)
            factor[term] = float(len(overlap)) / float(len(neis_in_checked))
            assert factor[term] <= 1.0
        return factor

    allone = dict.fromkeys(allterms, 1.0)

    def factor_maker(base_terms, checked_terms, expanded):
        if not expanded:
            return allone.copy()
        factor = _factor(base_terms, checked_terms, expanded)
        mapped = allone.copy()
        mapped.update(factor)
        return mapped

    return factor_maker

def fn_joint_bridgehierarchy(nx_graph, allterms, bridge='q', expandother=False):
    answermap = data.answermap

    if bridge not in ('q', 'a', 'qa'):
        raise ValueError('pick from {q, a, qa}')
    bridge_from_art = 'a' in bridge
    bridge_from_q = 'q' in bridge

    hierarchy_graph = nx_graph.copy()
    if not expandother:
        for src, dest, edgedata in nx_graph.edges(data=True):
            if edgedata['label'] not in (u'hyper', u'hyperx'):
                hierarchy_graph.remove_edge(src, dest)
    cache = {}
    def _bridge(fromterms, toterms):
        fromterms = list(fromterms)
        ordered_fromterms = list(sorted(set(fromterms)))
        toterms = list(sorted(set(toterms).difference(fromterms)))
        from_as_tuple, to_as_tuple = tuple(ordered_fromterms), tuple(toterms)
        if (from_as_tuple, to_as_tuple) in cache:
            appends = list(cache[(from_as_tuple, to_as_tuple)])
        else:
            appends = []
            for fromterm in ordered_fromterms:
                for toterm in toterms:
                    if fromterm not in hierarchy_graph or toterm not in hierarchy_graph:
                        continue
                    if nx.has_path(hierarchy_graph, fromterm, toterm):
                        appends.append(toterm)
            cache[(from_as_tuple, to_as_tuple)] = tuple(appends)
        fromterms.extend(appends)
        return tuple(fromterms)

    def _jmap(key_a, termset_a, key_b, termset_b):
        a_is_q = key_a.startswith(u'q')
        b_is_q = key_b.startswith(u'q')
        bridge_from_a = (a_is_q and bridge_from_q) or (not a_is_q and bridge_from_art)
        bridge_from_b = (b_is_q and bridge_from_q) or (not b_is_q and bridge_from_art)

        map_a = dict.fromkeys(allterms, 0.0)
        if bridge_from_a:
            expand_terms_a = _bridge(termset_a, termset_b)
        map_a.update(dict.fromkeys(expand_terms_a, 1.0))

        map_b = dict.fromkeys(allterms, 0.0)
        if bridge_from_b:
            expand_terms_b = _bridge(termset_b, termset_a)
        map_b.update(dict.fromkeys(expand_terms_b, 1.0))

        if bridge_from_a or bridge_from_b:
            if a_is_q and key_b in answermap[key_a]:
                print(u'q-{} & a-{}'.format(key_a, key_b))
                print(u'====================')
                print(u','.join(termset_a) + u'+->' + u','.join(set(expand_terms_a).difference(set(termset_a))))
                print(u'====================')
                print(u','.join(termset_b) + u'+->' + u','.join(set(expand_terms_b).difference(set(termset_b))))
                print(u'')
            elif b_is_q and key_a in answermap[key_b]:
                print(u'q-{} & a-{}'.format(key_b, key_a))
                print(u'====================')
                print(u','.join(termset_a) + u'+->' + u','.join(set(expand_terms_a).difference(set(termset_a))))
                print(u'====================')
                print(u','.join(termset_b) + u'+->' + u','.join(set(expand_terms_b).difference(set(termset_b))))
                print(u'')
                print(u'')
            else:
                pass

        if bridge_from_a:
            termset_a = expand_terms_a
        if bridge_from_b:
            termset_b = expand_terms_b

        return map_a, termset_a, map_b, termset_b
    return _jmap

def fn_joint_hierarchyreduce(nx_graph, allterms, termsets):
    answermap = data.answermap

    hierarchy_graph = nx_graph.copy()
    for src, dest, edgedata in nx_graph.edges(data=True):
        if edgedata['label'] not in (u'hyper', u'hyperx'):#, u'antecedent_to'):
            hierarchy_graph.remove_edge(src, dest)
    cache = {}
    def _upper(hyper, hypo):
        key = (hyper, hypo)
        if key not in cache:
            cache[key] = nx.has_path(hierarchy_graph, hypo, hyper)
        return cache[key]

    def _hierarchy_reduce(termset, excepts=tuple()):
        reduced_terms = list(termset)
        reduced = False
        for hyper, hypo in itertools.permutations(termset, 2):
            if hyper in excepts:
                continue
            if hyper == hypo:
                continue
            if hyper not in hierarchy_graph or hypo not in hierarchy_graph:
                continue
            if _upper(hyper, hypo) and hyper in reduced_terms:
                reduced_terms.remove(hyper)
                reduced_terms.append(hypo)
                reduced = True
        return tuple(reduced_terms), reduced

    def _jmap(key_a, termset_a, key_b, termset_b):
        mod_termset_a, a_is_reduced = _hierarchy_reduce(termset_a, excepts=list(termsets[key_a])+list(termsets[key_b]))
        mod_termset_b, b_is_reduced = _hierarchy_reduce(termset_b, excepts=list(termsets[key_b])+list(termsets[key_b]))
        # if key_a.startswith(u'q'):
        #     if key_b in answermap[key_a]:
        #         print(u'from {}: {}'.format(key_a, u','.join(termset_a)))
        #         print(u'from {}: {}'.format(key_b, u','.join(termset_b)))
        #         print(u'reduced: {}'.format(u','.join(mod_termset_a)))
        #         print(u'reduced: {}'.format(u','.join(mod_termset_b)))
        # if key_b.startswith(u'q'):
        #     if key_a in answermap[key_b]:
        #         print(u'from {}: {}'.format(key_a, u','.join(termset_a)))
        #         print(u'from {}: {}'.format(key_b, u','.join(termset_b)))
        #         print(u'reduced: {}'.format(u','.join(mod_termset_a)))
        #         print(u'reduced: {}'.format(u','.join(mod_termset_b)))

        map_a = dict.fromkeys(allterms, 0.0)
        map_a.update(dict.fromkeys(mod_termset_a, 1.0))
        map_b = dict.fromkeys(allterms, 0.0)
        map_b.update(dict.fromkeys(mod_termset_b, 1.0))

        return map_a, mod_termset_a, map_b, mod_termset_b
    return _jmap

def fn_joint_expandonly(nx_graph, allterms, single_expander, expand='q', with_cutoff_art=False,
                        ratelinks=False):
    answermap = data.answermap
    idfmap = casemaker.idfmap_with_interpolation(nx_graph)
    _linkrater = linkrater(nx_graph, allterms)

    if expand not in ('q', 'a', 'qa'):
        raise ValueError('pick from {q, a, qa}')
    expand_art = 'a' in expand
    expand_q = 'q' in expand

    def _jmap(key_a, termset_a, key_b, termset_b):
        a_is_q = key_a.startswith(u'q')
        b_is_q = key_b.startswith(u'q')
        expand_a = (a_is_q and expand_q) or (not a_is_q and expand_art)
        expand_b = (b_is_q and expand_q) or (not b_is_q and expand_art)

        map_a = dict.fromkeys(allterms, 0.0)
        map_a.update(dict.fromkeys(termset_a, 1.0))
        if expand_a:
            comp_map_a, expand_terms_a = single_expander(termset_a, label=key_a)
            map_a.update(comp_map_a)

        map_b = dict.fromkeys(allterms, 0.0)
        map_b.update(dict.fromkeys(termset_b, 1.0))
        if expand_b:
            comp_map_b, expand_terms_b = single_expander(termset_b, label=key_b)
            map_b.update(comp_map_b)

        if with_cutoff_art and expand_a and expand_b and a_is_q != b_is_q:
            # print(u'cut {} & {}'.format(key_a, key_b))
            both_contained = set(expand_terms_a).intersection(set(expand_terms_b))
            seed_a = set(termset_a).union(both_contained)
            seed_b = set(termset_b).union(both_contained)
            expand_terms_a = tuple([t for t in expand_terms_a if t in seed_a])
            expand_terms_b = tuple([t for t in expand_terms_b if t in seed_b])
            for term in map_a.keys():
                if term not in seed_a:
                    map_a[term] = 0.0
            for term in map_b.keys():
                if term not in seed_b:
                    map_b[term] = 0.0

        if ratelinks:
            for_a = _linkrater(
                expand_terms_b, expand_terms_a,
                # set(expand_terms_a).difference(set(termset_a))
                expand_terms_b,
            )
            for t in map_a:
                if t in for_a:
                    map_a[t] *= for_a[t]
            for_b = _linkrater(
                expand_terms_a, expand_terms_b,
                # set(expand_terms_b).difference(set(termset_b))
                expand_terms_a,
            )
            for t in map_b:
                if t in for_b:
                    map_b[t] *= for_b[t]

        if expand_a:
            termset_a = expand_terms_a
        if expand_b:
            termset_b = expand_terms_b

        # if a_is_q and not b_is_q and key_b in answermap[key_a]:
        #     print(u'ans!: {}:{}'.format(key_a, key_b))
        #     print(u'q-{}:'.format(key_a))
        #     print(u'====================')
        #     print(u', '.join(labeled_weights(termset_a, data.idfmap())))
        #     print(u'a-{}:'.format(key_b))
        #     print(u'====================')
        #     print(u', '.join(labeled_weights(termset_b, data.idfmap())))
        #     print(u'')
        # if b_is_q and not a_is_q and key_a in answermap[key_b]:
        #     print(u'ans!: {}:{}'.format(key_b, key_a))
        #     print(u'q-{}:'.format(key_b))
        #     print(u'====================')
        #     print(u', '.join(labeled_weights(termset_b, data.idfmap())))
        #     print(u'a-{}:'.format(key_a))
        #     print(u'====================')
        #     print(u', '.join(labeled_weights(termset_a, data.idfmap())))
        #     print(u'')

        return map_a, termset_a, map_b, termset_b
    return _jmap

def fn_joint_termpipe(mapper_x, mapper_y):
    def _jmap(key_a, termset_a, key_b, termset_b):
        xmap_a, mod_termset_a, xmap_b, mod_termset_b = mapper_x(key_a, termset_a, key_b, termset_b)
        ymap_a, mod_mod_termset_a, ymap_b, mod_mod_termset_b = mapper_y(key_a, mod_termset_a, key_b, mod_termset_b)
        xmap_a.update(ymap_a)
        xmap_b.update(ymap_b)
        return xmap_a, mod_mod_termset_a, xmap_b, mod_mod_termset_b
    return _jmap

def fn_joint_passpipe():
    def _jmap(key_a, termset_a, key_b, termset_b):
        return {}, termset_a, {}, termset_b
    return _jmap


def create_mapper(nx_graph=None, allterms=None, raw_titles=None, raw_sents=None):
    # mapper selection
    mapper_term = termmap(allterms)
    mapper_idf = fn_idfweight(nx_graph, allterms, interpole=False)
    mapper_pr = pr.pr_distribution_fn(
        nx_graph,
        preproc=lambda n: n.to_undirected(),
        amplify=10.0,
    )
    mapper_centr = fn_centrality(
        nx_graph,
        preproc=lambda n: n.to_undirected(),
        method=nx.betweenness_centrality,
    )
    mapper_expander = fn_expand(nx_graph, amplify=False, lower_expands=False)

    mapper_syntax = fn_syntax(allterms, raw_titles, raw_sents)

    mapper = fn_multiply(mapper_term, mapper_idf)

    mapper = fn_display(mapper, raw_titles, raw_sents)


    relmapper_cutoff = fn_cutoff_right()

    relmapper = relmapper_cutoff

    return mapper, relmapper


def create_joint_mapper(nx_graph=None, allterms=None, raw_titles=None, raw_sents=None, termsets=None):
    # mapper selection

    mapper_term = termmap(allterms, logscale=False)
    mapper_idf = fn_idfweight(nx_graph, allterms, interpole=False, preinterpole=True, sqrt=False)
    mapper_syntax = fn_syntax(allterms, raw_titles, raw_sents)
    mapper_expander = fn_expand(nx_graph, allterms, amplify=False, lower_expands=False)

    mapper_joint_bridgehierarchy = fn_joint_bridgehierarchy(
        nx_graph, allterms, bridge='qa',
        expandother=False,
    )
    mapper_joint_hierarchyreduce = fn_joint_hierarchyreduce(
        nx_graph, allterms, termsets,
    )
    mapper_joint_expandonly = fn_joint_expandonly(
        nx_graph, allterms, mapper_expander, expand='qa', with_cutoff_art=True,
        ratelinks=False,
    )
    mapper_joint_idfonly = fn_joint_idfonly(allterms, mapper_idf, idfonly='qa')
    mapper_joint_passpipe = fn_joint_passpipe()

    mapper_single = mapper_term
    mapper_single_display = fn_display(mapper_single, raw_titles, raw_sents)

    mapper_double = fn_double(mapper_single_display)
    # mapper_double = fn_joint_termpipe(mapper_joint_bridgehierarchy, mapper_joint_expandonly)
    # mapper_double = fn_joint_termpipe(mapper_joint_expandonly, mapper_joint_bridgehierarchy)
    # mapper_double = fn_joint_termpipe(mapper_joint_expandonly, mapper_joint_passpipe)
    # mapper_double = fn_joint_termpipe(mapper_double, mapper_joint_bridgehierarchy)
    mapper_double = fn_joint_termpipe(mapper_joint_expandonly, mapper_joint_hierarchyreduce)
    # mapper_double = mapper_joint_expandonly

    mapper_double = fn_joint_multiply(mapper_double, mapper_joint_idfonly)

    mapper_double = fn_joint_cutoff_art(mapper_double, by_multiplication=False, termsets=termsets)

    mapper = mapper_double

    return mapper

def print_similarity(nx_graph):
    term_sets = data.allart_term_sets
    term_sets.update(data.allq_term_sets)

    mapper = create_mapper(nx_graph=nx_graph)
    sim.print_dist_similarities(
        nx_graph.nodes(), term_sets,
        distribution_fn=mapper,
        grep=u'q18/15/',
    )

def batch_similarity(nx_graph, noorder=True):
    term_sets = data.all_mixedterm_sets
    allterms = data.mixed_allterms

    raw_titles = data.all_raw_titles
    raw_sents = data.all_raw_sents
    F_threshold = 3.0

    answers = data.answermap
    mapper = create_joint_mapper(
        nx_graph=nx_graph, allterms=allterms,
        raw_titles=raw_titles, raw_sents=raw_sents,
        termsets=term_sets,
    )

    sims = sim.joint_dist_similarities(
        allterms, term_sets,
        distribution_fn=mapper,
    )
    rankstack = []
    logrankstack = []
    # outstandings = []
    # closer_outstandings = []
    f_vals = []
    for qkey in sorted(answers):
        qsims = [
            (sims[(k1, k2)], (k1, k2))
            for (k1, k2) in sims
            if k1 == qkey
        ]
        for val, pair in qsims[:]:
            key_a, key_b = pair
            if key_a == qkey and key_b.startswith(u'q') or \
               key_b == qkey and key_a.startswith(u'q'):
                qsims.remove((val, pair))
        qsims.sort(reverse=True)
        order = [(ks, score) for score, ks in qsims]

        print(u'For {}'.format(qkey))
        print(u'==============')
        print(u'ans: {}'.format(u','.join(answers[qkey])))
        print(u'seen:')
        for pair, score in order[:10]:
            print(u'  {} <--> {} ({})'.format(*(list(pair) + [round(score, 4)])))
        rank_, logrank = keymap_avr_rank(order, answers[qkey], qkey, noorder=noorder)
        # outstanding_, closer_outst = outstanding_rate(qsims, answers[qkey], qkey)
        f_ = f_measure(F_threshold, order, answers[qkey], qkey)
        rankstack.append(rank_)
        logrankstack.append(logrank)
        # if outstanding_ != 0.0:
        #     outstandings.append(outstanding_)
        #     closer_outstandings.append(closer_outst)
        f_vals.append(f_)
        print(u'RANK: {}'.format(rank_))
        print(u'LOG(RANK): {}'.format(logrank))
        # print(u'INV OUTSTANDING RATE(AVR): {}'.format(outstanding_))
        # print(u'INV OUTSTANDING RATE(AVR/NEAREST): {}'.format(closer_outst))
        print(u'F: {}'.format(f_))
        print(u'==============\n')

    average = sum(rankstack) / float(len(rankstack))
    print(u'AVR RANK: {}'.format(average))

    sq_errs = []
    for rank_ in rankstack:
        sq_errs.append(pow(average - rank_, 2.0))
    variant = sum(sq_errs) / float(len(sq_errs))
    sd = math.sqrt(variant)
    print(u'SD: {}'.format(sd))

    average_logrank = sum(logrankstack) / float(len(logrankstack))
    print(u'AVR LOG(RANK): {}'.format(average_logrank))

    logrank_sq_errs = []
    for rank_ in logrankstack:
        logrank_sq_errs.append(pow(average_logrank - rank_, 2.0))
    variant = sum(logrank_sq_errs) / float(len(logrank_sq_errs))
    sd = math.sqrt(variant)
    print(u'SD LOGRANK: {}'.format(sd))

    # avr_outstanding = sum(outstandings) / float(len(outstandings))
    # avr_closest_outstanding = sum(closer_outstandings) / float(len(closer_outstandings))
    # print(u'OUTSTANDING RATE(GLOBAL AVR): {}'.format(1.0 / avr_outstanding))
    # print(u'OUTSTANDING RATE(GLOBAL AVR/NEAREST): {}'.format(1.0 / avr_closest_outstanding))
    # outst_sq_errs = []
    # for outst_ in outstandings:
    #     outst_sq_errs.append(pow(avr_outstanding - outst_, 2.0))
    # outst_variant = sum(outst_sq_errs) / float(len(outst_sq_errs))
    # outst_sd = math.sqrt(outst_variant)
    # cls_outst_sq_errs = []
    # for outst_ in closer_outstandings:
    #     cls_outst_sq_errs.append(pow(avr_closest_outstanding - outst_, 2.0))
    # cls_outst_variant = sum(cls_outst_sq_errs) / float(len(cls_outst_sq_errs))
    # cls_outst_sd = math.sqrt(cls_outst_variant)
    # print(u'SD INVOUTST RATE: {}'.format(outst_sd))
    # print(u'SD INVOUTST RATE/NEAREST: {}'.format(cls_outst_sd))

    f_avr = sum(f_vals) / float(len(f_vals))
    print(u'AVR-F: {}'.format(f_avr))

def keypair_MAP(order, correct_order, qkey, noorder=True):
    rankstack = keymap_ranks(order, correct_order, qkey, noorder=noorder)
    ratiostack = []
    for correct_rank, rank in enumerate(rankstack, start=1):
        map_ = float(correct_rank) / float(rank)
        ratiostack.append(map_)
    return sum(ratiostack) / float(len(ratiostack))

def keymap_avr_rank(order, correct_order, qkey, noorder=True):
    rankstack = keymap_ranks(order, correct_order, qkey, noorder=noorder)
    ratiostack = []
    for correct_rank, rank in enumerate(rankstack, start=1):
        rank_ = float(rank) / float(correct_rank)
        ratiostack.append(rank_)
    rank = sum(ratiostack) / float(len(ratiostack))
    logrank = sum(2.0 * math.log(r) for r in ratiostack) / float(len(ratiostack))
    return rank, logrank

def f_measure(F_threshold, order, correct_order, qkey):
    num_answers = len(correct_order)
    rankstack = keymap_ranks(order, correct_order, qkey)
    num_recall = 0
    for rank_ in rankstack:
        if rank_ <= F_threshold:
            num_recall += 1
    f = float(num_recall) / (0.5 * (F_threshold + float(num_answers)))
    return f

def keymap_ranks(order, correct_order, qkey, noorder=True):
    rankstack = []
    for artkey in correct_order:
        rank = 1
        prev_score = order[0][1]
        for keypair, score in order:
            if score < prev_score:  # it's descending!
                rank += 1
            prev_score = score
            if artkey in keypair:
                break
        else:
            raise ValueError('?')
        same_ranked = len([
            score for ks, score in order
            if score == prev_score
        ]) - 1  # subtract self
        rank += (float(same_ranked) / 2.0)
        rankstack.append(rank)
    if noorder:
        rankstack.sort()
    return rankstack

def keymap_ranks(order, correct_order, qkey, noorder=True):
    rankstack = []
    for artkey in correct_order:
        rank = 0.0
        for score, grouped in itertools.groupby(order, lambda kp_score: kp_score[1]):
            equivs = set(sum((list(keypair) for keypair, score in grouped), []))
            equivs.remove(qkey)
            if artkey in equivs:
                rank += (1.0 + float(len(equivs) - 1) / 2.0)
                break
            else:
                rank += float(len(equivs))
        else:
            raise ValueError('?')
        rankstack.append(rank)
    if noorder:
        rankstack.sort()
    return rankstack

def outstanding_rate(qsim_pairs, correct_order, qkey):
    simmap = {
        pair: simval
        for simval, pair in qsim_pairs
    }
    answer_sims = []
    for sim_pair in simmap.keys():
        key_a, key_b = sim_pair
        if key_a == qkey:
            artkey = key_b
        else:
            artkey = key_a
        if artkey in correct_order:
            answer_sims.append(simmap.pop(sim_pair))

    ratestack = []
    for ans_sim_value in answer_sims:
        for sim_value in simmap.values():
            try:
                ratestack.append(sim_value / ans_sim_value)
            except ZeroDivisionError:
                pass

    closest_outstrates = []
    for ans_sim_value in answer_sims:
        for sim_value in list(sorted(simmap.values(), reverse=True))[:2]:
            try:
                closest_outstrates.append(sim_value / ans_sim_value)
            except ZeroDivisionError:
                pass

    if not ratestack:
        return 0.0, 0.0
    avr_outstanding = sum(ratestack) / float(len(ratestack))
    avr_closest_outstanding = sum(closest_outstrates) / float(len(closest_outstrates))
    return avr_outstanding, avr_closest_outstanding


def check_expansion(nx_graph):
    term_sets = data.q18_15_1_term_sets
    term_set_adds = data.q18_15_1_term_set_adds
    term_set_expanded = {}
    expander = fn_expand(nx_graph)
    for key in sorted(term_sets):
        origin = term_sets[key]
        distmap, expanded = expander(origin)
        term_set_expanded[key] = expanded
        added = term_set_adds[key]
        both = set(expanded).intersection(set(added))
        missed = set(added).difference(both)
        unexpected = set(expanded).difference(both)
        expanded_gain = set(expanded).difference(set(origin))
        added_gain = set(added).difference(set(origin))
        both_gain = expanded_gain.intersection(added_gain)
        if not expanded_gain:
            if both_gain:
                precision = 0.0
            else:
                precision = 1.0
        else:
            precision = float(len(both_gain)) / float(len(expanded_gain))
        if not added_gain:
            recall = 1.0
        else:
            recall = float(len(both_gain)) / float(len(added_gain))
        if precision + recall == 0.0:
            fmsr = 0.0
        else:
            fmsr = (2.0 * precision * recall) / (precision + recall)
        precision_like = float(len(both)) / float(len(expanded))
        recall_like = float(len(both)) / float(len(added))
        if precision_like + recall_like == 0.0:
            fmsr_like = 0.0
        else:
            fmsr_like = (2.0 * precision_like * recall_like) / (precision_like + recall_like)
        formatter = (
            u'========================\n'
            u'{key}:\n'
            u'========================\n'
            u'    origin: [{origin}]({origsize})\n'
            u'    expanded: [{expanded}]({exsize})\n'
            u'    added: [{added}]({addedsize})\n'
            u'    intersection: [{both}]\n'
            u'    missed: [{missed}]\n'
            u'    unexpected: [{unexpected}]\n'
            u'    / precision(whole): {precision_like}\n'
            u'    / recall(whole): {recall_like}\n'
            u'    / f-msr(whole): {fmsr_like}\n'
            u'    / precision?: {precision}\n'
            u'    / recall?: {recall}\n'
            u'    / f-msr?: {fmsr}\n'
            u'========================'
        )
        joiner = lambda tset: u','.join(sorted(tset))
        print(formatter.format(
            key=key,
            origin=joiner(origin), origsize=len(origin),
            expanded=joiner(expanded), added=joiner(added), both=joiner(both),
            exsize=len(expanded), addedsize=len(added),
            missed=joiner(missed), unexpected=joiner(unexpected),
            precision_like=precision_like, recall_like=recall_like,
            fmsr_like=fmsr_like,
            precision=precision, recall=recall,
            fmsr=fmsr,
        ))
    print(
            u'average term size --\n'
            u'  added: {}\n'
            u'  expanded: {}'.format(
                float(sum(len(ts) for ts in term_set_adds.values())) / float(len(term_set_adds)),
                float(sum(len(ts) for ts in term_set_expanded.values())) / float(len(term_set_expanded)),
        )
    )
    assert term_set_adds != term_set_expanded


def run(nx_graph):
    copy_graph = nx_graph.copy()
    # for src, dest, edgedata in nx_graph.edges(data=True):
    #     if edgedata['label'] in (u'antecedent_to',):
    #         copy_graph.remove_edge(src, dest)
    # print(len(copy_graph.edges()))
    batch_similarity(copy_graph, noorder=True)
