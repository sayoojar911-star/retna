"""PyTorch CNN Architectures for Complete 225x225 RNFLT Thickness Maps.

Provides:
1. AdaptedResNet18: Standard ResNet-18 adapted for 1-channel (225x225) input and 2-class binary logits.
2. CompactRNFLTCNN: Lightweight custom CNN with 4 convolutional blocks, batch norm, and dropout.
"""

from typing import Tuple
import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights


class AdaptedResNet18(nn.Module):
    """ResNet-18 adapted for single-channel 225x225 RNFLT numerical maps."""

    def __init__(self, num_classes: int = 2, pretrained: bool = False):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = resnet18(weights=weights)

        # 1. Modify initial conv layer: from 3 channels to 1 channel (grayscale RNFLT)
        original_conv1 = self.backbone.conv1
        self.backbone.conv1 = nn.Conv2d(
            in_channels=1,
            out_channels=original_conv1.out_channels,
            kernel_size=original_conv1.kernel_size,
            stride=original_conv1.stride,
            padding=original_conv1.padding,
            bias=False,
        )

        if pretrained:
            # Average the original 3-channel weights across the single channel
            with torch.no_grad():
                self.backbone.conv1.weight.copy_(original_conv1.weight.mean(dim=1, keepdim=True))

        # 2. Modify final fully-connected classification head
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for input tensor of shape [batch, 1, 225, 225]."""
        return self.backbone(x)


class CompactRNFLTCNN(nn.Module):
    """Compact 4-block CNN tailored specifically for 225x225 RNFLT OCT thickness maps."""

    def __init__(self, num_classes: int = 2, in_channels: int = 1):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 225x225 -> 112x112
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            # Block 2: 112x112 -> 56x56
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            # Block 3: 56x56 -> 28x28
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            # Block 4: 28x28 -> 14x14
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(p=0.4),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for input tensor of shape [batch, 1, 225, 225]."""
        feat = self.features(x)
        return self.classifier(feat)


def build_model(model_name: str = "resnet18", num_classes: int = 2) -> nn.Module:
    """Factory function to build selected model architecture."""
    if model_name.lower() in ("resnet18", "resnet", "adaptedresnet18"):
        return AdaptedResNet18(num_classes=num_classes, pretrained=False)
    elif model_name.lower() in ("compact", "compact_cnn", "rnflt_cnn"):
        return CompactRNFLTCNN(num_classes=num_classes)
    else:
        raise ValueError(f"Unknown model architecture '{model_name}'. Choose 'resnet18' or 'compact_cnn'.")
