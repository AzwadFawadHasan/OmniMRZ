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

omni = OmniMRZ()
result = omni.process("ukpassport.jpg")

print(result)
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

## misc
![Visitor Count](https://visitor-badge.laobi.icu/badge?page_id=AzwadFawadHasan.OmniMRZ)
