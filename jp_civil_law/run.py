# encoding: utf-8

import os
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


def path_from_me(path):
    i_am_in = os.path.dirname(__file__)
    return os.path.sep.join([i_am_in, path])

BUILD_DESTINATION = path_from_me('./build/graph.dot')

TERMS_DIR = path_from_me('./source/terms')
RELATIONS_DIR = path_from_me('./source/relations')


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

    relation_loaders = sum([list(rlmap.values()) for rlmap in relation_loader_maps], [])
    return relation_loaders

def get_graph(terms_dir, relations_dir):
    nodeprovider = get_node_provider(terms_dir)
    relation_loaders = get_relation_loaders(relations_dir, nodeprovider=nodeprovider)
    graph = sum(
        [rl.graph for rl in relation_loaders],
        nodeprovider.graph
    )
    return graph

def save(nx_graph, tofile):
    agraph = networkx.to_agraph(nx_graph)
    for node in agraph.nodes():
        node_obj = agraph.get_node(node)
        node_obj.attr['style'] = 'filled'
        node_obj.attr['fillcolor'] = '#edf1f2'
        node_obj.attr['fontcolor'] = '#121718'
    agraph.layout('twopi')
    agraph.write(tofile)


def run(args):
    print('start build from {{"{}", "{}"}}'.format(args.terms_dir, args.relations_dir))
    rdflib_graph = get_graph(args.terms_dir, args.relations_dir)
    nx_graph = rdflib_to_networkx(rdflib_graph)
    save(nx_graph, args.build_destination)
    print('done. saved to "{}"'.format(args.build_destination))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-t', '--terms_dir', default=TERMS_DIR)
    argparser.add_argument('-r', '--relations_dir', default=RELATIONS_DIR)
    argparser.add_argument('-o', '--build_destination', default=BUILD_DESTINATION)
    args = argparser.parse_args()
    run(args)
