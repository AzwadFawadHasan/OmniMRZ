# KYC Integration Guide

This guide shows how to integrate OmniMRZ into production Know Your Customer (KYC), AML, and identity verification systems.

## Overview

OmniMRZ is specifically designed for KYC/AML workflows with:
- Complete ICAO-9303 compliance validation
- Screenshot and fraud detection
- Fast batch processing
- Structured data extraction for compliance databases
- Detailed audit trails

## Integration Architecture

### Typical KYC Pipeline

```
User Upload → Validation → Data Extraction → Compliance Checks → Database
                (OmniMRZ)    (OmniMRZ)         (Your system)      Storage
```

## Basic KYC Integration

### 1. Simple Single-Document Verification

```python
from omnimrz import OmniMRZ
import json
from datetime import datetime

class KYCVerifier:
    def __init__(self):
        self.omni = OmniMRZ()
    
    def verify_document(self, image_path, user_id):
        """Verify a single passport document for KYC"""
        
        # Process document
        result = self.omni.process(image_path)
        
        # Check all validations
        is_extractable = result["extraction"]["status"] == "SUCCESS(extraction of mrz)"
        is_structurally_valid = result["structural_validation"]["status"] == "PASS"
        is_checksum_valid = result["checksum_validation"]["status"] == "PASS"
        is_logically_valid = result["logical_validation"]["status"] == "PASS"
        is_not_screenshot = not result["screenshot_detection"]["is_screenshot"]
        
        # Determine KYC status
        if all([is_extractable, is_structurally_valid, 
                is_checksum_valid, is_logically_valid, is_not_screenshot]):
            kyc_status = "APPROVED"
            extracted_data = result["parsed_data"]["data"]
        else:
            kyc_status = "REJECTED"
            extracted_data = None
        
        # Create KYC record
        kyc_record = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "document_path": image_path,
            "kyc_status": kyc_status,
            "validation_details": {
                "extraction": is_extractable,
                "structural": is_structurally_valid,
                "checksum": is_checksum_valid,
                "logical": is_logically_valid,
                "screenshot": is_not_screenshot
            },
            "extracted_data": extracted_data,
            "errors": result["logical_validation"]["errors"],
            "raw_result": result  # For audit trail
        }
        
        return kyc_record

# Usage
verifier = KYCVerifier()
kyc_record = verifier.verify_document("passport.jpg", user_id="USER_12345")

if kyc_record["kyc_status"] == "APPROVED":
    print(f"KYC approved for {kyc_record['extracted_data']['given_names']}")
else:
    print(f"KYC rejected: {kyc_record['errors']}")
```

---

### 2. Batch Processing (Multiple Documents)

```python
from omnimrz import OmniMRZ
import os
import csv
from datetime import datetime

class BatchKYCProcessor:
    def __init__(self, csv_output_path="kyc_results.csv"):
        self.omni = OmniMRZ()
        self.csv_output = csv_output_path
    
    def process_batch(self, image_directory):
        """Process all passport images in a directory"""
        
        results = []
        
        for filename in os.listdir(image_directory):
            if filename.endswith((".jpg", ".png", ".jpeg")):
                image_path = os.path.join(image_directory, filename)
                
                # Process document
                result = self.omni.process(image_path)
                
                # Extract summary
                if result["extraction"]["status"] == "SUCCESS(extraction of mrz)":
                    data = result["parsed_data"]["data"]
                    status = (
                        "APPROVED" if (
                            result["structural_validation"]["status"] == "PASS" and
                            result["checksum_validation"]["status"] == "PASS" and
                            result["logical_validation"]["status"] == "PASS"
                        ) else "REJECTED"
                    )
                    
                    results.append({
                        "filename": filename,
                        "status": status,
                        "surname": data.get("surname", ""),
                        "given_names": data.get("given_names", ""),
                        "dob": data.get("date_of_birth", ""),
                        "nationality": data.get("nationality", ""),
                        "doc_expiry": data.get("expiry_date", ""),
                        "errors": ", ".join(result["logical_validation"]["errors"])
                    })
                else:
                    results.append({
                        "filename": filename,
                        "status": "EXTRACTION_FAILED",
                        "errors": result["extraction"].get("status_message", "Unknown error")
                    })
        
        # Save to CSV
        self._save_to_csv(results)
        return results
    
    def _save_to_csv(self, results):
        """Export results to CSV for compliance reporting"""
        if not results:
            return
        
        keys = results[0].keys()
        with open(self.csv_output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)

# Usage
processor = BatchKYCProcessor()
results = processor.process_batch("passport_images/")
print(f"Processed {len(results)} documents")
```

---

### 3. Web Application Integration (Flask Example)

```python
from flask import Flask, request, jsonify
from omnimrz import OmniMRZ
from datetime import datetime
import uuid

app = Flask(__name__)
omni = OmniMRZ()

@app.route('/api/verify-document', methods=['POST'])
def verify_document():
    """API endpoint for KYC document verification"""
    
    # Check if file uploaded
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No document provided"}), 400
    
    file = request.files['document']
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "user_id required"}), 400
    
    # Save temporarily
    temp_path = f"/tmp/{uuid.uuid4()}.jpg"
    file.save(temp_path)
    
    try:
        # Process with OmniMRZ
        result = omni.process(temp_path)
        
        # Prepare response
        response = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "kyc_status": "APPROVED" if all([
                result["extraction"]["status"] == "SUCCESS(extraction of mrz)",
                result["structural_validation"]["status"] == "PASS",
                result["checksum_validation"]["status"] == "PASS",
                result["logical_validation"]["status"] == "PASS",
                not result["screenshot_detection"]["is_screenshot"]
            ]) else "REJECTED",
            "validation": {
                "extraction": result["extraction"]["status"],
                "structural": result["structural_validation"]["status"],
                "checksum": result["checksum_validation"]["status"],
                "logical": result["logical_validation"]["status"],
                "anti_fraud": result["screenshot_detection"]["status"]
            }
        }
        
        # Include parsed data if validation passed
        if response["kyc_status"] == "APPROVED":
            response["extracted_data"] = result["parsed_data"]["data"]
        else:
            response["errors"] = result["logical_validation"]["errors"]
        
        return jsonify(response), 200
    
    finally:
        # Cleanup
        import os
        os.remove(temp_path)

if __name__ == '__main__':
    app.run(debug=False, port=5000)
```

**Testing the API:**
```bash
curl -X POST http://localhost:5000/api/verify-document \
  -F "document=@passport.jpg" \
  -F "user_id=USER_12345"
```

---

### 4. Database Integration

```python
from omnimrz import OmniMRZ
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLAlchemy ORM model
Base = declarative_base()

class KYCRecord(Base):
    __tablename__ = 'kyc_records'
    
    user_id = Column(String, primary_key=True)
    verification_timestamp = Column(DateTime, default=datetime.now)
    kyc_status = Column(String)  # APPROVED, REJECTED, PENDING
    surname = Column(String)
    given_names = Column(String)
    date_of_birth = Column(String)
    nationality = Column(String)
    doc_number = Column(String)
    doc_expiry = Column(String)
    is_expired = Column(Boolean)
    validation_errors = Column(JSON)
    raw_validation_result = Column(JSON)

class KYCDatabase:
    def __init__(self, db_url="sqlite:///kyc_records.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.omni = OmniMRZ()
    
    def verify_and_store(self, user_id, image_path):
        """Verify document and store in database"""
        
        result = self.omni.process(image_path)
        
        # Determine KYC status
        if (result["extraction"]["status"] == "SUCCESS(extraction of mrz)" and
            result["structural_validation"]["status"] == "PASS" and
            result["checksum_validation"]["status"] == "PASS"):
            
            data = result["parsed_data"]["data"]
            kyc_status = "APPROVED" if result["logical_validation"]["status"] == "PASS" else "REJECTED"
            
            # Create record
            record = KYCRecord(
                user_id=user_id,
                kyc_status=kyc_status,
                surname=data.get("surname", ""),
                given_names=data.get("given_names", ""),
                date_of_birth=data.get("date_of_birth", ""),
                nationality=data.get("nationality", ""),
                doc_number=data.get("document_number", ""),
                doc_expiry=data.get("expiry_date", ""),
                is_expired="DOCUMENT_EXPIRED" in result["logical_validation"]["errors"],
                validation_errors=result["logical_validation"]["errors"],
                raw_validation_result=result
            )
        else:
            record = KYCRecord(
                user_id=user_id,
                kyc_status="REJECTED",
                validation_errors=result["extraction"].get("status_message", "Extraction failed"),
                raw_validation_result=result
            )
        
        # Save to database
        session = self.Session()
        session.merge(record)  # Use merge to handle upserts
        session.commit()
        
        return record

# Usage
db = KYCDatabase()
kyc_record = db.verify_and_store("USER_12345", "passport.jpg")
print(f"Stored KYC record: {kyc_record.kyc_status}")
```

---

## Compliance & Audit Considerations

### 1. Audit Trail

```python
def create_audit_trail(user_id, result, action="DOCUMENT_VERIFIED"):
    """Create detailed audit logs for compliance"""
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "extraction_status": result["extraction"]["status"],
        "structural_valid": result["structural_validation"]["status"] == "PASS",
        "checksum_valid": result["checksum_validation"]["status"] == "PASS",
        "logical_valid": result["logical_validation"]["status"] == "PASS",
        "screenshot_detected": result["screenshot_detection"]["is_screenshot"],
        "validation_errors": result["logical_validation"]["errors"]
    }
    return audit_entry
```

### 2. Regulatory Compliance

OmniMRZ helps meet requirements for:
- **FATF (Financial Action Task Force)** recommendations on KYC
- **GDPR**: Structured data extraction with audit trails
- **PSDII**: Strong customer authentication verification
- **SOX (Sarbanes-Oxley)**: Document verification audit trails
- **AML/CFT**: Comprehensive document validation

### 3. Data Retention Policy

```python
from datetime import datetime, timedelta

def should_delete_kyc_record(kyc_record, retention_days=2555):  # ~7 years
    """Check if KYC record should be archived/deleted per policy"""
    age = (datetime.now() - kyc_record.verification_timestamp).days
    return age > retention_days
```

---

## Performance Optimization

### 1. Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor
from omnimrz import OmniMRZ
import os

def parallel_kyc_processing(image_directory, num_workers=4):
    """Process multiple documents in parallel"""
    
    def process_image(image_path):
        omni = OmniMRZ()
        return omni.process(image_path)
    
    image_paths = [
        os.path.join(image_directory, f)
        for f in os.listdir(image_directory)
        if f.endswith((".jpg", ".png"))
    ]
    
    results = []
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_image, image_paths))
    
    return results
```

### 2. Caching

```python
from functools import lru_cache
from omnimrz import OmniMRZ

class CachedOmniMRZ:
    def __init__(self):
        self.omni = OmniMRZ()
        self._cache = {}
    
    def process(self, image_path):
        """Process with caching for identical documents"""
        if image_path in self._cache:
            return self._cache[image_path]
        
        result = self.omni.process(image_path)
        self._cache[image_path] = result
        return result
```

---

## Error Handling for Production

```python
class KYCProcessingError(Exception):
    """Base exception for KYC processing"""
    pass

class DocumentExtractionError(KYCProcessingError):
    """Raised when MRZ extraction fails"""
    pass

class DocumentValidationError(KYCProcessingError):
    """Raised when validation fails"""
    pass

def process_with_error_handling(image_path, user_id):
    """Production-grade KYC processing with error handling"""
    
    try:
        omni = OmniMRZ()
        result = omni.process(image_path)
        
        # Check extraction
        if result["extraction"]["status"] != "SUCCESS(extraction of mrz)":
            raise DocumentExtractionError(result["extraction"].get("status_message"))
        
        # Check validations
        if result["structural_validation"]["status"] != "PASS":
            raise DocumentValidationError("Structural validation failed")
        
        if result["checksum_validation"]["status"] != "PASS":
            raise DocumentValidationError(f"Checksum failed: {result['checksum_validation']['errors']}")
        
        return {
            "user_id": user_id,
            "status": "SUCCESS",
            "data": result["parsed_data"]["data"]
        }
    
    except DocumentExtractionError as e:
        return {"user_id": user_id, "status": "EXTRACTION_FAILED", "error": str(e)}
    except DocumentValidationError as e:
        return {"user_id": user_id, "status": "VALIDATION_FAILED", "error": str(e)}
    except Exception as e:
        return {"user_id": user_id, "status": "SYSTEM_ERROR", "error": str(e)}
```

---

## Testing KYC Integration

```python
def test_kyc_workflow():
    """Test complete KYC workflow"""
    
    from omnimrz import OmniMRZ
    
    test_cases = [
        ("valid_passport.jpg", "APPROVED"),
        ("expired_passport.jpg", "REJECTED"),
        ("screenshot_passport.jpg", "REJECTED"),
        ("corrupted_mrz.jpg", "REJECTION"),
    ]
    
    omni = OmniMRZ()
    
    for image_path, expected_status in test_cases:
        result = omni.process(image_path)
        
        actual_status = (
            "APPROVED" if all([
                result["extraction"]["status"] == "SUCCESS(extraction of mrz)",
                result["structural_validation"]["status"] == "PASS",
                result["checksum_validation"]["status"] == "PASS",
                result["logical_validation"]["status"] == "PASS"
            ]) else "REJECTED"
        )
        
        assert actual_status == expected_status, f"Test failed for {image_path}"
        print(f"✓ {image_path}: {actual_status}")
```

---

## Best Practices

1. **Always validate** all 4 checksum stages
2. **Log all results** for audit trails
3. **Use screenshot detection** to prevent fraud
4. **Store raw results** for compliance investigation
5. **Implement timeouts** for document processing
6. **Use dedicated database** for KYC records
7. **Encrypt sensitive data** (SSN, DOB, etc.)
8. **Implement 2FA** for high-value transactions
9. **Regular audits** of KYC rejections
10. **Keep compliance team informed** of validation failures
