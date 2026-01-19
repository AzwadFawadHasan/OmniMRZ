# OmniMRZ — Python MRZ Extraction & Validation Library for Passport OCR and KYC


<div align="center">

[![License](https://img.shields.io/badge/license-AGPL%203.0-34D058?color=blue)](https://github.com/AzwadFawadHasan/OmniMRZ/LICENSE)
[![Downloads](https://static.pepy.tech/badge/OmniMRZ)](https://pypistats.org/packages/omnimrz)
![Python](https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=959DA5)
[![CodeQL](https://github.com/AzwadFawadHasan/OmniMRZ/actions/workflows/codeql.yml/badge.svg)](https://github.com/AzwadFawadHasan/OmniMRZ/actions/workflows/codeql.yml)
[![PyPI](https://img.shields.io/pypi/v/OmniMRZ.svg?logo=pypi&logoColor=959DA5&color=blue)](https://pypi.org/project/OmniMRZ/)

<a href="https://github.com/AzwadFawadHasan/OmniMRZ/" target="_blank">
    <img src="https://raw.githubusercontent.com/AzwadFawadHasan/OmniMRZ/main/omni_mrz_logo.jpg" target="_blank" />
</a>

**OmniMRZ** is an open-source **Python library for Machine Readable Zone (MRZ) extraction, parsing, and ICAO-9303 validation** from passport and ID images, built for OCR, KYC, and identity verification systems.

It is a production-grade MRZ extraction and validation engine designed for high-accuracy KYC, identity verification, and document intelligence pipelines.

Unlike simple MRZ readers, OmniMRZ evaluates whether an MRZ is structurally correct, cryptographically valid, and logically plausible.

### Typical Use Cases

🛂 Passport and ID card OCR pipelines  
🏦 KYC / AML identity verification systems  
✈️ Border control and immigration preprocessing  
📄 Document digitization and archiving  
🔐 Authentication and onboarding workflows  


⭐ Show Your Support
If OmniMRZ helped you or saved development time:
👉 Please consider starring the repository
It helps visibility and motivates continued development 


[Features](#features) 
<!-- [Built With](#built-with) •
[Prerequisites](#prerequisites) • -->
[Installation](#installation) 
<!-- [Example](#example) •
[Wiki](#wiki) •
[ToDo](#todo) • -->
<!-- [Contributing](- Contributing) -->
[Contributing](#-contributing)



</div>

## Why OmniMRZ?

Unlike basic MRZ readers, OmniMRZ provides **end-to-end MRZ quality assurance**:

- Combines OCR, structural validation, checksum verification, and logical consistency checks  
- Fully compliant with **ICAO 9303**  
- Designed for **production KYC and identity verification systems**  
- Robust against OCR noise and partially corrupted MRZ lines 

## Features
### At a glance
- MRZ detection and extraction from images
- Supports TD3 (passport) format
- Checksum validation (ICAO 9303)
- Logical and structural validation
- Clean Python API

# Detailed features
#### 🔍 MRZ Extraction
- PaddleOCR-based MRZ text extraction (robust on mobile & noisy images)
- Intelligent MRZ line clustering & reconstruction
- Automatic MRZ type detection (TD1 / TD2 / TD3)
- OCR noise filtering & MRZ-safe character normalization
- Works even with partially corrupted or misaligned MRZs

#### 🧱 Structural Validation (ICAO 9303)
- Exact line-length enforcement
- Strict MRZ format verification
- Field-level structural checks
- Early-exit gating for invalid layouts

#### 🔢 Checksum Validation

- Fully ICAO-9303 compliant checksum algorithm
- Field-level validation:
- Document number
- Date of birth
- Expiry date
- Composite checksum
- OCR-error tolerant digit correction (O→0, S→5, B→8, etc.)
- Detailed checksum failure diagnostics

#### 🧠 Logical & Semantic Validation

- Expired document detection
- Future date-of-birth detection
- Implausible age detection
- DOB ≥ expiry detection
- Gender value validation (M, F, X, <)
- Cross-field consistency signals (issuer vs nationality)

#### 📤 Output

- Clean MRZ text
- Structured JSON
- Deterministic pass / fail / warning signals
- Human-readable error messages

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
```python
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
## Citing OmniMRZ

If you use OmniMRZ in academic research or publications, please consider citing this repository:


## Contributing 

Contributions are welcome!🤝

1. Fork the repository
2. Create your feature branch
```bash
git checkout -b feature/amazing-feature
```
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

## Keywords

MRZ extraction, passport OCR, machine readable zone, ICAO 9303, MRZ parser, Python OCR, identity verification, KYC automation, document intelligence, ID card scanning, border control OCR

## misc
![Visitor Count](https://visitor-badge.laobi.icu/badge?page_id=AzwadFawadHasan.OmniMRZ)
