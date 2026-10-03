"""Preprocessing Transformations for GlaucoMap OCT Studies.

Tailored for optical coherence tomography imaging:
- Contrast windowing and clipping
- Grayscale luminance extraction
- Bilinear spatial resizing
- Min-Max and Z-score tensor normalization
"""

from typing import List, Optional, Tuple, Union
import numpy as np
from PIL import Image
import torch


class OCTPreprocessTransform:
    """Preprocesses 2D/3D OCT cross-sections into normalized model-ready tensors."""

    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        normalize_mode: str = "min_max",  # 'min_max', 'imagenet', 'none'
        num_channels: int = 1,  # 1 for native grayscale, 3 for pretrained CNNs
        clip_percentiles: Optional[Tuple[float, float]] = (1.0, 99.0),
    ):
        self.target_size = target_size
        self.normalize_mode = normalize_mode
        self.num_channels = num_channels
        self.clip_percentiles = clip_percentiles

    def __call__(self, image_input: Union[str, Image.Image, np.ndarray]) -> torch.Tensor:
        """Execute full preprocessing pipeline on input image path, PIL image, or array."""
        # 1. Load to PIL Image or NumPy array
        if isinstance(image_input, str):
            # Check for numpy archive
            if image_input.endswith(".npy") or image_input.endswith(".npz"):
                if image_input.endswith(".npz"):
                    with np.load(image_input) as data:
                        # Grab first key array
                        first_key = list(data.keys())[0]
                        arr = data[first_key]
                else:
                    arr = np.load(image_input)
                # If 3D volume, sample central slice
                if len(arr.shape) == 3:
                    mid_idx = arr.shape[0] // 2
                    arr = arr[mid_idx]
                pil_img = Image.fromarray(arr.astype(np.float32))
            else:
                with Image.open(image_input) as img:
                    pil_img = img.convert("RGB" if self.num_channels == 3 else "L")
        elif isinstance(image_input, np.ndarray):
            if len(image_input.shape) == 3 and image_input.shape[0] not in (1, 3):
                # 3D volume, sample middle B-scan
                mid = image_input.shape[0] // 2
                image_input = image_input[mid]
            pil_img = Image.fromarray(image_input.astype(np.float32))
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB" if self.num_channels == 3 else "L")
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        # 2. Resizing with high-quality bilinear interpolation
        resized_img = pil_img.resize(self.target_size, resample=Image.Resampling.BILINEAR)

        # 3. Convert to float numpy array
        arr = np.array(resized_img, dtype=np.float32)

        # 4. Intensity Percentile Clipping (removes specular retinal reflection spikes)
        if self.clip_percentiles:
            p_low, p_high = self.clip_percentiles
            v_min = np.percentile(arr, p_low)
            v_max = np.percentile(arr, p_high)
            if v_max > v_min:
                arr = np.clip(arr, v_min, v_max)

        # 5. Normalization
        if self.normalize_mode == "min_max":
            a_min = np.min(arr)
            a_max = np.max(arr)
            if a_max > a_min:
                arr = (arr - a_min) / (a_max - a_min + 1e-7)
            else:
                arr = np.zeros_like(arr)
        elif self.normalize_mode == "imagenet":
            # Scale to [0, 1] then apply ImageNet standard mean/std
            arr = arr / 255.0 if np.max(arr) > 1.0 else arr
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            if len(arr.shape) == 2:
                arr = np.stack([arr] * 3, axis=-1)
            arr = (arr - mean) / (std + 1e-7)

        # 6. Channel Formatting to PyTorch [C, H, W]
        if len(arr.shape) == 2:
            if self.num_channels == 1:
                tensor = torch.from_numpy(arr).unsqueeze(0)  # [1, H, W]
            else:
                tensor = torch.from_numpy(np.stack([arr] * self.num_channels, axis=0))  # [3, H, W]
        elif len(arr.shape) == 3:
            # Assuming [H, W, C]
            tensor = torch.from_numpy(arr).permute(2, 0, 1)  # [C, H, W]
        else:
            raise ValueError(f"Unexpected array shape: {arr.shape}")

        return tensor.float()
