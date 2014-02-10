# encoding: utf-8

import itertools
import networkx
from networkx.exception import NetworkXNoPath
import logbook


logger = logbook.Logger('termexpand')
logger_handler = logbook.StderrHandler()
logger_handler.format_string = '({record.channel}:{record.level_name}) {record.message}'
logger.handlers.append(logger_handler)
logger.level_name = 'NOTICE'


hyper_props = (u'hyper', u'hyperx')
frame_props = (u'sbj', u'obj', u'attr_slot')
slot_props = tuple(list(frame_props) + [u'antecedent_to', u'auth', u'auth_by', u'within'])
all_props = tuple(list(slot_props) + list(hyper_props))


scorebase = dict(
    hyperframes=1.0,
    hypoframes=0.3,
    attr_hypers=0.5,
    prerequisites=0.8,
    ascending_ways=0.2,
    ascendedhubs=0.2,
    attrs_of_attrs=0.5,
)

def populate(terms, nx_graph, methods=tuple()):
    logger.debug(u'** start expansion from: [{}]'.format(u','.join(terms)))
    expand = list(terms)
    scoremap = dict.fromkeys(expand, 0.5)
    exit_margin = 1
    init_margin = exit_margin
    while True:
        prev_terms = expand[:]
        for method in methods:
            for ex, reasons in method(expand, nx_graph):
                expand.append(ex)
                scoremap[ex] = scorebase[method.__name__]
                logger.debug(u'expanded: {} from <<{}>> by [{}]'.format(ex, method.__name__, u','.join(reasons)))
        if set(prev_terms) == set(expand):
            exit_margin -= 1
            if exit_margin == 0:
                break
        else:
            exit_margin = init_margin
    return tuple(expand), scoremap


def hyperframes(terms, nx_graph):
    new = []
    for term in terms:
        current = terms + new
        iter_hypers = links_from(term, nx_graph, hyper_props)

        for term_, hyperterm, attrs in iter_hypers:
            iter_slots = links_from(hyperterm, nx_graph, slot_props)

            for hyperterm_, frameterm, attrs in iter_slots:

                if frameterm in current and hyperterm_ not in current:
                    new.append(hyperterm_)
                    yield hyperterm_, [term_, frameterm]

def hypoframes(terms, nx_graph):
    new = []
    for term in nx_graph:
        current = terms + new
        if term in current:
            continue

        iter_hypers = links_from(term, nx_graph, hyper_props)
        hypers = [hyper for src, hyper, attrs in iter_hypers]
        if not hypers or set(hypers).isdisjoint(set(current)):
            continue

        iter_slots = links_from(term, nx_graph, frame_props)
        slots = [slot for src, slot, attrs in iter_slots]
        if not slots or set(slots).isdisjoint(set(current)):
            continue

        new.append(term)
        yield term, hypers + slots

def attr_hypers(terms, nx_graph):
    new = []
    for term in terms:
        current = terms + new
        iter_attrs = links_from(term, nx_graph, [u'attr_slot'])

        for term_, attrterm, attrs in iter_attrs:
            iter_hypers = links_from(attrterm, nx_graph, hyper_props)

            for attrterm_, hyperterm, attrs in iter_hypers:

                if hyperterm in current and attrterm_ not in current:
                    new.append(attrterm_)
                    yield attrterm_, [term_, hyperterm]

def prerequisites(terms, nx_graph):
    new = []
    for term in nx_graph:
        current = terms + new
        if term in current:
            continue

        iter_slots = links_from(term, nx_graph, all_props)
        slots = [slot for pre, slot, attrs in iter_slots]

        if not slots or len(set(slots).intersection(set(current))) < 2:
            continue

        new.append(term)
        yield term, slots

def ascending_ways(terms, nx_graph):
    graph_copy = nx_graph.copy()
    for src, dest, attrs in graph_copy.edges(data=True):
        if attrs['label'] not in hyper_props:
            graph_copy.remove_edge(src, dest)

    new = []
    for u, v in itertools.permutations(graph_copy.nodes(), 2):
        current = terms + new
        if u not in current or v not in current:
            continue

        try:
            path_uv = networkx.shortest_path(graph_copy, source=u, target=v)
        except NetworkXNoPath:
            continue

        for stop in path_uv:
            if stop not in current:
                new.append(stop)
                yield stop, [u, v]

def ascendedhubs(terms, nx_graph):
    graph_copy = nx_graph.copy()
    for src, dest, attrs in graph_copy.edges(data=True):
        if attrs['label'] not in hyper_props:
            graph_copy.remove_edge(src, dest)

    new = []
    for u, v in itertools.permutations(graph_copy.nodes(), 2):
        current = terms + new
        if u not in current:
            continue

        try:
            path_uv = networkx.shortest_path(graph_copy, source=u, target=v)
        except NetworkXNoPath:
            continue

        iter_slots = links_from(v, nx_graph, all_props)
        slots = [slot for pre, slot, attrs in iter_slots]
        if not slots or len(set(slots).intersection(set(current))) < 2:
            continue

        for stop in path_uv:
            if stop not in current:
                new.append(stop)
                yield stop, [u, v] + slots

def attrs_of_attrs(terms, nx_graph):
    new = []
    for term in terms:
        current = terms + new
        iter_attrs = links_from(term, nx_graph, [u'attr_slot'])

        for term_, attrterm, attrs in iter_attrs:
            if attrterm in current:
                continue
            iter_attr_of_attrs = links_from(attrterm, nx_graph, [u'attr_slot'])

            for attrterm_, attr_of_attr, attrs in iter_attr_of_attrs:
                if attr_of_attr not in current:
                    continue

                if attr_of_attr in nx_graph[term_] or term_ in nx_graph[attr_of_attr]:
                    new.append(attrterm_)
                    yield attrterm_, [term_, attr_of_attr]


def links_from(node, nx_graph, props):
    for src, dest, attrs in nx_graph.edges(nbunch=[node], data=True):
        if attrs['label'] not in props:
            continue
        yield src, dest, attrs

all_methods = (
    hyperframes,
    hypoframes,
    attr_hypers,
    prerequisites,
    ascending_ways,
    ascendedhubs,
    attrs_of_attrs,
)
