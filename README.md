# OmniMRZ

OmniMRZ is a fast, production-ready Python library for extracting, parsing, and validating
Machine Readable Zones (MRZ) from passports and ID documents using PaddleOCR.

## Features

- MRZ detection and extraction from images
- Supports TD3 (passport) format
- Checksum validation (ICAO 9303)
- Logical and structural validation
- Clean Python API

## Installation

```bash
pip install omnimrz
```
Note: PaddleOCR requires additional system dependencies.
Please ensure PaddlePaddle installs correctly on your platform.
```bash
pip install paddleocr
pip install paddle paddle
```
or if that fails then run
```bash
python -m pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

# Quick Usage
```bash
from omnimrz import OmniMRZ
from omnimrz import structural_mrz_validation, checksum_mrz_validation, parse_mrz_fields

extractor = OmniMRZ()

result = extractor.get_details("passport.jpg")
print(result)

struct = structural_mrz_validation(result)

if struct["status"] == "PASS":
    checksum = checksum_mrz_validation(result, struct["mrz_type"])
    parsed = parse_mrz_fields(result, struct["mrz_type"])
    print(parsed)
```
# Output Example
```
{
  "status": "PARSED",
  "data": {
    "document_type": "P",
    "issuing_country": "USA",
    "surname": "DOE",
    "given_names": "JOHN",
    "document_number": "123456789",
    "nationality": "USA",
    "date_of_birth": "1990-01-01",
    "gender": "M",
    "expiry_date": "2030-01-01"
  }
}
```