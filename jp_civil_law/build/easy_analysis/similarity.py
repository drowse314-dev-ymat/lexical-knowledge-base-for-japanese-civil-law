# encoding: utf-8

import math
import itertools


def combination_sims(term_sets, dimensions, distribution=None):
    sims = {}
    for key1, key2 in itertools.combinations(sorted(term_sets), 2):
        rankmap_1 = distribution(term_sets[key1])
        rankmap_2 = distribution(term_sets[key2])
        vect_1 = rankmap2vect(rankmap_1, dimensions)
        vect_2 = rankmap2vect(rankmap_2, dimensions)
        sim = cosine_similarity(vect_1, vect_2)
        sims[(key1, key2)] = sim
    return sims

def cosine_similarity(vect_a, vect_b):
    norm = normalize(vect_a) * normalize(vect_b)
    prod = product(vect_a, vect_b)
    return prod / norm

def normalize(term_vector):
    return math.sqrt(product(term_vector, term_vector))

def product(vect_a, vect_b):
    return sum((p_a * p_b for p_a, p_b in itertools.izip(vect_a, vect_b)), 0.0)

def rankmap2vect(rankmap, dimensions):
    powervect = [rankmap[d] for d in dimensions]
    return powervect

def print_dist_similarities(nx_graph, term_sets,
                            distribution_fn=None, grep=None):
    sims = combination_sims(
        term_sets, nx_graph.nodes(),
        distribution=distribution_fn,
    )
    sim_pairs = [
        (u'{}: {}'.format(key1, key2), sims[(key1, key2)])
        for key1, key2 in sorted(sims)
        if (grep is not None and grep in (key1 + key2))
    ]
    sim_pairs.sort(key=lambda desc_sim: desc_sim[1], reverse=True)
    sum_sims = sum([sim for desc, sim in sim_pairs])
    for desc, sim_value in sim_pairs:
        sim_value_normalized = sim_value / sum_sims * 10.0
        print(u'{} --> {}'.format(desc, sim_value_normalized))
