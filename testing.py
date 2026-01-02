# testing.py
from omnimrz import OmniMRZ
from omnimrz import structural_mrz_validation, checksum_mrz_validation, parse_mrz_fields

extractor = OmniMRZ()

result = extractor.get_details("ukpassport.jpg")
print(result)

struct = structural_mrz_validation(result)

if struct["status"] == "PASS":
    checksum = checksum_mrz_validation(result, struct["mrz_type"])
    parsed = parse_mrz_fields(result, struct["mrz_type"])
    print(parsed)