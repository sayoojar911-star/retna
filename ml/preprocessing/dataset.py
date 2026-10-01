"""PyTorch Dataset Interface for GlaucoMap.

Bridges the OCTStudy common representation to standard PyTorch DataLoaders,
providing model-ready tensors and ground-truth targets.
"""

from typing import Any, Callable, Dict, List, Optional
import numpy as np
import torch
from torch.utils.data import Dataset

from ml.preprocessing.schema import OCTStudy
from ml.preprocessing.transforms import OCTPreprocessTransform


class GlaucoMapDataset(Dataset):
    """PyTorch Dataset consuming standardized OCTStudy instances."""

    def __init__(
        self,
        studies: List[OCTStudy],
        transform: Optional[Callable[[Any], torch.Tensor]] = None,
        return_clinical: bool = True,
    ):
        self.studies = [s for s in studies if s.image_path or s.image is not None]
        self.transform = transform or OCTPreprocessTransform()
        self.return_clinical = return_clinical

    def __len__(self) -> int:
        return len(self.studies)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        study = self.studies[idx]

        # 1. Transform Image Asset
        if study.image is not None:
            image_tensor = self.transform(study.image)
        elif study.image_path:
            image_tensor = self.transform(study.image_path)
        else:
            raise ValueError(f"Study '{study.study_id}' contains no image data or path.")

        # 2. Extract Labels (-1 represents unannotated/unlabeled)
        glaucoma_label = -1
        progression_label = -1
        md_slope = 0.0

        if study.labels:
            if study.labels.glaucoma is not None:
                glaucoma_label = study.labels.glaucoma
            if study.labels.progression is not None:
                progression_label = study.labels.progression
            if study.labels.progression_md_slope is not None:
                md_slope = study.labels.progression_md_slope
        elif study.clinical_data:
            if study.clinical_data.glaucoma_diagnosed is not None:
                glaucoma_label = int(study.clinical_data.glaucoma_diagnosed)

        # 3. Extract Clinical Feature Vector [age, iop, vf_md]
        # Missing values are zero-centered or flagged to avoid hallucination
        clinical_vec = np.zeros(4, dtype=np.float32)
        if study.clinical_data and self.return_clinical:
            c = study.clinical_data
            clinical_vec[0] = (c.age - 60.0) / 15.0 if c.age is not None else 0.0
            clinical_vec[1] = (c.intraocular_pressure_mmhg - 16.0) / 5.0 if c.intraocular_pressure_mmhg is not None else 0.0
            clinical_vec[2] = c.visual_field_md_db / 10.0 if c.visual_field_md_db is not None else 0.0
            clinical_vec[3] = 1.0 if c.gender and c.gender.lower() in ("f", "female") else 0.0

        return {
            "image": image_tensor,
            "glaucoma": torch.tensor(glaucoma_label, dtype=torch.long),
            "progression": torch.tensor(progression_label, dtype=torch.long),
            "md_slope": torch.tensor(md_slope, dtype=torch.float32),
            "clinical_features": torch.from_numpy(clinical_vec),
            "study_id": study.study_id,
            "patient_id": study.patient_id or study.study_id,
            "modality": study.modality.value,
        }
