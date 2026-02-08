"""Tests for OmniMRZ library."""

import pytest
import cv2
import numpy as np
from omnimrz import OmniMRZ


class TestOmniMRZ:
    """Test cases for OmniMRZ functionality."""

    def test_initialization(self):
        """Test that OmniMRZ can be initialized."""
        engine = OmniMRZ()
        assert engine is not None

    def test_process_with_invalid_image(self):
        """Test processing with invalid image path."""
        engine = OmniMRZ()
        result = engine.process("nonexistent.jpg")
        assert result["extraction"]["status"] == "FAILURE"

    def test_process_with_numpy_array(self):
        """Test processing with numpy array input."""
        engine = OmniMRZ()
        # Create a dummy image array
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = engine.process(dummy_image)
        # Should still return a result structure even if MRZ extraction fails
        assert "extraction" in result
        assert "structural_validation" in result
        assert "screenshot_detection" in result

    def test_screenshot_detection_structure(self):
        """Test that screenshot detection returns expected structure."""
        engine = OmniMRZ()
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = engine.process(dummy_image)

        screenshot = result["screenshot_detection"]
        assert "status" in screenshot
        assert "is_screenshot" in screenshot
        assert "score" in screenshot
        assert "confidence" in screenshot
        assert "reasons" in screenshot

        # For numpy array input, should default to not screenshot
        assert screenshot["is_screenshot"] is False
        assert screenshot["status"] == "PASS"


if __name__ == "__main__":
    pytest.main([__file__])