import cv2
import re
import numpy as np
from paddleocr import PaddleOCR

class FastMRZ:
    def __init__(self, lang="en"):
        print("Initializing PaddleOCR (stable 3.x)...")
        self.ocr = PaddleOCR(lang=lang)
        print("PaddleOCR initialized OK")

    # ---------------------------------------------------------
    # 1. Image Preprocessing
    # ---------------------------------------------------------
    def _crop_mrz_zone(self, image):
        h, w = image.shape[:2]
        return image[int(h * 0.50):h, 0:w]

    def _preprocess(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Upscale to ensure characters are large enough for OCR
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        # slight blur to reduce noise
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # ---------------------------------------------------------
    # 2. Text Normalization & Clustering
    # ---------------------------------------------------------
    def _normalize(self, text):
        text = text.upper().strip()
        text = text.replace(" ", "") # standard OCR fix
        # Remove anything that isn't A-Z, 0-9, or <
        text = re.sub(r"[^A-Z0-9<]", "", text)
        return text

    def _cluster_text_to_lines(self, ocr_results, y_threshold=20):
        if not ocr_results or not ocr_results[0]:
            return []

        raw_items = []
        for box, text, score in zip(ocr_results[0]["dt_polys"], ocr_results[0]["rec_texts"], ocr_results[0]["rec_scores"]):
            y_center = sum(p[1] for p in box) / 4
            x_center = sum(p[0] for p in box) / 4
            raw_items.append({"text": text, "y": y_center, "x": x_center})

        raw_items.sort(key=lambda k: k['y'])

        lines = []
        current_line_items = []
        for item in raw_items:
            if not current_line_items:
                current_line_items.append(item)
            else:
                avg_y = sum(i['y'] for i in current_line_items) / len(current_line_items)
                if abs(item['y'] - avg_y) < y_threshold:
                    current_line_items.append(item)
                else:
                    lines.append(current_line_items)
                    current_line_items = [item]
        if current_line_items:
            lines.append(current_line_items)

        merged_lines = []
        for line_items in lines:
            line_items.sort(key=lambda k: k['x'])
            full_text = "".join([i['text'] for i in line_items])
            merged_lines.append(self._normalize(full_text))
        
        return merged_lines

    # ---------------------------------------------------------
    # 3. Intelligent Alignment (NEW)
    # ---------------------------------------------------------
    def _align_and_fix_line(self, text, target_length, is_line1):
        """
        Smartly aligns the MRZ line. If extra junk is at the start, it removes it.
        If junk is at the end, it removes it.
        """
        if len(text) == target_length:
            return text

        # If too short, pad with <
        if len(text) < target_length:
            return text + ("<" * (target_length - len(text)))

        # If too long, we need to find the "start" of the MRZ
        # Line 1 usually starts with P<, I<, A<, C<
        # Line 2 usually starts with a letter or digit followed by digits
        if is_line1:
            match = re.search(r"[PIACV][A-Z0-9<]", text)
            if match:
                start_idx = match.start()
                text = text[start_idx:]
        
        # After left-trimming, if still too long, trim the right
        return text[:target_length]

    # ---------------------------------------------------------
    # 4. MRZ Extraction Logic
    # ---------------------------------------------------------
    def _extract_mrz(self, image, show_image=0):
        roi = self._crop_mrz_zone(image)
        preprocessed = self._preprocess(roi)

        if show_image:
            import matplotlib.pyplot as plt
            import cv2
            plt.figure(figsize=(10, 5))
            plt.imshow(preprocessed)
            plt.axis('off')  # Hide the x and y axes
            plt.show()
        
        result = self.ocr.predict(preprocessed)
        merged_rows = self._cluster_text_to_lines(result)

        # Filter short garbage
        candidate_rows = [row for row in merged_rows if len(row) > 10]

        if len(candidate_rows) < 2:
            return None

        # Logic: Look for the last two lines that resemble MRZ structure
        line1 = ""
        line2 = ""
        
        # Taking the last two valid-looking lines is usually safest for Passport/IDs
        # unless there is noise at the absolute bottom
        if len(candidate_rows) >= 2:
            line1 = candidate_rows[-2]
            line2 = candidate_rows[-1]

        # Determine Likely Type based on Line 1 Start
        target_len = 44 # Default TD3
        if len(line1) > 32 and len(line1) < 40:
            target_len = 36 # TD2
        elif len(line1) <= 32:
            target_len = 30 # TD1

        line1 = self._align_and_fix_line(line1, target_len, is_line1=True)
        line2 = self._align_and_fix_line(line2, target_len, is_line1=False)

        return f"{line1}\n{line2}"

    def get_details(self, image):
        if isinstance(image, str):
            image = cv2.imread(image)
        
        if image is None:
            return {"status": "FAILURE", "status_message": "Image load failed"}

        mrz = self._extract_mrz(image)
        if not mrz:
            return {"status": "FAILURE", "status_message": "No MRZ found"}

        lines = mrz.split("\n")
        return {
            "status": "SUCCESS(extraction of mrz)",
            "line1": lines[0],
            "line2": lines[1]
        }

# ---------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------
def _get_char_value(c: str) -> int:
    """Returns ICAO value for a character."""
    if c.isdigit():
        return int(c)
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A') + 10
    if c == '<':
        return 0
    # Fallback for OCR errors if needed (optional)
    return 0 

def _compute_check_digit(data: str) -> int:
    weights = [7, 3, 1]
    total = 0
    for i, ch in enumerate(data):
        total += _get_char_value(ch) * weights[i % 3]
    return total % 10

def _clean_ocr_digit(char: str) -> str:
    """Fix common OCR digit errors for Check Digits."""
    if char == 'O' or char == 'D' or char == 'Q': return '0'
    if char == 'S': return '5'
    if char == 'B': return '8'
    if char == 'Z': return '2'
    if char == 'I': return '1'
    return char

def _validate_check_digit(data_field, check_digit_char, field_name):
    """
    Computes checksum of data_field and compares with check_digit_char.
    """
    # 1. Clean the check digit (handle OCR O/0 confusion)
    cleaned_cd_char = _clean_ocr_digit(check_digit_char)
    
    # 2. Ensure check digit is actually a digit
    if not cleaned_cd_char.isdigit():
        return f"{field_name}_INVALID_CD_CHAR({check_digit_char})"

    expected_val = int(cleaned_cd_char)
    calculated_val = _compute_check_digit(data_field)

    if expected_val != calculated_val:
        return f"{field_name}_CHECKSUM_FAIL(Exp:{expected_val},Got:{calculated_val})"
    
    return None
from datetime import datetime

# ---------------------------------------------------------
# MRZ PARSING & NORMALIZATION
# ---------------------------------------------------------


from datetime import datetime, date

# ---------------------------------------------------------
# UPDATED PARSING & NORMALIZATION
# ---------------------------------------------------------
from datetime import datetime, date

# ---------------------------------------------------------
# UPDATED PARSING & NORMALIZATION
# ---------------------------------------------------------

def _parse_date_yyMMdd(date_str: str, is_expiry: bool = False):
    """
    Parses YYMMDD into YYYY-MM-DD using smart century inference.
    """
    if not re.match(r"\d{6}", date_str):
        return None

    year_2d = int(date_str[0:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])

    # Get current year last 2 digits (e.g., 26 for 2026)
    current_year_full = datetime.now().year
    current_year_2d = current_year_full % 100

    # Century Logic
    century = 2000
    
    if is_expiry:
        # Expiry Logic: 
        # If year is much smaller than current year (e.g. 60 vs 26), it might be 1960, 
        # but for passports, we usually assume 2000s unless the gap is huge.
        # Threshold: If year is more than 60 years in the past relative to now, assume 1900.
        # Example: Current 26. MRZ 80. (80-26 = 54). likely 1980? 
        # Actually simpler: Expiry is rarely > 10 years in past.
        # If MRZ year is 60-99 and current is 00-40, it's likely 1900s (expired long ago).
        if year_2d > current_year_2d + 50: 
            century = 1900
        else:
            century = 2000
    else:
        # DOB Logic: 
        # If MRZ year > Current Year, it must be 1900s (Time travel not possible).
        # Example: MRZ 99, Current 26 -> 1999.
        # Example: MRZ 10, Current 26 -> 2010.
        if year_2d > current_year_2d:
            century = 1900
        else:
            century = 2000

    full_year = century + year_2d

    try:
        return datetime(full_year, month, day).date().isoformat()
    except ValueError:
        return None

def _clean_name(name: str):
    """
    Converts MRZ name format to human-readable form.
    """
    # Replace single < with space, double << with space (already handled by split usually)
    name = name.replace("<", " ").strip()
    return re.sub(r"\s+", " ", name)

def parse_mrz_fields(mrz_result: dict, mrz_type: str):
    """
    Parses MRZ into structured identity fields.
    """
    if mrz_result.get("status") != "SUCCESS(extraction of mrz)":
        return {"status": "SKIPPED"}

    l1 = mrz_result["line1"]
    l2 = mrz_result["line2"]

    try:
        parsed = {}
        if mrz_type == "TD3":  # Passport
            parsed = {
                "document_type": l1[0:2].replace("<", ""),
                "issuing_country": l1[2:5],
                "surname": _clean_name(l1[5:].split("<<")[0]),
                "given_names": _clean_name(l1[5:].split("<<")[1]) if "<<" in l1[5:] else "",
                "document_number": l2[0:9].replace("<", ""),
                "nationality": l2[10:13],
                "date_of_birth": _parse_date_yyMMdd(l2[13:19], is_expiry=False), # Context: DOB
                "gender": l2[20],
                "expiry_date": _parse_date_yyMMdd(l2[21:27], is_expiry=True),    # Context: Expiry
                "personal_number": l2[28:42].replace("<", "")
            }

        elif mrz_type == "TD2": # ID Card (Common)
            # TD2 Structure:
            # L1: I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<
            # L2: D231458907UTO7408122F1204159<<<<<<<6
            parsed = {
                 "document_type": l1[0:2].replace("<", ""),
                 "issuing_country": l1[2:5],
                 "surname": _clean_name(l1[5:].split("<<")[0]),
                 "given_names": _clean_name(l1[5:].split("<<")[1]) if "<<" in l1[5:] else "",
                 "document_number": l2[0:9].replace("<", ""),
                 "nationality": l2[10:13],
                 "date_of_birth": _parse_date_yyMMdd(l2[13:19], is_expiry=False),
                 "gender": l2[20],
                 "expiry_date": _parse_date_yyMMdd(l2[21:27], is_expiry=True),
                 "personal_number": "" # TD2 "optional data" is at end, but usually not personal #
            }
        
        else:
            return {"status": "UNSUPPORTED_MRZ_TYPE"}

        return {
            "status": "PARSED",
            "data": parsed
        }

    except Exception as e:
        return {
            "status": "PARSE_ERROR",
            "error": str(e)
        }


# ---------------------------------------------------------
# MAIN VALIDATION LOGIC
# ---------------------------------------------------------
def structural_mrz_validation(mrz_result: dict):
    if mrz_result.get("status") != "SUCCESS(extraction of mrz)":
        return {"status": "SKIPPED", "mrz_type": None}

    l1 = mrz_result["line1"]
    l2 = mrz_result["line2"]
    
    errors = []
    mrz_type = None

    if len(l1) == 44 and len(l2) == 44: mrz_type = "TD3"
    elif len(l1) == 36 and len(l2) == 36: mrz_type = "TD2"
    elif len(l1) == 30 and len(l2) == 30: mrz_type = "TD1"
    else: errors.append(f"BAD_LENGTHS: {len(l1)}/{len(l2)}")

    status = "FAIL" if errors else "PASS"
    return {"status": status, "mrz_type": mrz_type, "errors": errors}

def checksum_mrz_validation(mrz_result: dict, mrz_type: str):
    if mrz_result["status"] != "SUCCESS(extraction of mrz)" or not mrz_type:
        return {"status": "SKIPPED", "errors": []}

    line2 = mrz_result["line2"]
    errors = []

    # Helper wrapper to append errors easily
    def check(data, cd_char, name):
        err = _validate_check_digit(data, cd_char, name)
        if err: errors.append(err)

    try:
        if mrz_type == "TD3": # Passport (44 chars)
            # 1. Passport Num (0-9) + CD (9)
            doc_num = line2[0:9]
            doc_cd = line2[9]
            check(doc_num, doc_cd, "DOC_NUM")

            # 2. DOB (13-19) + CD (19)
            dob = line2[13:19]
            dob_cd = line2[19]
            check(dob, dob_cd, "DOB")

            # 3. Expiry (21-27) + CD (27)
            exp = line2[21:27]
            exp_cd = line2[27]
            check(exp, exp_cd, "EXPIRY")

            # 4. Personal Number (28-42) - Note: CD is usually NOT checked individually in composite for strictness, 
            # but composite covers it.
            personal_num = line2[28:42]
            
            # 5. Composite (Final char at 43)
            # Data = DocNum + DocCD + DOB + DOBCD + Exp + ExpCD + PersonalNum + PersonalCD(if any)
            # Simplest Composite: line2[0:10] + line2[13:20] + line2[21:43]
            composite_data = line2[0:10] + line2[13:20] + line2[21:43]
            composite_cd = line2[43]
            check(composite_data, composite_cd, "COMPOSITE")

        elif mrz_type == "TD2": # ID Card (36 chars)
            # 1. Doc Num (0-9) + CD (9)
            doc_num = line2[0:9]
            doc_cd = line2[9]
            check(doc_num, doc_cd, "DOC_NUM")

            # 2. DOB (13-19) + CD (19)
            dob = line2[13:19]
            dob_cd = line2[19]
            check(dob, dob_cd, "DOB")

            # 3. Expiry (21-27) + CD (27)
            exp = line2[21:27]
            exp_cd = line2[27]
            check(exp, exp_cd, "EXPIRY")

            # 4. Composite (Usually at 35) represents (Doc+CD + DOB+CD + Exp+CD + Optional)
            # Indices: 0-10, 13-20, 21-35. 
            composite_data = line2[0:10] + line2[13:20] + line2[21:35]
            composite_cd = line2[35]
            check(composite_data, composite_cd, "COMPOSITE")

    except IndexError:
        # This handles cases where lines are structurally OK length-wise 
        # but somehow we accessed out of bounds (unlikely with fixed lengths)
        errors.append("INDEX_ERROR_DURING_CHECKSUM")
    except Exception as e:
        errors.append(f"UNEXPECTED_ERROR: {str(e)}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors
    }


# ---------------------------------------------------------
# Logical VALIDATION LOGIC
# ---------------------------------------------------------
from datetime import date

MAX_HUMAN_AGE = 125
MAX_VALIDITY_YEARS = 20

def _years_between(d1: date, d2: date) -> int:
    return d2.year - d1.year - ((d2.month, d2.day) < (d1.month, d1.day))

def _only_mrz_chars(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9<]*", value))
# ---------------------------------------------------------
# LOGICAL VALIDATION LOGIC
# ---------------------------------------------------------

def logical_mrz_validation(parsed_result: dict, mrz_type: str):
    """
    Performs logical (semantic) validation on parsed MRZ fields.
    Does NOT do checksums or structural checks.
    """

    if parsed_result.get("status") != "PARSED":
        return {"status": "SKIPPED"}

    data = parsed_result["data"]
    errors = []
    warnings = []
    signals = []

    today = date.today()

    # -------------------------------------------------
    # 1. Mandatory Fields Presence
    # -------------------------------------------------
    mandatory_fields = [
        "document_number", "date_of_birth",
        "expiry_date", "surname",
        "nationality", "issuing_country", "gender"
    ]

    for field in mandatory_fields:
        if not data.get(field):
            # For personal_number, it's optional in many cases, so skip strictly
            if field == "personal_number": continue 
            errors.append(f"MISSING_{field.upper()}")

    # -------------------------------------------------
    # 2. Character Set Validation (Selective)
    # -------------------------------------------------
    # We only check fields that should remain raw MRZ alphanumeric
    regex_fields = ["document_number", "nationality", "issuing_country", "personal_number"]
    
    for field in regex_fields:
        val = data.get(field, "")
        if val and not _only_mrz_chars(val):
            errors.append(f"INVALID_CHARSET_{field.upper()}")

    # Name fields allow A-Z and spaces (converted from <)
    name_fields = ["surname", "given_names"]
    for field in name_fields:
        val = data.get(field, "")
        if val and not re.fullmatch(r"[A-Z0-9 ]*", val):
             errors.append(f"INVALID_CHARSET_{field.upper()}")

    # -------------------------------------------------
    # 3. Date Logical Validation
    # -------------------------------------------------
    dob = None
    exp = None

    # Date Format Check (YYYY-MM-DD)
    if data["date_of_birth"]:
        try:
            dob = date.fromisoformat(data["date_of_birth"])
        except ValueError:
            errors.append("INVALID_DOB_FORMAT")

    if data["expiry_date"]:
        try:
            exp = date.fromisoformat(data["expiry_date"])
        except ValueError:
            errors.append("INVALID_EXPIRY_FORMAT")

    # Logical checks if dates are valid
    if dob:
        if dob > today:
            errors.append("FUTURE_BIRTH_DATE")

        age = _years_between(dob, today)
        if age < 0:
            errors.append("NEGATIVE_AGE") # Should be caught by Future Birth Date
        elif age > MAX_HUMAN_AGE:
            warnings.append(f"IMPLAUSIBLE_AGE_{age}")
        elif age < 1:
            signals.append("INFANT_DOCUMENT")

    if dob and exp:
        if dob >= exp:
            errors.append("DOB_AFTER_EXPIRY")
        
        # Check if issued too young (e.g. 5 year old with 20 year validity?)
        # Not strictly an error but logic check

    if exp:
        # Check for expired document
        if exp < today:
            warnings.append("DOCUMENT_EXPIRED")
        
        # Check validity duration (Cap at 10 years + epsilon, or 20 for some countries)
        # Note: We don't have Issue Date in MRZ (usually), so we rely on exp - today or exp - dob (rough)
        if dob:
            # This is a weak check because we don't know issue date, 
            # but if exp is 100 years after dob, that's wrong.
            if _years_between(dob, exp) > 110:
                warnings.append("EXPIRY_TOO_FAR_FROM_BIRTH")

    # -------------------------------------------------
    # 4. Gender Validation
    # -------------------------------------------------
    if data["gender"] not in ["M", "F", "<", "X"]: # X is becoming common for non-binary
        errors.append(f"INVALID_GENDER_VALUE_{data['gender']}")

    # -------------------------------------------------
    # 5. Cross-Field Logic
    # -------------------------------------------------
    # Warning if Nationality differs from Issuer (valid, but worth noting)
    if data["issuing_country"] != data["nationality"]:
        signals.append(f"NATIONALITY_MISMATCH_{data['issuing_country']}_{data['nationality']}")

    # -------------------------------------------------
    # Final Result
    # -------------------------------------------------
    status = "FAIL" if errors else "PASS"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "signals": signals
    }

# ---------------------------------------------------------
# Test Script

# ---------------------------------------------------------
if __name__ == "__main__":
    images = [
        "ukpassport.jpg",
      
    ]

    
    extractor = FastMRZ()
    for img_path in images:
        print(f"Processing: {img_path}")
        
        # 1. Extract
        res = extractor.get_details(img_path)
        print("\nExtraction Result:")
        print(res)
    
        # 2. Structural Check
        struct_res = structural_mrz_validation(res)
        print("\nStructural Validation:")
        print(struct_res)
    
        
        # 3. Checksum Check
        if struct_res["status"] == "PASS":
            chk_res = checksum_mrz_validation(res, struct_res["mrz_type"])
            print("\nChecksum Validation:")
            print(chk_res)
        
            # 4. Parsing (ONLY if checksum passes)
            if chk_res["status"] == "PASS":
                parsed = parse_mrz_fields(res, struct_res["mrz_type"])
                print("\nParsed MRZ Fields:")
                print(parsed)


                # 5. Logical Validation (NEW)
                logical_res = logical_mrz_validation(parsed, struct_res["mrz_type"])
                print("\nLogical Validation:")
                print(logical_res)
