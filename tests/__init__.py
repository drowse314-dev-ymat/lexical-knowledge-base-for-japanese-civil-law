# encoding: utf-8

from attest import Tests
from .nodeprovider import nodeprovider_unit, kakasi_unit


tests = Tests(
    [
        nodeprovider_unit,
        kakasi_unit,
    ]
)
