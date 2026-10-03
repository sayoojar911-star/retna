"""Standard Research Image Loader for GlaucoMap.

Ingests standard research image formats (PNG, JPEG, TIFF, BMP, NPY) into
the unified OCTStudy schema while performing technical validation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image

from ml.preprocessing.base_loader import BaseDataLoader
from ml.preprocessing.quality_checks import TechnicalValidator
from ml.preprocessing.schema import EyeLaterality, Modality, OCTStudy, QualityStatus


class StandardImageLoader(BaseDataLoader):
    """Loader for 2D/3D research ophthalmic images stored in standard formats."""

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".npy", ".npz"}

    def __init__(
        self,
        source_name: str = "generic_image_source",
        default_modality: Modality = Modality.OCT_B_SCAN,
        validator: Optional[TechnicalValidator] = None,
    ):
        super().__init__(source_name=source_name, validator=validator)
        self.default_modality = default_modality

    def infer_modality_from_filename(self, filename: str) -> Modality:
        """Infer modality hints from standardized file nomenclature without guessing."""
        name_lower = filename.lower()
        if "rnfl" in name_lower or "thickness" in name_lower or "tsnit" in name_lower:
            return Modality.OCT_RNFL_MAP
        if "bscan" in name_lower or "oct_b" in name_lower or "b_scan" in name_lower:
            return Modality.OCT_B_SCAN
        if "volume" in name_lower or "cube" in name_lower or "3d" in name_lower:
            return Modality.OCT_VOLUME
        if "fundus" in name_lower or "cfp" in name_lower or "color" in name_lower:
            return Modality.FUNDUS_PHOTO
        if "report" in name_lower or "screenshot" in name_lower or "printout" in name_lower:
            return Modality.REPORT_SCREENSHOT
        return self.default_modality

    def infer_eye_from_filename(self, filename: str) -> EyeLaterality:
        """Extract OD / OS / OU from filename tokens if explicitly present."""
        name_upper = filename.upper()
        tokens = name_upper.replace("-", "_").replace(".", "_").split("_")
        if "OD" in tokens or "RE" in tokens or "RIGHT" in tokens:
            return EyeLaterality.OD
        if "OS" in tokens or "LE" in tokens or "LEFT" in tokens:
            return EyeLaterality.OS
        if "OU" in tokens or "BOTH" in tokens:
            return EyeLaterality.OU
        return EyeLaterality.UNKNOWN

    def load_study(
        self,
        file_path: str,
        study_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        modality: Optional[Modality] = None,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> OCTStudy:
        """Load an image file into an OCTStudy instance with technical validation."""
        path_obj = Path(file_path)
        computed_study_id = study_id or path_obj.stem
        inferred_modality = modality or self.infer_modality_from_filename(path_obj.name)
        inferred_eye = self.infer_eye_from_filename(path_obj.name)

        study = OCTStudy(
            study_id=computed_study_id,
            patient_id=patient_id,
            eye=inferred_eye,
            modality=inferred_modality,
            image_path=str(path_obj.resolve()),
            metadata=metadata or {},
            source=self.source_name,
            quality_status=QualityStatus.UNKNOWN,
        )

        # Attach technical validation status & image shape
        study = self.attach_quality_status(study)
        return study

    def discover_studies(self, root_dir: str) -> List[OCTStudy]:
        """Discover all matching image files under a directory and load as studies."""
        studies: List[OCTStudy] = []
        if not os.path.exists(root_dir):
            return studies

        for root, _, files in os.walk(root_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    study = self.load_study(file_path)
                    studies.append(study)

        return studies
