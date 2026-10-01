# RETNA Fundus Image Glaucoma Analysis Pipeline

> **Research Prototype Notice**: RETNA is a research-oriented decision-support prototype. Model outputs represent algorithmic statistical estimates and should not replace clinical judgment or establish an independent diagnosis.

---

## 1. Checkpoint Location & Management

- **Model Filename**: `best_model_v2.pth`
- **Canonical Storage Location**: `models/checkpoints/best_model_v2.pth`
- **Configurable Environment Override**: `FUNDUS_MODEL_CHECKPOINT`
- **Trained Classes**:
  - `0`: Glaucoma_Negative
  - `1`: Glaucoma_Positive

---

## 2. Model Architecture

The classifier is built upon a standard ResNet-18 backbone initialized without pre-trained weights (`weights=None`), with a customized single-output fully connected head:

```python
import torchvision.models as models
import torch.nn as nn

model = models.resnet18(weights=None)
model.fc = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(model.fc.in_features, 1)
)
```

The model emits a single binary logit. The sigmoid activation function converts this logit to the predicted glaucoma probability:

$$\hat{p} = \sigma(z) = \frac{1}{1 + e^{-z}}$$

Classification assignment uses a standard 0.5 decision threshold:
- $\hat{p} \ge 0.5 \implies$ **Glaucoma Positive (Class 1)**
- $\hat{p} < 0.5 \implies$ **Glaucoma Negative (Class 0)**

---

## 3. Image Preprocessing & Input Validation

1. **Validation Checks**:
   - File extension: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`.
   - File readability and RGB conversion.
   - Non-zero variance verification (rejects solid/blank images).
   - NaN/Inf pixel exclusion.
2. **Dimension Handling**:
   - Input images of any optical resolution are accepted (they are **never** rejected merely for having non-training dimensions).
   - Bilinear interpolation resizes all inputs internally to $224 \times 224$ pixels.
3. **ImageNet Normalization**:
   - Mean: $[0.485, 0.456, 0.406]$
   - Standard Deviation: $[0.229, 0.224, 0.225]$

---

## 4. Visual Explainability (Grad-CAM)

Attribution heatmaps are computed via Gradient-Weighted Class Activation Mapping (Grad-CAM) targeting the final convolutional layer of the ResNet-18 architecture:

- **Target Layer**: `model.backbone.layer4[-1]`
- **Forward Activation**: $A^k \in \mathbb{R}^{512 \times 7 \times 7}$
- **Gradients**: Backpropagated with respect to the output logit $y$:
  $$\alpha_k = \frac{1}{H \times W} \sum_{i=1}^H \sum_{j=1}^W \frac{\partial y}{\partial A_{ij}^k}$$
- **Heatmap**:
  $$L_{\text{Grad-CAM}} = \text{ReLU}\left( \sum_k \alpha_k A^k \right)$$
- **Overlay**: 55% original color fundus photograph + 45% Jet colormap heatmap.
- **Mandatory Disclaimer**:
  > *"Highlighted regions represent areas that influenced the model prediction. They do not independently establish a diagnosis."*

---

## 5. Performance Benchmarks from Validation Experiment

The following metrics were recorded during offline validation experiments:

| Metric | Validation Score | Status |
| :--- | :---: | :--- |
| **Fundus Image Alone AUC** | **0.727** | Active (`best_model_v2.pth`) |
| **Cup-Size Alone AUC** | **0.710** | Offline Kaggle Model (Not Exported) |
| **Experimental Combined AUC** | **0.755** | Offline Research Benchmark |

> **Important**: These metrics represent validation experiment outcomes on benchmark datasets. They are **not** clinical validation metrics.

---

## 6. C/D Ratio & Combined Score Policy

1. **No Formula-Based Estimation**:
   The active ResNet-18 fundus classifier is a global image classifier and does **not** perform semantic segmentation of the optic disc or cup. Estimating or fabricating a C/D ratio via mathematical formulas is strictly prohibited.
   - **C/D Status**: `"Not available from current fundus model"`
2. **Combined Score Isolation**:
   The 0.755 combined AUC was obtained in Kaggle using a separately trained Logistic Regression model leveraging cup-size features. That model has not yet been exported into this repository.
   - **Combined Score Status**: `"Unavailable until cup-size model is integrated"`

---

## 7. Backend API Endpoints

- `GET /api/fundus/status`: Returns model checkpoint status, architecture, and validation metrics.
- `GET /api/fundus/demo-cases`: Lists available demonstration cases.
- `POST /api/fundus/analyze`: Accepts multipart image upload or `demo_case_id` form field, returning complete inference, probabilities, and Grad-CAM data URIs.
