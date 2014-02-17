# encoding: utf-8

import os
import math
import collections
import networkx as nx


def idfmap(cache={}):
    if 'cache' not in cache:
        path = os.path.abspath(
            os.path.sep.join([os.path.dirname(__file__), 'idfvals.txt'])
        )
        idftxt = open(path).read().decode('utf-8')
        idfs = {}
        for idfline in idftxt.split(u'\n'):
            if idfline != u'':
                term, idf = idfline.split(u',')
                idfs[term] = float(idf)
        cache['cache'] = idfs
    return cache['cache'].copy()

def idfmap_with_interpolation(nx_graph, cache={}):
    if 'cache' not in cache:
        idfs = idfmap()
        orig_terms = idfs.keys()
        for term in nx_graph.nodes():
            if term not in idfs:
                idfs[term] = 0.0
        updated = 0
        while True:
            pre_comp = sum(idfs.values())
            for term in idfs.keys():
                if idfs[term] != 0.0:
                    continue
                elif term not in nx_graph:
                    continue
                else:
                    nei_scores = [idfs[node] for node in nx.all_neighbors(nx_graph, term)]
                    # nei_scores = [s for s in nei_scores if s != 0.0]
                    if nei_scores:
                        idfs[term] = float(sum(nei_scores)) / float(len(nei_scores))
            updates = sum(idfs.values()) - pre_comp
            updated += 1
            if updates == 0.0:
                break
        print(u'(idfmap interpole) updated: {} times / inserted weights: {}'.format(
            unicode(updated),
            u','.join([u'{}/{}'.format(t, idfs[t]) for t in set(idfs.keys()).difference(set(orig_terms))])
        ))
        cache['cache'] = idfs
    return cache['cache'].copy()

def stopwords():
    path = os.path.abspath(
        os.path.sep.join([os.path.dirname(__file__), 'mod_stopwords.txt'])
    )
    termstxt = open(path).read().decode('utf-8')
    stops = []
    for termline in termstxt.split(u'\n'):
        terms = termline.split(u',')
        for t in terms:
            t = t.strip()
            if t != u'':
                stops.append(t)
    return stops

def matchterms(sequence, terms, stopwords, prefer_from=tuple()):
    termdict = collections.defaultdict(list)
    for t in set(terms):
        termdict[t[0]].append(t)
    for index in termdict:
        termdict[index].sort(reverse=True, key=lambda wd: len(wd))

    if prefer_from:
        for index in termdict:
            for preference in reversed(prefer_from):
                cp_order = termdict[index][:]
                new_order = []
                for term in termdict[index]:
                    if term in preference:
                        cp_order.remove(term)
                        new_order.append(term)
                new_order.extend(cp_order)
                termdict[index] = new_order

    cp_sequence = sequence[:]
    sequence_que = list(reversed(sequence))
    splits = []

    while cp_sequence:
        candidates = termdict[sequence_que[-1]]
        if not candidates:
            sequence_que.pop()
            cp_sequence = cp_sequence[1:]
            continue

        for match in candidates:
            if cp_sequence.startswith(match):
                break
        else:
            sequence_que.pop()
            cp_sequence = cp_sequence[1:]
            continue

        if match not in stopwords:
            splits.append(match)
        cp_sequence = cp_sequence[len(match):]
        sequence_que = sequence_que[:-len(match)]

    return splits

def termfind_func(terms_to_match, stopwords, prefer_from=tuple()):
    def _termfind(sentences):
        terms = []
        for sent in sentences:
            terms.extend(matchterms(sent, terms_to_match, stopwords, prefer_from=prefer_from))
        return terms
    return _termfind

def uniq(term_sets):
    def _uniq(termset):
        seen = []
        for term in termset:
            if term not in seen:
                seen.append(term)
        return tuple(seen)
    for key in term_sets:
        term_sets[key] = _uniq(term_sets[key])
    return term_sets

def as_dist_map(term_set, all_terms, fill=None, logscale=False):
    distmap = dict.fromkeys(all_terms, 0.0)
    if fill is None:
        fill = 1.0 / float(len(term_set))
    for term in term_set:
        distmap[term] += fill
    if logscale:
        for term in term_set:
            if distmap[term] > 0.0:
                distmap[term] = 1.0 + math.log(distmap[term])
    return distmap

def mapmerge(map_a, map_b):
    result = map_a.copy()
    result.update(map_b)
    return result


if __name__ == '__main__':

    prepared = ['agoo', 'uboo', 'boo', 'goo', 'oo', 'aboo', 'ugoo', 'abebe']
    stops = ['abebe', 'obebe']
    seq = 'agooooboouboogooobebeagooooabebebooobebeuboogooabebeooooagooaboougooabebeagoo'
    splits = 'agoo,oo,boo,uboo,goo,agoo,oo,boo,uboo,goo,oo,oo,agoo,aboo,ugoo,agoo'.split(',')
    assert matchterms(seq, prepared, stops) == splits

    prepared_a = ['a', 'b', 'c', 'd', 'cd', 'e', 'f', 'ef', 'ghi']
    prepared_b = ['a', 'b', 'ab', 'c', 'd', 'e', 'f', 'ef', 'g', 'h', 'i', 'gh']
    prepared = prepared_a + prepared_b
    prefer = list(set(prepared_a).intersection(set(prepared_b)))
    seq = 'axbxabcdxcxdxefeefaxabaxcdcxghi'
    splits = 'a,b,a,b,c,d,c,d,ef,e,ef,a,a,b,a,c,d,c,gh,i'.split(',')
    assert matchterms(seq, prepared, [], prefer_from=[prefer,prepared_b]) == splits
