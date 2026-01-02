import re
from datetime import datetime
from .utils import compute_check_digit, clean_ocr_digit


def _parse_date_yyMMdd(date_str, is_expiry=False):
    if not re.match(r"\d{6}", date_str):
        return None

    year, month, day = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:6])
    current_year = datetime.now().year % 100

    century = 1900 if (year > current_year and not is_expiry) else 2000
    try:
        return datetime(century + year, month, day).date().isoformat()
    except ValueError:
        return None


def _clean_name(name):
    return re.sub(r"\s+", " ", name.replace("<", " ").strip())


def parse_mrz_fields(mrz_result, mrz_type):
    if mrz_result.get("status") != "SUCCESS(extraction of mrz)":
        return {"status": "SKIPPED"}

    l1, l2 = mrz_result["line1"], mrz_result["line2"]

    try:
        if mrz_type == "TD3":
            data = {
                "document_type": l1[:2].replace("<", ""),
                "issuing_country": l1[2:5],
                "surname": _clean_name(l1[5:].split("<<")[0]),
                "given_names": _clean_name(l1[5:].split("<<")[1]),
                "document_number": l2[:9].replace("<", ""),
                "nationality": l2[10:13],
                "date_of_birth": _parse_date_yyMMdd(l2[13:19]),
                "gender": l2[20],
                "expiry_date": _parse_date_yyMMdd(l2[21:27], True),
                "personal_number": l2[28:42].replace("<", ""),
            }
        else:
            return {"status": "UNSUPPORTED_MRZ_TYPE"}

        return {"status": "PARSED", "data": data}
    except Exception as e:
        return {"status": "PARSE_ERROR", "error": str(e)}
