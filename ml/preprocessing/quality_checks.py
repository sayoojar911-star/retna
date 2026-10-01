"""Technical Data Quality Verification for GlaucoMap.

Performs foundational technical sanity checks on raw files, image dimensions,
and data completeness. Does NOT implement subjective medical-quality grading.
"""

import os
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from PIL import Image

from ml.preprocessing.schema import Modality, OCTStudy, QualityStatus


class ValidationResult(BaseModel):
    """Result of a technical validation check."""
    is_valid: bool
    status: QualityStatus
    issues: List[str] = Field(default_factory=list)
    image_shape: Optional[List[int]] = None


class TechnicalValidator:
    """Foundational technical validator for study files and image assets."""

    SUPPORTED_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".npy", ".npz", ".dcm"
    }

    def __init__(
        self,
        min_dim: Tuple[int, int] = (32, 32),
        max_dim: Tuple[int, int] = (8192, 8192),
        max_blank_ratio: float = 0.98,
    ):
        self.min_dim = min_dim
        self.max_dim = max_dim
        self.max_blank_ratio = max_blank_ratio

    def validate_file(self, file_path: str) -> ValidationResult:
        """Verify file existence, non-emptiness, and extension support."""
        if not os.path.exists(file_path):
            return ValidationResult(
                is_valid=False,
                status=QualityStatus.CORRUPTED,
                issues=[f"File does not exist: {file_path}"]
            )

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                status=QualityStatus.CORRUPTED,
                issues=[f"File is zero bytes (empty): {file_path}"]
            )

        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.SUPPORTED_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                status=QualityStatus.CORRUPTED,
                issues=[f"Unsupported file format '{ext}'. Expected one of: {sorted(self.SUPPORTED_EXTENSIONS)}"]
            )

        return ValidationResult(is_valid=True, status=QualityStatus.VALID)

    def validate_image(self, file_path: str) -> ValidationResult:
        """Inspect image header, decode integrity, dimensions, and basic signal."""
        file_check = self.validate_file(file_path)
        if not file_check.is_valid:
            return file_check

        issues: List[str] = []
        ext = os.path.splitext(file_path.lower())[1]
        try:
            if ext in {".npz", ".npy"}:
                import numpy as np
                if ext == ".npz":
                    with np.load(file_path, allow_pickle=True) as data:
                        key = "rnflt" if "rnflt" in data else list(data.keys())[0]
                        arr = data[key]
                else:
                    arr = np.load(file_path, allow_pickle=True)

                shape = list(arr.shape)
                if len(shape) < 2:
                    return ValidationResult(
                        is_valid=False,
                        status=QualityStatus.INVALID_DIMENSIONS,
                        issues=[f"Array must be at least 2D, got shape {shape}"],
                        image_shape=shape,
                    )
                h, w = shape[-2], shape[-1]
                if w < self.min_dim[0] or h < self.min_dim[1]:
                    return ValidationResult(
                        is_valid=False,
                        status=QualityStatus.INVALID_DIMENSIONS,
                        issues=[f"Array spatial dimensions {w}x{h} below minimum threshold {self.min_dim[0]}x{self.min_dim[1]}"],
                        image_shape=shape,
                    )
                if w > self.max_dim[0] or h > self.max_dim[1]:
                    return ValidationResult(
                        is_valid=False,
                        status=QualityStatus.INVALID_DIMENSIONS,
                        issues=[f"Array spatial dimensions {w}x{h} exceed maximum threshold {self.max_dim[0]}x{self.max_dim[1]}"],
                        image_shape=shape,
                    )
                if np.isnan(arr).any() or np.isinf(arr).any():
                    return ValidationResult(
                        is_valid=False,
                        status=QualityStatus.CORRUPTED,
                        issues=["Array contains NaN or infinite values"],
                        image_shape=shape,
                    )
                if np.min(arr) == np.max(arr):
                    return ValidationResult(
                        is_valid=False,
                        status=QualityStatus.EXCESSIVE_ARTIFACTS,
                        issues=["Array has zero variance across all elements"],
                        image_shape=shape,
                    )
                return ValidationResult(is_valid=True, status=QualityStatus.VALID, issues=[], image_shape=shape)

            with Image.open(file_path) as img:
                img.verify()

            # Reopen for dimensional checks (verify closes file pointer)
            with Image.open(file_path) as img:
                width, height = img.size
                shape = [height, width]
                if hasattr(img, "n_frames") and img.n_frames > 1:
                    shape.insert(0, img.n_frames)

                # Dimensional bounds check
                if width < self.min_dim[0] or height < self.min_dim[1]:
                    issues.append(
                        f"Image dimensions {width}x{height} below minimum allowable threshold {self.min_dim[0]}x{self.min_dim[1]}"
                    )
                    return ValidationResult(
                        is_valid=False,
                        status=QualityStatus.INVALID_DIMENSIONS,
                        issues=issues,
                        image_shape=shape
                    )

                if width > self.max_dim[0] or height > self.max_dim[1]:
                    issues.append(
                        f"Image dimensions {width}x{height} exceed maximum allowable threshold {self.max_dim[0]}x{self.max_dim[1]}"
                    )
                    return ValidationResult(
                        is_valid=False,
                        status=QualityStatus.INVALID_DIMENSIONS,
                        issues=issues,
                        image_shape=shape
                    )

                # Basic blank / corrupted frame check
                if ext in {".png", ".jpg", ".jpeg", ".bmp"}:
                    grayscale = img.convert("L")
                    extrema = grayscale.getextrema()
                    # Check if all pixels are identical (completely solid black or white)
                    if extrema[0] == extrema[1]:
                        issues.append("Image has zero variance across all pixels (completely blank or solid canvas)")
                        return ValidationResult(
                            is_valid=False,
                            status=QualityStatus.EXCESSIVE_ARTIFACTS,
                            issues=issues,
                            image_shape=shape
                        )

                return ValidationResult(
                    is_valid=True,
                    status=QualityStatus.VALID,
                    issues=[],
                    image_shape=shape
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=QualityStatus.CORRUPTED,
                issues=[f"Failed to read/decode image file: {str(e)}"]
            )

    def validate_study_completeness(
        self,
        study: OCTStudy,
        required_fields: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Check for presence of strictly required fields in a loaded study."""
        if required_fields is None:
            required_fields = ["study_id", "source"]

        issues: List[str] = []
        study_dict = study.model_dump()
        for field in required_fields:
            val = study_dict.get(field)
            if val is None or val == "":
                issues.append(f"Missing required study field: '{field}'")

        if issues:
            return ValidationResult(
                is_valid=False,
                status=QualityStatus.MISSING_REQUIRED_DATA,
                issues=issues
            )

        return ValidationResult(is_valid=True, status=QualityStatus.VALID)

    def check_modality(self, study: OCTStudy, expected_modality: Modality) -> ValidationResult:
        """Ensure study modality aligns with downstream requirements."""
        if study.modality != expected_modality:
            return ValidationResult(
                is_valid=False,
                status=QualityStatus.WRONG_MODALITY,
                issues=[f"Modality mismatch: expected '{expected_modality.value}', found '{study.modality.value}'"]
            )
        return ValidationResult(is_valid=True, status=QualityStatus.VALID)
