# omnimrz\__init__.py
from .extractor import OmniMRZ
from .parser import parse_mrz_fields
from .validation import (
    structural_mrz_validation,
    checksum_mrz_validation,
    logical_mrz_validation,
)

__all__ = [
    "OmniMRZ",
    "parse_mrz_fields",
    "structural_mrz_validation",
    "checksum_mrz_validation",
    "logical_mrz_validation",
]

__version__ = "0.1.0"
