# API Reference

Complete documentation of OmniMRZ's public methods and response formats.

## OmniMRZ Class

The main class for MRZ extraction and validation.

### Constructor

```python
OmniMRZ(lang="en")
```

**Parameters:**
- `lang` (str, optional): Language code for OCR. Default: "en" (English)
  - Supports PaddleOCR language codes: "ch", "en", "ar", "ja", "ko", etc.

**Returns:** OmniMRZ instance

**Example:**
```python
from omnimrz import OmniMRZ

# English OCR
omni = OmniMRZ()

# Chinese OCR
omni = OmniMRZ(lang="ch")
```

---

## Methods

### process(image)

Full MRZ extraction and validation pipeline in a single call.

**Syntax:**
```python
result = omni.process(image)
```

**Parameters:**
- `image` (str or numpy.ndarray): 
  - File path to image (str): "path/to/passport.jpg"
  - OpenCV image array (numpy.ndarray): `cv2.imread("image.jpg")`

**Returns:** dict with complete MRZ analysis

**Response Structure:**
```json
{
  "extraction": {
    "status": "SUCCESS(extraction of mrz) | FAILURE",
    "status_message": "Error description (if FAILURE)",
    "line1": "MRZ line 1 (44 chars)",
    "line2": "MRZ line 2 (44 chars)"
  },
  "structural_validation": {
    "status": "PASS | FAIL | SKIPPED",
    "mrz_type": "TD3",
    "errors": []
  },
  "checksum_validation": {
    "status": "PASS | FAIL | SKIPPED",
    "errors": ["CHECKSUM_FAIL"] or []
  },
  "parsed_data": {
    "status": "PARSED | SKIPPED | PARSE_ERROR",
    "data": {
      "document_type": "P",
      "issuing_country": "GBR",
      "surname": "SURNAME",
      "given_names": "GIVENNAMES",
      "document_number": "123456789",
      "nationality": "GBR",
      "date_of_birth": "1995-05-20",
      "gender": "M",
      "expiry_date": "2025-04-22",
      "personal_number": ""
    }
  },
  "logical_validation": {
    "status": "PASS | FAIL | SKIPPED",
    "errors": ["DOCUMENT_EXPIRED"] or []
  },
  "screenshot_detection": {
    "status": "PASS | WARNING",
    "is_screenshot": false,
    "score": 0,
    "confidence": 0.0,
    "reasons": []
  }
}
```

**Example:**
```python
import json
from omnimrz import OmniMRZ

omni = OmniMRZ()
result = omni.process("uk_passport.jpg")

print(json.dumps(result, indent=2))
```

---

### get_details(image)

Extract MRZ text without validation. Useful for debugging or custom validation pipelines.

**Syntax:**
```python
extraction_result = omni.get_details(image)
```

**Parameters:**
- `image` (str or numpy.ndarray): File path or image array

**Returns:** dict with extraction only

**Response Structure:**
```json
{
  "status": "SUCCESS(extraction of mrz) | FAILURE",
  "status_message": "Error message if failed",
  "line1": "MRZ line 1",
  "line2": "MRZ line 2"
}
```

**Example:**
```python
from omnimrz import OmniMRZ

omni = OmniMRZ()
extraction = omni.get_details("passport.jpg")

if extraction["status"] == "SUCCESS(extraction of mrz)":
    print(f"Line 1: {extraction['line1']}")
    print(f"Line 2: {extraction['line2']}")
else:
    print(f"Failed: {extraction['status_message']}")
```

---

## Response Fields Reference

### Extraction Status

**SUCCESS(extraction of mrz)**
- MRZ successfully extracted from image

**FAILURE**
- Image could not be loaded or no MRZ detected
- Check `status_message` for specific error

### Structural Validation Status

**PASS**
- MRZ format is valid (44 characters per line)
- Document type identified (TD3)

**FAIL**
- MRZ format invalid (incorrect line length)
- Common error: `BAD_LENGTH`

**SKIPPED**
- Extraction failed, validation skipped

### Checksum Validation Status

**PASS**
- All ICAO-9303 checksums verified
- Document number checksum valid
- Date of birth checksum valid
- Expiry date checksum valid
- Composite checksum valid

**FAIL**
- One or more checksums failed
- Error: `CHECKSUM_FAIL` indicates which field failed

**SKIPPED**
- Unsupported MRZ type or extraction failed

### Parsed Data Status

**PARSED**
- MRZ fields successfully extracted and structured
- Access via `data` dict

**PARSE_ERROR**
- Failed to parse MRZ fields
- Check `error` field for details

**SKIPPED**
- Structural validation failed

### Logical Validation Status

**PASS**
- Document is valid (not expired, reasonable dates, etc.)

**FAIL**
- Logical errors detected
- Common errors:
  - `DOCUMENT_EXPIRED`: Expiry date is in the past

**SKIPPED**
- Parsing failed or unsupported MRZ type

### Screenshot Detection Status

**PASS**
- Image is not a screenshot (or confidence is low)

**WARNING**
- Image detected as screenshot
- Score, confidence, and reasons provided for investigation

## Common Usage Patterns

### Validate a Single Document

```python
from omnimrz import OmniMRZ

omni = OmniMRZ()
result = omni.process("passport.jpg")

# Check if all validations passed
is_valid = (
    result["extraction"]["status"] == "SUCCESS(extraction of mrz)" and
    result["structural_validation"]["status"] == "PASS" and
    result["checksum_validation"]["status"] == "PASS" and
    result["logical_validation"]["status"] == "PASS" and
    not result["screenshot_detection"]["is_screenshot"]
)

if is_valid:
    print("Document is valid!")
    print(f"Name: {result['parsed_data']['data']['given_names']} {result['parsed_data']['data']['surname']}")
else:
    print("Document validation failed")
```

### Process Multiple Images

```python
import os
from omnimrz import OmniMRZ

omni = OmniMRZ()
image_dir = "passport_images/"

for filename in os.listdir(image_dir):
    if filename.endswith((".jpg", ".png")):
        path = os.path.join(image_dir, filename)
        result = omni.process(path)
        
        if result["extraction"]["status"] == "SUCCESS(extraction of mrz)":
            print(f"{filename}: ✓ MRZ extracted")
        else:
            print(f"{filename}: ✗ Failed to extract")
```

### Extract Structured Data Only

```python
from omnimrz import OmniMRZ

omni = OmniMRZ()
result = omni.process("passport.jpg")

if result["parsed_data"]["status"] == "PARSED":
    data = result["parsed_data"]["data"]
    print(f"Name: {data['given_names']} {data['surname']}")
    print(f"DOB: {data['date_of_birth']}")
    print(f"Expiry: {data['expiry_date']}")
