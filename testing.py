# # testing.py
# from omnimrz import OmniMRZ
# print(OmniMRZ().process("ukpassport.jpg"))


from omnimrz import OmniMRZ
import json

engine = OmniMRZ()

result = engine.process("ukpassport.jpg")

print(json.dumps(result, indent=4))
