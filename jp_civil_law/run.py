# encoding: utf-8

import os
import difflib
import argparse
import networkx
from lkbutils import (
    rdflib_load_terms,
    rdflib_load_relations,
    rdflib_to_networkx,
)
from lkbutils.nodeprovider import (
    merge_nodeproviders,
)
from lkbutils.relationprovider import (
    noconflict_providers,
)


def path_from_me(path):
    i_am_in = os.path.dirname(__file__)
    return os.path.sep.join([i_am_in, path])

BUILD_DESTINATION = path_from_me('./build/graph.dot')

TERMS_DIR = path_from_me('./source/terms')
RELATIONS_DIR = path_from_me('./source/relations')

TRACKING_LOG = path_from_me('./build/definitions.log')


def read_unicode(path, encoding='utf-8'):
    bytetext = open(path, 'rb').read()
    return bytetext.decode(encoding)

def yaml_files_in(directly):
    for root, dirs, files in os.walk(directly):
        for f in files:
            if f.endswith('.yml'):
                path = os.path.sep.join([root, f])
                print('    + .yml found: "{}"'.format(path))
                yield path

def yaml_texts_in(directly):
    for path in yaml_files_in(directly):
        yield read_unicode(path)

def get_node_provider(src_dir):
    node_providers = [
        rdflib_load_terms(yml).nodeprovider
        for yml in yaml_texts_in(src_dir)
    ]
    return merge_nodeproviders(*node_providers)

def get_relation_loaders(src_dir, nodeprovider=None):
    relation_loader_maps = [
        rdflib_load_relations(yml, nodeprovider=nodeprovider)
        for yml in yaml_texts_in(src_dir)
    ]

    sum_len_keys = sum([len(rlmap) for rlmap in relation_loader_maps])
    len_merged_keys = len(set(sum([list(rlmap.keys()) for rlmap in relation_loader_maps], [])))
    assert (sum_len_keys == len_merged_keys), 'multiple definitions for some relation'

    relation_loaders = sum(
        [
            list(rlmap[r] for r in sorted(rlmap))
            for rlmap in relation_loader_maps
        ],
        [],
    )
    check_relation_conflicts(relation_loaders, nodeprovider)
    return relation_loaders

def check_relation_conflicts(relation_loaders, nodeprovider):
    providers = [rl._relation_provider for rl in relation_loaders]
    noconflict_providers(providers, nodeprovider=nodeprovider)

def get_graph(terms_dir, relations_dir, log=TRACKING_LOG):
    nodeprovider = get_node_provider(terms_dir)
    relation_loaders = get_relation_loaders(relations_dir, nodeprovider=nodeprovider)
    showdiff(log, nodeprovider, [rl.relationprovider for rl in relation_loaders])
    graph = sum(
        [rl.graph for rl in relation_loaders],
        nodeprovider.graph
    )
    return graph

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

def save(nx_graph, tofile):
    agraph = networkx.to_agraph(nx_graph)
    agraph.graph_attr['remincross'] = 'true'
    for node in agraph.nodes():
        node_obj = agraph.get_node(node)
        node_obj.attr['style'] = 'filled'
        node_obj.attr['fillcolor'] = '#edf1f2'
        node_obj.attr['fontcolor'] = '#121718'
    agraph.layout('twopi')
    agraph.write(tofile)


def run(args):
    print('start build from {{"{}", "{}"}}'.format(args.terms_dir, args.relations_dir))
    rdflib_graph = get_graph(args.terms_dir, args.relations_dir, log=args.tracking_log)
    nx_graph = rdflib_to_networkx(rdflib_graph)
    save(nx_graph, args.build_destination)
    print('done. saved to "{}"'.format(args.build_destination))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-t', '--terms_dir', default=TERMS_DIR)
    argparser.add_argument('-r', '--relations_dir', default=RELATIONS_DIR)
    argparser.add_argument('-o', '--build_destination', default=BUILD_DESTINATION)
    argparser.add_argument('-l', '--tracking_log', default=TRACKING_LOG)
    args = argparser.parse_args()
    run(args)
