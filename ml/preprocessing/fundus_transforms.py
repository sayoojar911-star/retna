"""Image Preprocessing and Validation for Retinal Fundus Photography.

Implements:
1. Technical validation (file format, readable image, RGB conversion, non-zero variance, blank detection).
2. Internal resizing to 224x224 (never rejects images with different dimensions).
3. ImageNet normalization:
   mean = [0.485, 0.456, 0.406]
   std  = [0.229, 0.224, 0.225]
"""

from pathlib import Path
from typing import Tuple, List, Union, Optional
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as T

from ml.preprocessing.schema import QualityStatus


FUNDUS_SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

# Standard ImageNet normalization parameters specified by trained ResNet-18
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Standard Fundus Transformation Pipeline
fundus_transform = T.Compose([
    T.Resize((224, 224), interpolation=T.InterpolationMode.BILINEAR),
    T.ToTensor(),
    T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


class FundusValidationResult:
    """Validation report for fundus image inputs."""

    def __init__(
        self,
        is_valid: bool,
        status: QualityStatus,
        issues: Optional[List[str]] = None,
        dimensions: Optional[Tuple[int, int]] = None,
        color_mode: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.status = status
        self.issues = issues or []
        self.dimensions = dimensions
        self.color_mode = color_mode

    def to_dict(self):
        return {
            "is_valid": self.is_valid,
            "status": self.status.value,
            "issues": self.issues,
            "dimensions": list(self.dimensions) if self.dimensions else None,
            "color_mode": self.color_mode,
        }


def validate_fundus_image(
    file_path: Union[str, Path],
    min_dim: Tuple[int, int] = (32, 32),
    max_dim: Tuple[int, int] = (16384, 16384),
) -> Tuple[FundusValidationResult, Optional[Image.Image]]:
    """Validates fundus image file integrity, readability, and dimensions.
    
    Does NOT reject valid images because they differ from 224x224 (they are resized internally).
    """
    path = Path(file_path)
    issues: List[str] = []

    if not path.exists():
        return FundusValidationResult(
            is_valid=False,
            status=QualityStatus.MISSING_REQUIRED_DATA,
            issues=[f"Fundus image file not found: {path.name}"],
        ), None

    if path.stat().st_size == 0:
        return FundusValidationResult(
            is_valid=False,
            status=QualityStatus.CORRUPTED,
            issues=["Image file is empty (0 bytes)."],
        ), None

    ext = path.suffix.lower()
    if ext not in FUNDUS_SUPPORTED_EXTENSIONS:
        return FundusValidationResult(
            is_valid=False,
            status=QualityStatus.WRONG_MODALITY,
            issues=[
                f"Unsupported fundus image format '{ext}'. "
                f"Supported formats: {', '.join(sorted(FUNDUS_SUPPORTED_EXTENSIONS))}"
            ],
        ), None

    try:
        with Image.open(str(path)) as img:
            w, h = img.size
            orig_mode = img.mode

            # Validate dimensions
            if w < min_dim[0] or h < min_dim[1]:
                issues.append(f"Image dimensions {w}x{h} are below minimum viable optical threshold {min_dim[0]}x{min_dim[1]}.")
                return FundusValidationResult(
                    is_valid=False,
                    status=QualityStatus.INVALID_DIMENSIONS,
                    issues=issues,
                    dimensions=(w, h),
                    color_mode=orig_mode,
                ), None

            if w > max_dim[0] or h > max_dim[1]:
                issues.append(f"Image dimensions {w}x{h} exceed maximum permitted threshold.")
                return FundusValidationResult(
                    is_valid=False,
                    status=QualityStatus.INVALID_DIMENSIONS,
                    issues=issues,
                    dimensions=(w, h),
                    color_mode=orig_mode,
                ), None

            # Convert to RGB
            rgb_img = img.convert("RGB")
            arr = np.array(rgb_img, dtype=np.float32)

            # Check for NaN / Inf
            if np.isnan(arr).any() or np.isinf(arr).any():
                issues.append("Image contains NaN or Inf pixel values.")
                return FundusValidationResult(
                    is_valid=False,
                    status=QualityStatus.CORRUPTED,
                    issues=issues,
                    dimensions=(w, h),
                    color_mode=orig_mode,
                ), None

            # Check for solid blank image (zero variance)
            if np.min(arr) == np.max(arr):
                issues.append("Image has zero variance across all channels (completely blank/monochrome).")
                return FundusValidationResult(
                    is_valid=False,
                    status=QualityStatus.CORRUPTED,
                    issues=issues,
                    dimensions=(w, h),
                    color_mode=orig_mode,
                ), None

            return FundusValidationResult(
                is_valid=True,
                status=QualityStatus.VALID,
                issues=[],
                dimensions=(w, h),
                color_mode="RGB",
            ), rgb_img

    except Exception as e:
        return FundusValidationResult(
            is_valid=False,
            status=QualityStatus.CORRUPTED,
            issues=[f"Failed to decode image data: {str(e)}"],
        ), None


def preprocess_fundus_image(
    image: Union[str, Path, Image.Image]
) -> Tuple[torch.Tensor, Image.Image]:
    """Preprocesses a fundus image for ResNet-18 model inference.
    
    1. Loads / converts image to RGB.
    2. Resizes to 224x224 with bilinear interpolation.
    3. Converts to Tensor and applies ImageNet normalization.
    
    Returns:
        Tuple of (normalized_tensor [1, 3, 224, 224], 224x224 RGB PIL image for overlay)
    """
    if isinstance(image, (str, Path)):
        with Image.open(str(image)) as img:
            rgb_img = img.convert("RGB")
    elif isinstance(image, Image.Image):
        rgb_img = image.convert("RGB")
    else:
        raise TypeError(f"Expected file path or PIL Image, got {type(image)}")

    # Create 224x224 reference image for visualizations
    resized_rgb = rgb_img.resize((224, 224), Image.Resampling.BILINEAR)

    # Tensor with batch dimension: [1, 3, 224, 224]
    tensor = fundus_transform(rgb_img).unsqueeze(0)
    return tensor, resized_rgb
