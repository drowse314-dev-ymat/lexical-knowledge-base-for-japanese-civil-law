# encoding: utf-8

from attest import Tests
from .nodeprovider import (
    nameprovider_unit, kakasi_unit,
    nodeprovider_unit,
)
from .nodemodel import (
    rdflib_nodemodel_unit,
)
from .relationprovider import (
    relationchecker_unit,
    relationprovider_unit,
)


tests = Tests(
    [
        nameprovider_unit,
        kakasi_unit,
        nodeprovider_unit,
        rdflib_nodemodel_unit,
        relationchecker_unit,
        relationprovider_unit,
    ]
)
