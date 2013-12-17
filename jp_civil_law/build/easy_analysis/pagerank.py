# encoding: utf-8

import networkx as nx
from networkx.exception import NetworkXError


def personalization_map(targets, whole, amplify=100.0):
    flat = 1.0
    featured = flat * amplify
    p = dict.fromkeys(whole, flat)
    for elem in set(targets):
        p[elem] = featured
    return p

def pr_distribution_fn(nx_graph, pagerank=nx.pagerank, preproc=lambda x: x, amplify=100.0):
    graph_copy = nx_graph.copy()
    graph_copy = preproc(graph_copy)
    def _distribution(featured_nodes):
        return pagerank(
            graph_copy,
            personalization=personalization_map(
                featured_nodes, graph_copy.nodes(),
                amplify=amplify
            ),
        )
    return _distribution


class PageRank(object):

    @classmethod
    def graphtype_for_pr(klass, G):
        if type(G) == nx.MultiGraph or type(G) == nx.MultiDiGraph:
            raise Exception("pagerank() not defined for graphs with multiedges.")
        D = klass.directed(G)
        return D

    @classmethod
    def directed(klass, G):
        if not G.is_directed():
            D = G.to_directed()
        else:
            D = G
        return D

    @classmethod
    def stochastic(klass, D, weight):
        # create a copy in (right) stochastic form
        ## a form in which transition probs. are equally distributed
        H = nx.stochastic_graph(D, weight=weight)
        return H

    @classmethod
    def v_normalize(klass, v):
        factor = 1.0 / sum(v.values())
        for node in v:
            v[node] *= factor
        return v

    @classmethod
    def start_vector(klass, H, eq_prob, nstart=None):
        # choose fixed starting vector if not given
        if nstart is None:
            I = dict.fromkeys(H, eq_prob)
        else:
            I = nstart
            # normalize starting vector to 1
            I = klass.v_normalize(I)
        return I

    @classmethod
    def personalization_vector(klass, personalization, eq_prob, H):
        # assign uniform personalization/teleportation vector if not given
        if personalization is None:
            teleportation = dict.fromkeys(H, eq_prob)
        else:
            teleportation = personalization
            # normalize starting vector to 1
            teleportation = klass.v_normalize(teleportation)
            if set(teleportation) != set(H):
                raise NetworkXError('Personalization vector '
                                    'must have a value for every node')
        return teleportation

    @classmethod 
    def find_dangle(klass, H):
        # "dangling" nodes, no links out from them
        out_degree = H.out_degree()
        dangle = [
            node for node in H
            if out_degree[node] == 0.0
        ]
        return dangle

    @classmethod
    def converged(klass, I, prev_I, tol):
        err=sum([abs(I[n]-prev_I[n]) for n in I])
        if err < tol:
            return True
        return False

    @classmethod
    def pagerank(klass, G, alpha=0.85, personalization=None,
                 max_iter=10000, tol=1.0e-8, nstart=None, weight='weight'):
        D = klass.graphtype_for_pr(G)
        if len(G) == 0:
            return {}
        H = klass.stochastic(D, weight)
        eq_prob = 1.0 / H.number_of_nodes()
    
        I = klass.start_vector(H, eq_prob, nstart=nstart)
        teleportation = klass.personalization_vector(personalization, eq_prob, H)
        dangle = klass.find_dangle(H)
    
        i = 0
        while True: # power iteration: make up to max_iter iterations
            prev_I = I
            I = dict.fromkeys(prev_I.keys(), 0)
    
            danglesum = alpha * eq_prob * sum(prev_I[dngl_node] for dngl_node in dangle)
    
            for node in I:
                # this matrix multiply looks odd because it is
                # doing a left multiply I^T=prev_I^T*H
                for destination_node in H[node]:
                    I[destination_node] += (
                        alpha * prev_I[node] * H[node][destination_node][weight]
                    )
                I[node] += danglesum + ((1.0 - alpha) * teleportation[node])
    
            # normalize vector
            I = klass.v_normalize(I)
            # check convergence, l1 norm
            if klass.converged(I, prev_I, tol):
                break
            if i > max_iter:
                raise NetworkXError('pagerank: power iteration failed to converge '
                                    'in %d iterations.'%(i-1))
            i += 1

        return I

    @classmethod
    def separate_conditional(klass, H, conditional_links=tuple()):
        labels = nx.get_edge_attributes(H, 'label')
        weights = nx.get_edge_attributes(H, 'weight')
        Hstat = nx.DiGraph()
        Hcond = nx.DiGraph()
        Hstat.add_nodes_from(H.nodes())
        Hcond.add_nodes_from(H.nodes())
        for edgeref in H.edges():
            edge = labels[edgeref]
            weight = weights[edgeref]
            if edge in conditional_links:
                Hcond.add_edge(*edgeref, label=edge, weight=weight)
            else:
                Hstat.add_edge(*edgeref, label=edge, weight=weight)
        return Hstat, Hcond

    @classmethod
    def pagerank_conditional(klass, G, alpha=0.85, personalization=None,
                             max_iter=10000, tol=1.0e-8, nstart=None, error_at_max=True,
                             conditional_links=tuple(), weight='weight',
                             in_degree=False, out_degree=False, through=False):
        D = klass.graphtype_for_pr(G)
        if len(G) == 0:
            return {}

        H = klass.stochastic(D, weight)
        eq_prob = 1.0 / H.number_of_nodes()
    
        I = klass.start_vector(H, eq_prob, nstart=nstart)
        teleportation = klass.personalization_vector(personalization, eq_prob, H)
        dangle = klass.find_dangle(H)

        Hstat, Hcond = klass.separate_conditional(H, conditional_links=conditional_links)
    
        i = 0
        while True: # power iteration: make up to max_iter iterations
            prev_I = I
            I = dict.fromkeys(prev_I.keys(), 0)
    
            danglesum = alpha * eq_prob * sum(prev_I[dngl_node] for dngl_node in dangle)
    
            for node in I:
                for destination_node in Hstat[node]:
                    I[destination_node] += (
                        alpha * prev_I[node] * Hstat[node][destination_node][weight]
                    )

                for destination_node in Hcond[node]:
                    power = 0.0
                    if in_degree:
                        for in_degree_node_to_dest in Hstat.predecessors(destination_node):
                            power += (
                                prev_I[in_degree_node_to_dest] *
                                Hstat[in_degree_node_to_dest][destination_node][weight]
                            )
                    if out_degree:
                        for out_degree_node_to_dest in Hstat[destination_node]:
                            power += (
                                prev_I[out_degree_node_to_dest] *
                                Hstat[destination_node][out_degree_node_to_dest][weight]
                            )
                    if through:
                        pass
                    I[destination_node] += (
                        alpha * power * Hcond[node][destination_node][weight]
                    )

                I[node] += danglesum + ((1.0 - alpha) * teleportation[node])
    
            # normalize vector
            I = klass.v_normalize(I)
            # check convergence, l1 norm
            if klass.converged(I, prev_I, tol):
                break
            if i > max_iter:
                if error_at_max:
                    raise NetworkXError('pagerank: power iteration failed to converge '
                                        'in %d iterations.'%(i-1))
                else:
                    print('pagerank: power iteration failed to converge '
                          'in %d iterations.'%(i-1))
                    break
            i += 1

        return I
