# Getting Started with OmniMRZ

This guide will help you install OmniMRZ and process your first passport image with full MRZ validation.

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Install

The simplest way to get started:

```bash
pip install omnimrz
```

That's it! No complex system dependencies or PATH configurations required.

### Verify Installation

Test your installation:

```python
from omnimrz import OmniMRZ

omni = OmniMRZ()
print("OmniMRZ installed successfully!")
```

### Installing from Source (Optional)

If you want to contribute or use the latest development version:

```bash
git clone https://github.com/AzwadFawadHasan/OmniMRZ.git
cd OmniMRZ
pip install -e .
```

## Your First MRZ Extraction

### Basic Usage

```python
from omnimrz import OmniMRZ

# Initialize OmniMRZ
omni = OmniMRZ()

# Process a passport image
result = omni.process("path/to/passport.jpg")

# Print results
import json
print(json.dumps(result, indent=2))
```

### Sample Output

```json
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
    "errors": ["DOCUMENT_EXPIRED"]
  },
  "screenshot_detection": {
    "status": "PASS",
    "is_screenshot": false,
    "score": 3,
    "confidence": 30.0,
    "reasons": ["Low ELA: 0.38"]
  }
}
```

## Understanding the Pipeline

OmniMRZ processes documents through 5 stages:

1. **Extraction**: Detects and extracts MRZ text from the image using PaddleOCR
2. **Structural Validation**: Verifies the MRZ format complies with ICAO-9303
3. **Checksum Validation**: Validates all checksums using ICAO-9303 algorithm
4. **Parsing**: Extracts structured data (name, DOB, nationality, etc.)
5. **Logical Validation**: Checks for expired documents, impossible dates, etc.

## Supported Document Types

Currently, OmniMRZ supports:

- **TD3**: Passport format (44 characters per line)
- **TD1/TD2**: ID card formats (upcoming support)

## Working with Different Languages

OmniMRZ supports multiple languages for initial OCR. Currently optimized for:

```python
# Default English
omni = OmniMRZ(lang="en")

# For other languages, pass the language code
omni = OmniMRZ(lang="ch")  # Chinese
omni = OmniMRZ(lang="ar")  # Arabic
```

## Next Steps

- Read the [API Reference](./api-reference.md) for detailed methods
- Understand [Validation Explained](./validation-explained.md) for technical details
- Check [KYC Integration](./kyc-integration.md) for production use
- See [Troubleshooting](./troubleshooting.md) if you encounter issues
