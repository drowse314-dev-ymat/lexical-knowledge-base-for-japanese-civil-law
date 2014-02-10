# encoding: utf-8

import os
import argparse
import logbook
import networkx
from build.easy_analysis import colouring
from build.easy_analysis import user_color, user_calc
from . import graph


logger = logbook.Logger('run-build')
logger_handler = logbook.StderrHandler()
logger_handler.format_string = '({record.channel}:{record.level_name}) {record.message}'
logger.handlers.append(logger_handler)


def path_from_me(path):
    i_am_in = os.path.dirname(__file__)
    return os.path.sep.join([i_am_in, path])

BUILD_DESTINATION = path_from_me('./build/graph.dot')


def save_graph(nx_graph, tofile, cut_solos=False, rankcolor=False,
               white_nodes=None, white_rels=None):

    # complete graphs
    agraph = networkx.to_agraph(nx_graph)
    nx_orig_graph = nx_graph.copy()

    # color or process
    featured = hook_color(nx_graph, agraph, rankcolor=rankcolor)
    hook_calc(nx_orig_graph)

    # filter
    filter_target(nx_graph, (white_nodes + featured), white_rels)
    if cut_solos:
        remove_solos(nx_graph, without=featured)
    reduced_agraph = networkx.to_agraph(nx_graph)
    copy_agraph_attrs(agraph, reduced_agraph)

    reduced_agraph.graph_attr['rankdir'] = 'BT'
    reduced_agraph.graph_attr['remincross'] = 'true'
    reduced_agraph.layout('twopi')

    reduced_agraph.write(tofile)

def hook_color(nx_graph, agraph, rankcolor=False):
    if rankcolor:
        rankmap = user_color.pagerank_method(nx_graph, agraph)(user_color.terms.t)
        colouring.set_graphcolor(agraph, rankcolor=True, rankmap=rankmap, fullrange=True)
        colouring.color_nodeborders(agraph, user_color.terms.a, preset_with_fill='a')
        colouring.color_nodeborders(agraph, user_color.terms.t, preset_with_fill='ab')
        featured = user_color.terms.a
    else:
        featured = user_color.run(nx_graph, agraph)
    return featured

def hook_calc(nx_graph):
    user_calc.run(nx_graph)

def filter_target(nx_graph, target_nodes=None, target_rels=None):
    if target_nodes is not None:
        to_remove = set(nx_graph.nodes()).difference(target_nodes)
        nx_graph.remove_nodes_from(to_remove)
    if target_rels is not None:
        to_remove = set(nx_graph.edges()).difference(target_rels)
        nx_graph.remove_edges_from(to_remove)

def remove_solos(nx_graph, without=tuple()):
    degs = nx_graph.degree()
    for node in degs:
        if degs[node] == 0 and node not in without:
            nx_graph.remove_node(node)

def copy_agraph_attrs(srcg, destg):
    destg.graph_attr.update(srcg.graph_attr)
    destg.node_attr.update(srcg.node_attr)
    destg.edge_attr.update(srcg.edge_attr)
    for node in destg.nodes():
        node = destg.get_node(node)
        node.attr.update(srcg.get_node(node).attr)
    for edge in destg.edges():
        edge = destg.get_edge(*edge)
        edge.attr.update(srcg.get_edge(*edge).attr)


def run(args):

    logger.level_name = args.loglevel
    graph.logger.level_name = args.loglevel
    graph.difflogger.level_name = args.loglevel

    logger.notice('start build from {{"{}", "{}"}}'.format(args.terms_dir, args.relations_dir))
    nx_graph, white_nodes, white_rels = graph.get_graph(
        args.terms_dir, args.relations_dir, log=args.tracking_log,
        use_whitelist=args.use_whitelist, as_nx=True
    )
    save_graph(
        nx_graph, args.build_destination, cut_solos=args.cut_solos,
        rankcolor=args.rankcolor,
        white_nodes=white_nodes, white_rels=white_rels,
    )
    logger.notice('done. saved to "{}"'.format(args.build_destination))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-t', '--terms_dir', default=graph.TERMS_DIR)
    argparser.add_argument('-r', '--relations_dir', default=graph.RELATIONS_DIR)
    argparser.add_argument('-o', '--build_destination', default=BUILD_DESTINATION)
    argparser.add_argument('-l', '--tracking_log', default=graph.TRACKING_LOG)
    argparser.add_argument('-w', '--use_whitelist', action='store_true', default=False)
    argparser.add_argument('--cut_solos', action='store_true', default=False)
    argparser.add_argument('--rankcolor', action='store_true', default=False)
    argparser.add_argument('--loglevel', default='INFO')
    args = argparser.parse_args()
    run(args)
