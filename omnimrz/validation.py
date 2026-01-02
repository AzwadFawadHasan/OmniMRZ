import re
from datetime import date
from .utils import compute_check_digit, clean_ocr_digit


def structural_mrz_validation(mrz_result):
    if mrz_result.get("status") != "SUCCESS(extraction of mrz)":
        return {"status": "SKIPPED", "mrz_type": None}

    l1, l2 = mrz_result["line1"], mrz_result["line2"]

    if len(l1) == len(l2) == 44:
        return {"status": "PASS", "mrz_type": "TD3", "errors": []}

    return {"status": "FAIL", "mrz_type": None, "errors": ["BAD_LENGTH"]}


def checksum_mrz_validation(mrz_result, mrz_type):
    if mrz_type != "TD3":
        return {"status": "SKIPPED", "errors": []}

    l2 = mrz_result["line2"]
    errors = []

    def check(data, cd):
        cd = clean_ocr_digit(cd)
        if not cd.isdigit() or compute_check_digit(data) != int(cd):
            errors.append("CHECKSUM_FAIL")

    check(l2[:9], l2[9])
    check(l2[13:19], l2[19])
    check(l2[21:27], l2[27])

    composite = l2[:10] + l2[13:20] + l2[21:43]
    check(composite, l2[43])

    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def logical_mrz_validation(parsed_result, mrz_type):
    if parsed_result.get("status") != "PARSED":
        return {"status": "SKIPPED"}

    data = parsed_result["data"]
    errors = []

    if data["expiry_date"]:
        if date.fromisoformat(data["expiry_date"]) < date.today():
            errors.append("DOCUMENT_EXPIRED")

    return {"status": "FAIL" if errors else "PASS", "errors": errors}
