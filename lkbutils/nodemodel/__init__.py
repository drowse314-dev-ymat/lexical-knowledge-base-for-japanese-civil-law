# encoding: utf-8

from .rdflib_model import RDFLib


def rdflib_to_networkx(rdflib_graph):
    """Proxy to RDFLib().to_networkx."""
    model = RDFLib()
    return model.to_networkx(rdflib_graph)
