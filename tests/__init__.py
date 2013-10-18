# encoding: utf-8

from attest import Tests
from .nodeprovider import (
    nameprovider_unit, kakasi_unit,
    nodemodel_unit,
)


tests = Tests(
    [
        nameprovider_unit,
        kakasi_unit,
        nodemodel_unit,
    ]
)
