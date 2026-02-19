# Troubleshooting Guide

Common issues and solutions when using OmniMRZ.

## Installation Issues

### Issue: `ModuleNotFoundError: No module named 'paddleocr'`

**Symptom:**
```
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    from omnimrz import OmniMRZ
ModuleNotFoundError: No module named 'paddleocr'
```

**Solutions:**

1. **Install PaddleOCR explicitly:**
   ```bash
   pip install paddleocr paddlepaddle
   ```

2. **If installation fails on Windows, try:**
   ```bash
   python -m pip install paddlepaddle==2.6.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
   pip install paddleocr
   ```

3. **On macOS with Apple Silicon:**
   ```bash
   # Install with correct architecture
   pip install paddlepaddle paddleocr --no-cache-dir
   ```

4. **If you're in a virtual environment, make sure it's activated:**
   ```bash
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   pip install omnimrz
   ```

---

### Issue: `ImportError: DLL load failed` (Windows)

**Symptom:**
```
ImportError: DLL load failed while importing paddle._core: The specified module could not be found.
```

**Solutions:**

1. **Install Visual C++ Runtime:**
   - Download from: https://support.microsoft.com/en-us/help/2977003
   - Install "Visual C++ Redistributable for Visual Studio 2022"

2. **Use conda instead of pip:**
   ```bash
   conda create -n omnimrz python=3.10
   conda activate omnimrz
   conda install paddlepaddle paddleocr -c paddle
   pip install omnimrz
   ```

3. **Update pip and setuptools:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install omnimrz
   ```

---

### Issue: `ModuleNotFoundError: No module named 'cv2'` (OpenCV)

**Symptom:**
```
ModuleNotFoundError: No module named 'cv2'
```

**Solution:**
```bash
pip install opencv-python
```

---

## Extraction Issues

### Issue: "No MRZ found" / Extraction Fails

**Symptom:**
```json
{
  "extraction": {
    "status": "FAILURE",
    "status_message": "No MRZ found"
  }
}
```

**Possible Causes & Solutions:**

1. **Image quality is too poor:**
   - Use high-quality, well-lit photos (at least 300 DPI)
   - Avoid blurry, rotated, or partially visible passports
   - Test with a different passport image first

2. **MRZ zone not visible:**
   - Ensure the bottom 50% of the passport is visible in the photo
   - The two MRZ lines must be in the frame
   - Example: Passport must be photographed straight-on

3. **Image format not supported:**
   - Supported: JPG, PNG, JPEG
   - Convert other formats: GIF → PNG, BMP → JPG, etc.
   - Ensure file is not corrupted:
     ```python
     import cv2
     image = cv2.imread("passport.jpg")
     if image is None:
         print("Image file is corrupted or invalid")
     ```

4. **Using a screenshot (detected by OmniMRZ):**
   - Capture real photos, not screenshots
   - Screenshots have watermarks and reduced quality
   - Check `screenshot_detection` in result

5. **Document type not supported:**
   - Currently supports: TD3 (Passport)
   - Coming soon: TD1/TD2 (ID cards)

**Debug Steps:**
```python
from omnimrz import OmniMRZ
import cv2

omni = OmniMRZ()

# Check image loads correctly
image = cv2.imread("passport.jpg")
if image is None:
    print("Image cannot be loaded")
    exit()

print(f"Image shape: {image.shape}")

# Try extraction
result = omni.get_details("passport.jpg")
if result["status"] == "FAILURE":
    print(f"Error: {result['status_message']}")
    print("Suggested: Use higher quality image or check if MRZ is visible")
```

---

## Validation Issues

### Issue: Checksum Validation Fails

**Symptom:**
```json
{
  "checksum_validation": {
    "status": "FAIL",
    "errors": ["CHECKSUM_FAIL"]
  }
}
```

**Possible Causes:**

1. **OCR misread a character:**
   - Common confusions: O→0, S→5, B→8, Z→2, I→1
   - OmniMRZ auto-corrects these, but if multiple errors exist, checksums fail
   - Solution: Use higher quality image

2. **Forged or altered document:**
   - Checksum indicates document is not authentic
   - Don't accept this document
   - Report to KYC/compliance team

3. **Partially corrupted image:**
   - One character in the MRZ is unreadable
   - Solution: Retake the photo with better lighting

**Debug:**
```python
result = omni.process("passport.jpg")

if result["checksum_validation"]["status"] == "FAIL":
    print("Checksum failed")
    print("Raw MRZ:")
    print(f"  Line 1: {result['extraction']['line1']}")
    print(f"  Line 2: {result['extraction']['line2']}")
    print("This indicates:")
    print("  1. Image quality issue (blurry/dark), OR")
    print("  2. Document is forged/altered, OR")
    print("  3. Multiple OCR errors in same field")
```

---

### Issue: Structural Validation Fails

**Symptom:**
```json
{
  "structural_validation": {
    "status": "FAIL",
    "mrz_type": null,
    "errors": ["BAD_LENGTH"]
  }
}
```

**Possible Causes:**

1. **MRZ lines not exactly 44 characters:**
   - TD3 passport must have exactly 44 chars per line
   - Check extraction output
   - Solution: Ensure full MRZ is captured in image

2. **OCR extracted wrong text:**
   - OCR may have missed part of MRZ
   - Lines may be clustered incorrectly
   - Solution: Retake photo, ensure entire MRZ is visible

**Debug:**
```python
result = omni.get_details("passport.jpg")

if result["status"] == "SUCCESS(extraction of mrz)":
    line1 = result["line1"]
    line2 = result["line2"]
    print(f"Line 1 length: {len(line1)} (expected: 44)")
    print(f"Line 2 length: {len(line2)} (expected: 44)")
    print(f"Line 1: '{line1}'")
    print(f"Line 2: '{line2}'")
```

---

### Issue: Document Shows as Expired

**Symptom:**
```json
{
  "logical_validation": {
    "status": "FAIL",
    "errors": ["DOCUMENT_EXPIRED"]
  }
}
```

**Solution:**

This is expected for expired passports. If document is expired:
- Do not accept for KYC if your regulations require valid documents
- Check if your KYC process allows expired documents during grace periods
- Document owner should renew passport

**Check expiry date:**
```python
result = omni.process("passport.jpg")

if "DOCUMENT_EXPIRED" in result["logical_validation"]["errors"]:
    expiry = result["parsed_data"]["data"]["expiry_date"]
    print(f"Document expired on: {expiry}")
    print("Request user to upload valid passport")
```

---

## Performance Issues

### Issue: Processing is Too Slow

**Symptom:** Takes >2 seconds per document

**Solutions:**

1. **First run loads models (slow):**
   - First-time use downloads PaddleOCR models
   - Second run will be faster
   - Models cached in `~/.paddleocr/` directory

2. **Reuse OmniMRZ instance:**
   - Bad (slow):
     ```python
     for image in images:
         omni = OmniMRZ()  # Reinitializes each time
         result = omni.process(image)
     ```
   - Good (fast):
     ```python
     omni = OmniMRZ()  # Initialize once
     for image in images:
         result = omni.process(image)
     ```

3. **Use GPU acceleration:**
   ```python
   from omnimrz import OmniMRZ
   
   # PaddleOCR will auto-detect GPU if available
   omni = OmniMRZ()
   
   # Check if GPU detected
   import paddle
   print(f"Using GPU: {paddle.device.is_compiled_with_cuda()}")
   ```

4. **Process in parallel for batch operations:**
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   omni = OmniMRZ()
   
   def process_image(path):
       return omni.process(path)
   
   image_paths = ["passport1.jpg", "passport2.jpg", ...]
   
   with ThreadPoolExecutor(max_workers=4) as executor:
       results = list(executor.map(process_image, image_paths))
   ```

---

## Screenshot Detection Issues

### Issue: Valid Passport Detected as Screenshot

**Symptom:**
```json
{
  "screenshot_detection": {
    "status": "WARNING",
    "is_screenshot": true
  }
}
```

**Possible Causes:**

1. **Passport has hologram/security features:**
   - Modern passports have reflective elements
   - These may trigger false positives
   - Check confidence score

2. **Low image quality:**
   - Blurry photos may appear screenshot-like
   - Solution: Retake with better lighting

**Handle screenshot warnings:**
```python
result = omni.process("passport.jpg")

if result["screenshot_detection"]["is_screenshot"]:
    confidence = result["screenshot_detection"]["confidence"]
    print(f"Screenshot detection confidence: {confidence}%")
    
    if confidence < 50:
        print("Low confidence - likely a real photo")
        print("Likely cause: Hologram/security features")
    else:
        print("High confidence - likely a screenshot")
        print("Request user to photograph document")
```

---

## API / Integration Issues

### Issue: `TypeError: argument of type 'str' is not iterable`

**Symptom:**
```
TypeError: argument of type 'str' is not iterable
```

**Solution:** You passed a file path string instead of loading the image:

```python
# Wrong:
import cv2
result = omni.process("passport.jpg")  # Works fine actually

# If you get error, check image loading:
image = cv2.imread("passport.jpg")
if image is None:
    print("Image not found")
else:
    result = omni.process(image)  # Pass numpy array
```

---

### Issue: `FileNotFoundError: Image file not found`

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'passport.jpg'
```

**Solution:**

1. **Use absolute path:**
   ```python
   import os
   
   image_path = os.path.abspath("passport.jpg")
   result = omni.process(image_path)
   ```

2. **Check file exists:**
   ```python
   import os
   
   if os.path.exists("passport.jpg"):
       result = omni.process("passport.jpg")
   else:
       print("File not found")
   ```

3. **Handle different working directories:**
   ```python
   import os
   
   # Get script directory
   script_dir = os.path.dirname(os.path.abspath(__file__))
   image_path = os.path.join(script_dir, "images", "passport.jpg")
   result = omni.process(image_path)
   ```

---

## Data Extraction Issues

### Issue: Extracted Names Have Strange Characters

**Symptom:**
```python
{
  "given_names": "JUAN<MARIA",
  "surname": "GARCIA <<<<<<"
}
```

**Explanation:** 
- MRZ uses `<` (less-than) as filler character
- OmniMRZ automatically cleans these in parsed data
- If you see them, it means parsing had issues

**Solution:**
```python
name = result["parsed_data"]["data"]["given_names"]
# Clean remaining special chars
clean_name = name.replace("<", " ").strip()
```

---

### Issue: Dates Parsed Incorrectly

**Symptom:**
```json
{
  "date_of_birth": "1920-05-20",
  "expiry_date": null
}
```

**Causes:**

1. **Century boundary ambiguity:**
   - Years 00-20: interpreted as 2000-2020
   - Years 21-99: interpreted as 1921-1999
   - Example: 95 = 1995 (past), 05 = 2005 (future)

2. **Invalid date format:**
   - Checksum failed, date field corrupted
   - OmniMRZ returns `null` for unparseable dates

**Debug:**
```python
result = omni.process("passport.jpg")
line2 = result["extraction"]["line2"]

dob_raw = line2[13:19]  # YYMMDD
expiry_raw = line2[21:27]  # YYMMDD

print(f"Raw DOB: {dob_raw}")
print(f"Raw Expiry: {expiry_raw}")
print(f"Parsed DOB: {result['parsed_data']['data']['date_of_birth']}")
print(f"Parsed Expiry: {result['parsed_data']['data']['expiry_date']}")
```

---

## Reporting Bugs

If you encounter issues not covered here:

1. **Check GitHub Issues:** https://github.com/AzwadFawadHasan/OmniMRZ/issues

2. **Collect debug information:**
   ```python
   from omnimrz import OmniMRZ
   import json
   
   omni = OmniMRZ()
   result = omni.process("problematic_image.jpg")
   
   # Save full output
   with open("debug_output.json", "w") as f:
       json.dump(result, f, indent=2)
   ```

3. **Include in bug report:**
   - Sample image (if possible)
   - Full error message
   - Python version: `python --version`
   - PaddleOCR version: `pip show paddleocr`
   - OmniMRZ version: `pip show omnimrz`
   - Operating system

4. **Create issue on GitHub with:**
   - Title: Clear one-liner
   - Description: What you tried, what happened
   - Logs: Full traceback
   - Environment: Python, OS, package versions

---

## Performance Benchmarks

Expected performance on modern hardware:

- **First-time initialization:** 3-5 seconds (model download)
- **Subsequent processing:** 200-500ms per document
- **GPU acceleration:** 100-200ms per document
- **Batch processing:** 200ms/document with 4 workers

---

## Getting Further Help

- GitHub Issues: https://github.com/AzwadFawadHasan/OmniMRZ/issues
- Read API Reference: [../docs/api-reference.md](./api-reference.md)
- Technical details: [../docs/validation-explained.md](./validation-explained.md)
- KYC integration: [../docs/kyc-integration.md](./kyc-integration.md)
