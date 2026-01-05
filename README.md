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
  "extraction": {
    "status": "SUCCESS(extraction of mrz)",
    "line1": "P<GBRPUDARSAN<<HENERT<<<<<<<<<<<<<<<<<<<<<<<",
    "line2": "7077979792GBR9505209M1704224<<<<<<<<<<<<<<00"
  },
  "structural_validation": {
    "status": "PASS",
    "mrz_type": "TD3",
    "errors": []
  },
  "checksum_validation": {
    "status": "PASS",
    "errors": []
  },
  "parsed_data": {
    "status": "PARSED",
    "data": {
      "document_type": "P",
      "issuing_country": "GBR",
      "surname": "PUDARSAN",
      "given_names": "HENERT",
      "document_number": "707797979",
      "nationality": "GBR",
      "date_of_birth": "1995-05-20",
      "gender": "M",
      "expiry_date": "2017-04-22",
      "personal_number": ""
    }
  },
  "logical_validation": {
    "status": "FAIL",
    "errors": [
      "DOCUMENT_EXPIRED"
    ]
  }
}
```

## misc
![Visitor Count](https://visitor-badge.laobi.icu/badge?page_id=AzwadFawadHasan.OmniMRZ)
