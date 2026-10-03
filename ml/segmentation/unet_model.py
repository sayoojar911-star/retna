"""Lightweight Supervised 2D U-Net for OCT Retinal Nerve Fiber Layer (RNFL) Segmentation.

Designed specifically for optical coherence tomography B-scan images:
- Input: Grayscale OCT B-scan [B, 1, H, W]
- Output: Pixel-level RNFL probability map / logits [B, 1, H, W]
- Extractable outputs:
  - Binary RNFL mask
  - Upper boundary (ILM / Inner Limiting Membrane)
  - Lower boundary (RNFL-GCL interface)
  - Column-wise RNFL thickness (pixels and micrometers)

DISCLAIMER:
Research demonstrator only. Not cleared or approved by the FDA or CE.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    """(Convolution => BatchNorm => ReLU) * 2."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.double_conv(x)


class DownBlock(nn.Module):
    """Downscaling with MaxPool then double conv."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.maxpool_conv(x)


class UpBlock(nn.Module):
    """Upscaling then double conv with skip connection."""

    def __init__(self, in_channels: int, out_channels: int, bilinear: bool = True):
        super().__init__()
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels)
        else:
            self.up = nn.ConvTranspose2d(in_channels // 2, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        x1 = self.up(x1)
        # Pad x1 if dimensions differ slightly due to odd resolutions
        diff_y = x2.size()[2] - x1.size()[2]
        diff_x = x2.size()[3] - x1.size()[3]
        if diff_y != 0 or diff_x != 0:
            x1 = F.pad(x1, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class RNFL_UNet(nn.Module):
    """Supervised U-Net for OCT B-scan RNFL layer segmentation."""

    def __init__(self, in_channels: int = 1, base_filters: int = 16, bilinear: bool = True):
        super().__init__()
        self.in_channels = in_channels
        self.bilinear = bilinear

        f = base_filters  # 16
        self.inc = DoubleConv(in_channels, f)          # 1 -> 16
        self.down1 = DownBlock(f, f * 2)               # 16 -> 32
        self.down2 = DownBlock(f * 2, f * 4)           # 32 -> 64
        self.down3 = DownBlock(f * 4, f * 8)           # 64 -> 128
        factor = 2 if bilinear else 1
        self.down4 = DownBlock(f * 8, (f * 16) // factor) # 128 -> 256 // factor

        self.up1 = UpBlock(f * 16, (f * 8) // factor, bilinear)
        self.up2 = UpBlock(f * 8, (f * 4) // factor, bilinear)
        self.up3 = UpBlock(f * 4, (f * 2) // factor, bilinear)
        self.up4 = UpBlock(f * 2, f, bilinear)
        self.outc = nn.Conv2d(f, 1, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass. Returns single-channel logits [B, 1, H, W]."""
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        logits = self.outc(x)
        return logits

    @torch.no_grad()
    def predict_mask(
        self, bscan_tensor: torch.Tensor, threshold: float = 0.5
    ) -> torch.Tensor:
        """Predict binary mask [B, 1, H, W] uint8 given input tensor in [0, 1]."""
        self.eval()
        logits = self.forward(bscan_tensor)
        probs = torch.sigmoid(logits)
        mask = (probs >= threshold).to(torch.uint8)
        return mask


def extract_boundaries_from_mask(
    mask: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract ILM, RNFL-GCL rows and thickness in pixels from a 2D binary mask (H, W).

    Args:
        mask: 2D uint8 or bool array (height, width), where 1/255 is RNFL layer.

    Returns:
        ilm_y: float32 array (width,), row index of top RNFL edge (ILM)
        rnfl_gcl_y: float32 array (width,), row index of bottom RNFL edge (RNFL-GCL)
        thickness_pixels: float32 array (width,), RNFL thickness in pixels
    """
    height, width = mask.shape
    ilm_y = np.zeros(width, dtype=np.float32)
    rnfl_gcl_y = np.zeros(width, dtype=np.float32)
    thickness_pixels = np.zeros(width, dtype=np.float32)

    is_fg = (mask > 0)

    for col in range(width):
        fg_rows = np.where(is_fg[:, col])[0]
        if len(fg_rows) > 0:
            top = float(fg_rows[0])
            bot = float(fg_rows[-1] + 1)
            ilm_y[col] = top
            rnfl_gcl_y[col] = bot
            thickness_pixels[col] = bot - top
        else:
            # If empty column, extrapolate from neighbors or zero
            ilm_y[col] = 0.0
            rnfl_gcl_y[col] = 0.0
            thickness_pixels[col] = 0.0

    return ilm_y, rnfl_gcl_y, thickness_pixels


class SoftDiceLoss(nn.Module):
    """Soft Dice Loss for binary segmentation."""

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        probs_flat = probs.view(-1)
        targets_flat = targets.view(-1)

        intersection = (probs_flat * targets_flat).sum()
        dice = (2.0 * intersection + self.smooth) / (
            probs_flat.sum() + targets_flat.sum() + self.smooth
        )
        return 1.0 - dice


class CombinedBCEDiceLoss(nn.Module):
    """Combined BCE and Dice Loss for robust layer boundary detection."""

    def __init__(self, bce_weight: float = 0.5, dice_weight: float = 0.5):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = SoftDiceLoss()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        loss_bce = self.bce(logits, targets)
        loss_dice = self.dice(logits, targets)
        return self.bce_weight * loss_bce + self.dice_weight * loss_dice
