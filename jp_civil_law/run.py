# encoding: utf-8

import os
import difflib
import argparse
import networkx
from lkbutils import (
    rdflib_load_terms,
    rdflib_load_relations,
    rdflib_to_networkx,
    yamllib,
)
from lkbutils.nodeprovider import (
    merge_nodeproviders,
)
from lkbutils.relationprovider import (
    noconflict_providers,
)
from lkbutils.declarative import leaves_from_struct
from build.easy_analysis import colouring
from build.easy_analysis import user_color, user_calc


def path_from_me(path):
    i_am_in = os.path.dirname(__file__)
    return os.path.sep.join([i_am_in, path])

BUILD_DESTINATION = path_from_me('./build/graph.dot')

TERMS_DIR = path_from_me('./source/terms')
RELATIONS_DIR = path_from_me('./source/relations')

TRACKING_LOG = path_from_me('./build/definitions.log')
WHITELIST = path_from_me('./build/files_to_load.yml')


def read_unicode(path, encoding='utf-8'):
    bytetext = open(path, 'rb').read()
    return bytetext.decode(encoding)

def yaml_files_in(directly, whitelist=None):
    for root, dirs, files in os.walk(directly):
        for f in files:
            if f.endswith('.yml'):
                path = os.path.sep.join([root, f])
                if whitelist is not None and f not in whitelist:
                    white = False
                else:
                    white = True
                yield path, white
                if white:
                    whitemark = 'w'
                else:
                    whitemark = 'b'
                print('    + .yml found: "{}" ({})'.format(path, whitemark))

def yaml_texts_in(directly, whitelist=None):
    for path, white in yaml_files_in(directly, whitelist=whitelist):
        yield read_unicode(path), white

def get_node_provider(src_dir, whitelist=None):
    node_providers = []
    white_nodes = []
    for yml, white in yaml_texts_in(src_dir, whitelist=whitelist):
        provider = rdflib_load_terms(yml).nodeprovider
        node_providers.append(provider)
        if white:
            white_nodes.extend(provider.nameprovider.origin_names)
    return merge_nodeproviders(*node_providers), white_nodes

def get_relation_loaders(src_dir, nodeprovider=None, whitelist=None):
    relation_loader_maps = []
    white_rels = []
    for yml, white in yaml_texts_in(src_dir, whitelist=whitelist):
        loader_map = rdflib_load_relations(yml, nodeprovider=nodeprovider)
        relation_loader_maps.append(loader_map)
        if white:
            pairs = []
            for loader in loader_map.values():
                pairs.extend(list(loader.relationprovider.relationchecker.iterpairs()))
            for src, dest in pairs:
                white_rels.append(
                    (nodeprovider.get_origin_name_from(src),
                     nodeprovider.get_origin_name_from(dest))
                )

    relation_loaders = sum(
        [
            list(rlmap[r] for r in sorted(rlmap))
            for rlmap in relation_loader_maps
        ],
        [],
    )
    check_relation_conflicts(relation_loaders, nodeprovider)
    return relation_loaders, white_rels

def check_relation_conflicts(relation_loaders, nodeprovider):
    providers = [rl._relation_provider for rl in relation_loaders]
    noconflict_providers(providers, nodeprovider=nodeprovider)

def get_graph(terms_dir, relations_dir, log=TRACKING_LOG, use_whitelist=False):
    if use_whitelist:
        whitelist = load_whitelist()
    else:
        whitelist = None
    nodeprovider, white_nodes = get_node_provider(terms_dir, whitelist=whitelist)
    relation_loaders, white_rels = get_relation_loaders(relations_dir, nodeprovider=nodeprovider, whitelist=whitelist)
    showdiff(log, nodeprovider, [rl.relationprovider for rl in relation_loaders])
    graph = sum(
        [rl.graph for rl in relation_loaders],
        nodeprovider.graph
    )
    return graph, white_nodes, white_rels

def load_whitelist(src=WHITELIST):
    try:
        yaml = read_unicode(src)
    except IOError:
        return None
    data = yamllib.parse_yaml(yaml)
    whitelist = list(leaves_from_struct(data))
    if not whitelist:
        return None
    return whitelist

def showdiff(logfile, nodeprovider, relationproviders, logencoding='utf8'):
    serialized = u"---\n"
    serialized += nodeprovider.serialize()
    serialized += u"---\n"
    serialized += u"---\n".join(rp.serialize(nodeprovider=nodeprovider) for rp in relationproviders)
    if os.path.exists(logfile):
        print(u"\n=========================================================")
        print(u'diff from prev. definition: "{}"'.format(logfile))
        print(u"---------------------------------------------------------")
        prev = open(logfile, 'rb').read().decode(logencoding).split(u'\n')
        for line in difflib.unified_diff(prev, serialized.split(u'\n')):
            print(line)
        print(u"=========================================================\n")
    else:
        print('definition log does not exists: "{}"'.format(logfile))
    with open(logfile, 'wb') as log:
        log.write(serialized.encode(logencoding))

def save_graph(nx_graph, tofile, cut_solos=False, rankcolor=False,
               white_nodes=None, white_rels=None):

    # complete graphs
    agraph = networkx.to_agraph(nx_graph)
    nx_orig_graph = nx_graph.copy()

    # color or process
    featured = hook_color(nx_graph, agraph, rankcolor=rankcolor)
    hook_calc(nx_orig_graph)

    # filter
    filter_target(nx_graph, white_nodes, white_rels)
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
    print('start build from {{"{}", "{}"}}'.format(args.terms_dir, args.relations_dir))
    rdflib_graph, white_nodes, white_rels = get_graph(
        args.terms_dir, args.relations_dir, log=args.tracking_log,
        use_whitelist=args.use_whitelist,
    )
    nx_graph = rdflib_to_networkx(rdflib_graph)
    save_graph(
        nx_graph, args.build_destination, cut_solos=args.cut_solos,
        rankcolor=args.rankcolor,
        white_nodes=white_nodes, white_rels=white_rels,
    )
    print('done. saved to "{}"'.format(args.build_destination))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-t', '--terms_dir', default=TERMS_DIR)
    argparser.add_argument('-r', '--relations_dir', default=RELATIONS_DIR)
    argparser.add_argument('-o', '--build_destination', default=BUILD_DESTINATION)
    argparser.add_argument('-l', '--tracking_log', default=TRACKING_LOG)
    argparser.add_argument('-w', '--use_whitelist', action='store_true', default=False)
    argparser.add_argument('--cut_solos', action='store_true', default=False)
    argparser.add_argument('--rankcolor', action='store_true', default=False)
    args = argparser.parse_args()
    run(args)
