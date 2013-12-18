# encoding: utf-8

import os
import difflib
import logbook
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


def path_from_me(path):
    i_am_in = os.path.dirname(__file__)
    return os.path.sep.join([i_am_in, path])

TERMS_DIR = path_from_me('./source/terms')
RELATIONS_DIR = path_from_me('./source/relations')
WHITELIST = path_from_me('./build/files_to_load.yml')

TRACKING_LOG = path_from_me('./build/definitions.log')

logger = logbook.Logger('graph-builder')
logger_handler = logbook.StderrHandler()
logger_handler.format_string = '({record.channel}:{record.level_name}) {record.message}'
logger.handlers.append(logger_handler)
difflogger = logbook.Logger('graph-diff')
difflogger_handler = logbook.StderrHandler()
difflogger_handler.format_string = '{record.message}'
difflogger.handlers.append(difflogger_handler)

logger.level_name = 'NOTICE'
difflogger.level_name = 'NOTICE'


def read_unicode(path, encoding='utf-8'):
    bytetext = open(path, 'rb').read()
    return bytetext.decode(encoding)

def yaml_files_in(directory, whitelist=None):
    for root, dirs, files in os.walk(directory):
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
                logger.info('+ .yml found: "{}" ({})'.format(path, whitemark))

def yaml_texts_in(directory, whitelist=None):
    for path, white in yaml_files_in(directory, whitelist=whitelist):
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


def get_graph(terms_dir=TERMS_DIR, relations_dir=RELATIONS_DIR,
              log=TRACKING_LOG, use_whitelist=False, as_nx=False):
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
    if as_nx:
        graph = rdflib_to_networkx(graph)
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
        difflogger.info(u"\n=========================================================")
        difflogger.info(u'diff from prev. definition: "{}"'.format(logfile))
        difflogger.info(u"---------------------------------------------------------")
        prev = open(logfile, 'rb').read().decode(logencoding).split(u'\n')
        for line in difflib.unified_diff(prev, serialized.split(u'\n')):
            difflogger.info(line)
        difflogger.info(u"=========================================================\n")
    else:
        difflogger.info('definition log does not exists: "{}"'.format(logfile))
    with open(logfile, 'wb') as log:
        log.write(serialized.encode(logencoding))


if __name__ == '__main__':
    from networkx import DiGraph
    graph, _, _ = get_graph(as_nx=True)
    assert isinstance(graph, DiGraph)
