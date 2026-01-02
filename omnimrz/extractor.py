# omnimrz\extractor.py
import cv2
import re
import numpy as np
from paddleocr import PaddleOCR


class OmniMRZ:
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
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # ---------------------------------------------------------
    # 2. Text Normalization & Clustering
    # ---------------------------------------------------------
    def _normalize(self, text):
        text = text.upper().strip()
        text = text.replace(" ", "")
        return re.sub(r"[^A-Z0-9<]", "", text)

    def _cluster_text_to_lines(self, ocr_results, y_threshold=20):
        if not ocr_results or not ocr_results[0]:
            return []

        raw_items = []
        for box, text, score in zip(
            ocr_results[0]["dt_polys"],
            ocr_results[0]["rec_texts"],
            ocr_results[0]["rec_scores"],
        ):
            y_center = sum(p[1] for p in box) / 4
            x_center = sum(p[0] for p in box) / 4
            raw_items.append({"text": text, "y": y_center, "x": x_center})

        raw_items.sort(key=lambda k: k["y"])

        lines, current = [], []
        for item in raw_items:
            if not current:
                current.append(item)
            else:
                avg_y = sum(i["y"] for i in current) / len(current)
                if abs(item["y"] - avg_y) < y_threshold:
                    current.append(item)
                else:
                    lines.append(current)
                    current = [item]
        if current:
            lines.append(current)

        merged_lines = []
        for line in lines:
            line.sort(key=lambda k: k["x"])
            merged_lines.append(self._normalize("".join(i["text"] for i in line)))

        return merged_lines

    # ---------------------------------------------------------
    # 3. Intelligent Alignment
    # ---------------------------------------------------------
    def _align_and_fix_line(self, text, target_length, is_line1):
        if len(text) == target_length:
            return text

        if len(text) < target_length:
            return text + ("<" * (target_length - len(text)))

        if is_line1:
            match = re.search(r"[PIACV][A-Z0-9<]", text)
            if match:
                text = text[match.start():]

        return text[:target_length]

    # ---------------------------------------------------------
    # 4. MRZ Extraction
    # ---------------------------------------------------------
    def _extract_mrz(self, image):
        roi = self._crop_mrz_zone(image)
        preprocessed = self._preprocess(roi)
        result = self.ocr.predict(preprocessed)

        merged_rows = self._cluster_text_to_lines(result)
        candidate_rows = [r for r in merged_rows if len(r) > 10]

        if len(candidate_rows) < 2:
            return None

        line1, line2 = candidate_rows[-2], candidate_rows[-1]

        target_len = 44
        if len(line1) <= 32:
            target_len = 30
        elif len(line1) < 40:
            target_len = 36

        return (
            self._align_and_fix_line(line1, target_len, True),
            self._align_and_fix_line(line2, target_len, False),
        )

    def get_details(self, image):
        if isinstance(image, str):
            image = cv2.imread(image)

        if image is None:
            return {"status": "FAILURE", "status_message": "Image load failed"}

        mrz = self._extract_mrz(image)
        if not mrz:
            return {"status": "FAILURE", "status_message": "No MRZ found"}

        return {
            "status": "SUCCESS(extraction of mrz)",
            "line1": mrz[0],
            "line2": mrz[1],
        }
