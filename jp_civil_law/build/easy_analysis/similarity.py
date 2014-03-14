# encoding: utf-8

import math
import itertools
from . import casedata as data


answermap = data.answermap
def selective_print(key1, map_1, key2, map_2):
    if key1 in answermap.get(key2, []):
        q, qmap, a, amap = key2, map_2, key1, map_1
    if key2 in answermap.get(key1, []):
        q, qmap, a, amap = key1, map_1, key2, map_2
    else:
        q, a = None, None
    def _mapped(somemap):
        return [u'{}/{}'.format(k, round(v, 2)) for k, v in somemap.iteritems() if v != 0.0]
    if None not in (q, a):
        print(u'::Terms in question -- correct answer::')
        print(u'q({})--a({})'.format(q, a))
        print(u'===========')
        qmapped = _mapped(qmap)
        print(u'#[{}]: {}'.format(q, u','.join(qmapped)))
        amapped = _mapped(amap)
        print(u'#[{}]: {}'.format(a, u','.join(amapped)))
        print(u'===========\n')


def combination_sims(term_sets, dimensions, distribution=None):
    sims = {}

    def calculate_distribution(key, distcache={}):
        assert set(term_sets[key]).issubset(set(dimensions)), \
               (u'{}: '.format(key) + u','.join(set(term_sets[key]).difference(set(dimensions)))).encode('utf-8')
        if key not in distcache:
            rankmap, mod_terms = distribution(term_sets[key], label=key)
            distcache[key] = rankmap, mod_terms
        return distcache[key]

    for key1, key2 in itertools.permutations(sorted(term_sets, reverse=True), 2):
        rankmap_1, mod_terms1 = calculate_distribution(key1)
        rankmap_2, mod_terms2 = calculate_distribution(key2)
        vect_1 = rankmap2vect(rankmap_1, dimensions)
        vect_2 = rankmap2vect(rankmap_2, dimensions)
        sim = cosine_similarity(vect_1, vect_2)
        sims[(key1, key2)] = sim
    return sims

def joint_combination_sims(term_sets, dimensions, jdistribution_fn=None):
    sims = {}
    def calculate_distribution(key_a, key_b, distcache={}):
        assert set(term_sets[key_a]).issubset(set(dimensions)), \
               (u'{}: '.format(key_a) + u','.join(set(term_sets[key_a]).difference(set(dimensions)))).encode('utf-8')
        assert set(term_sets[key_b]).issubset(set(dimensions)), \
               (u'{}: '.format(key_b) + u','.join(set(term_sets[key_b]).difference(set(dimensions)))).encode('utf-8')
        if (key_a, key_b) not in distcache:
            rankmap_a, mod_terms_a, rankmap_b, mod_terms_b = jdistribution_fn(key_a, term_sets[key_a], key_b, term_sets[key_b])
            distcache[(key_a), (key_b)] = rankmap_a, mod_terms_a, rankmap_b, mod_terms_b
        return distcache[(key_a, key_b)]

    for key1, key2 in itertools.permutations(sorted(term_sets, reverse=True), 2):
        rankmap_1, mod_terms1, rankmap_2, mod_terms_b = calculate_distribution(key1, key2)
        selective_print(key1, rankmap_1, key2, rankmap_2)
        vect_1 = rankmap2vect(rankmap_1, dimensions)
        vect_2 = rankmap2vect(rankmap_2, dimensions)
        sim = cosine_similarity(vect_1, vect_2)
        sims[(key1, key2)] = sim
    return sims

def cosine_similarity(vect_a, vect_b):
    assert len(vect_a) == len(vect_b)
    norm = normalize(vect_a) * normalize(vect_b)
    if norm == 0.0:
        return 0.0
    prod = product(vect_a, vect_b)
    return prod / norm

def normalize(term_vector):
    return math.sqrt(product(term_vector, term_vector))

def product(vect_a, vect_b):
    return sum((p_a * p_b for p_a, p_b in itertools.izip(vect_a, vect_b)), 0.0)

def rankmap2vect(rankmap, dimensions):
    powervect = [rankmap[d] for d in dimensions]
    return powervect

def dist_similarities(dimensions, term_sets, distribution_fn=None):
    return combination_sims(
        term_sets, dimensions, distribution=distribution_fn,
    )

def joint_dist_similarities(dimensions, term_sets, distribution_fn=None):
    return joint_combination_sims(
        term_sets, dimensions, jdistribution_fn=distribution_fn,
    )

def print_dist_similarities(dimensions, term_sets,
                            distribution_fn=None, grep=None,
                            sumrange=None):
    sims = dist_similarities(dimensions, term_sets, distribution_fn)
    sim_pairs = [
        (u'{},{}'.format(key1, key2), sims[(key1, key2)])
        for key1, key2 in sorted(sims)
        if (grep is not None and grep in (key1 + key2))
    ]
    sim_pairs.sort(key=lambda desc_sim: desc_sim[1], reverse=True)
    sum_sims = sum([sim for desc, sim in sim_pairs])
    for desc, sim_value in sim_pairs:
        if sumrange is not None:
            sim_value_normalized = sim_value / sum_sims * sumrange
        else:
            sim_value_normalized = sim_value
        print(u'{},{}'.format(desc, round(sim_value_normalized, 3)))
