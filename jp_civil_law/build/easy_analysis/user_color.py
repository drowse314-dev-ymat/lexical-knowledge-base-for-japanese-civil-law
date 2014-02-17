# encoding: utf-8

import functools
import networkx
import colors.w3c
from . import casedata as data
from . import casemaker
from . import pagerank as pr
from . import colouring as color
from . import termexpand as tex


class terms:
    # label = u'375'
    ## MUST SET ##
    t = getattr(data, 't' + ''.join(data.answermap[u'q19/7/3']))
    # a = data.t375_add
    q = data.tq19_7_3
    # qa = data.tq18_15_2_add
    bridge = [
        u'所有', u'占有',
        u'財産', u'動産',
        u'譲渡',
        u'法定果実',
        u'賃貸借', u'賃貸物',
        u'貸借契約',
        u'契約', u'目的',
    ]
    q18154bridge = [
        u'元本確定', u'根保証', u'根抵当',
        u'担保', u'担保権', u'担保物権', u'抵当権',
        u'debts and credits',
        u'履行期',
        u'制限物権', u'本権', u'物権', u'権利',
        u'権利者',
    ]
    q18152bridge = [
        u'元本確定', u'根保証', u'根抵当',
        u'debts and credits',
        u'担保権', u'担保物権',
    ]
    q18151bridge = [
        u'抵当権', u'優先権', u'担保物権', u'担保権',
        u'元本確定', u'元本確定期日',
        u'根保証', u'根抵当',
        u'期日', u'期限',
        u'制限物権', u'本権', u'物権', u'目的物',
    ]


def run(nx_graph, agraph):

    t = terms.t
    # a = terms.a
    q = terms.q
    # qa = terms.qa
    onlyterms = False

    # Pagerank method for following calcs.
    prmeth = nondistribution(nx_graph)

    featured = non_color(nx_graph, agraph, prmeth)
    assert featured is not None

    if onlyterms:
        filter_nodes(nx_graph, featured or a)

    return featured


def non_color(nx_graph, agraph, prmeth):
    color.set_graphcolor(agraph)
    return []

def fancy_color(nx_graph, agraph, prmeth):
    from .user_calc import create_mapper
    mapper = create_mapper(nx_graph)
    rankmap, ex = mapper(terms.t, label=terms.label)
    colormap = color.pwrvariation_with_ranks(agraph, rankmap, fullrange=True)
    color.color_graph(agraph, colormap, blueback=True)
    color.color_nodeborders(agraph, terms.a)
    color.color_nodeborders(agraph, ex, preset_with_fill='b')
    color.color_nodeborders(agraph, terms.t, preset_with_fill='ab')
    print(u'diffs: ' + u','.join(set(ex).difference(set(terms.t))))
    return terms.t + ex + terms.a

def tq_compare(nx_graph, agraph, prmeth):
    color.set_graphcolor(agraph)
    color.color_nodeborders(agraph, terms.q, preset_with_fill='a')
    color.color_nodeborders(agraph, terms.t, preset_with_fill='b')
    color.color_nodeborders(agraph, set(terms.t).intersection(set(terms.q)), preset_with_fill='ab')
    return terms.t + terms.q

def tq_bridge(nx_graph, agraph, prmeth):
    color.color_nodeborders(agraph, terms.bridge, color=colors.w3c.lightsalmon)
    color.color_nodeborders(agraph, terms.q, preset_with_fill='a')
    color.color_nodeborders(agraph, terms.t, preset_with_fill='b')
    color.color_nodeborders(agraph, set(terms.t).intersection(set(terms.q)), preset_with_fill='ab')
    return terms.t + terms.q + terms.bridge

def t_raw_a_compare(nx_graph, agraph, prmeth):
    map_higher, _ = prmeth(terms.t, label=terms.label)
    avr = sum(map_higher.values()) / float(len(map_higher))
    fillvalue = 0.1 / float(len(terms.a))
    map_lower = data.as_dist_map(terms.a, agraph.nodes(), fill=fillvalue)
    color.set_mixed_graphcolor(agraph, map_higher, map_lower, fullrange=True)
    color.color_nodeborders(agraph, terms.a, preset_with_fill='a')
    color.color_nodeborders(agraph, terms.t, preset_with_fill='b')
    color.color_nodeborders(agraph, set(terms.a).intersection(set(terms.t)), preset_with_fill='ab')
    return terms.t + terms.a

def shortest_path(nx_graph, agraph, prmeth):
    undir_graph = nx_graph.to_undirected()
    len_from_root = networkx.shortest_path_length(undir_graph, source=u'root')
    maxdepth = max(len_from_root.values())
    for src, dest in undir_graph.edges():
        if undir_graph[src][dest]['label'] in (u'hyper', u'status of', u'results'):
            depthrate = (len_from_root[src] + len_from_root[dest]) / (2.0 * maxdepth)
            factor = 0.1 ** depthrate
            undir_graph[src][dest]['weight'] = 1.5 + 2.0 * depthrate
        else:
            undir_graph[src][dest]['weight'] = 1.0
    shpaths = networkx.shortest_path(undir_graph, weight='weight')
    lenshpaths = networkx.shortest_path_length(undir_graph, weight='weight')
    for n in shpaths.keys():
        if n not in terms.t:
            shpaths.pop(n)
            lenshpaths.pop(n)
    lenpairmap = []
    for src, lens in lenshpaths.iteritems():
        for dest, length in lens.iteritems():
            lenpairmap.append((length, src, dest))
    lenpairmap.sort()
    paths = []
    rest = set(terms.t)
    for l,s,d in lenpairmap:
        if not rest:
            break
        if (s not in rest or d not in rest and
            s in terms.t or d in terms.t and s != d):
            path = shpaths[s][d]
            paths.append(shpaths[s][d])
            try:
                rest.remove(s)
                rest.remove(d)
            except KeyError:
                pass
    tspread = sum(paths, [])
    map_lower = data.as_dist_map(terms.a, agraph.nodes(), fill=0.5)
    map_higher = data.as_dist_map(tspread, agraph.nodes(), fill=0.5)
    color.set_mixed_graphcolor(agraph, map_higher, map_lower, fullrange=True)
    color.color_nodeborders(agraph, terms.a, preset_with_fill='a')
    color.color_nodeborders(agraph, tspread, preset_with_fill='b')
    color.color_nodeborders(agraph, set(terms.a).intersection(set(tspread)), preset_with_fill='ab')
    return terms.a + tspread

def term_expansion(nx_graph, agraph, prmeth):
    ex, scoremap = tex.populate(
        terms.t, nx_graph,
        methods=tex.all_methods,
    )
    map_higher, _ = prmeth(ex, label=terms.label)
    map_lower, _ = prmeth(terms.t, label=terms.label)
    color.set_mixed_graphcolor(agraph, map_higher, map_lower, fullrange=True)
    color.color_nodeborders(agraph, terms.a)
    color.color_nodeborders(agraph, ex, preset_with_fill='b')
    color.color_nodeborders(agraph, terms.t, preset_with_fill='ab')
    print(u'diffs: ' + u','.join(set(ex).difference(set(terms.t))))
    return terms.t + ex + terms.a

def pagerank_method(nx_graph, agraph):
    return pr.pr_distribution_fn(
        nx_graph,
        preproc=lambda g: g.to_undirected(),
        pagerank=create_pagerank_functor('normal'),
        amplify=100.0,
    )

def nondistribution(nx_graph):
    _allterms = nx_graph.nodes()
    def _map(terms, label=None):
        mapped = casemaker.as_dist_map(terms, _allterms, fill=1.0)
        return mapped, terms
    return _map


def create_pagerank_functor(method):
    def pr_X_btw(nx_graph, personalization=None, **kwargs):
        pageranks = networkx.pagerank(nx_graph, personalization=personalization, **kwargs)
        btwness_vals = networkx.betweenness_centrality(nx_graph)
        ranks = {n: pageranks[n] * btwness_vals[n] for n in pageranks}
        factor = 1.0 / sum(ranks.values())
        for node in ranks:
            ranks[node] *= factor
        return ranks
    methods = dict(
        normal=networkx.pagerank,
        cond=functools.partial(
            pr.PageRank.pagerank_conditional,
            conditional_links=(u'hyper', u'status of', u'results'),#, u'attr', u'within', u'auth', u'auth by',),
            # in_degree=True, out_degree=True,
            # error_at_max=False,
        ),
        btw=pr_X_btw,
    )
    return methods[method]

def filter_nodes(nx_graph, nodes):
    to_remove = set(nx_graph.nodes()).difference(nodes)
    nx_graph.remove_nodes_from(to_remove)
