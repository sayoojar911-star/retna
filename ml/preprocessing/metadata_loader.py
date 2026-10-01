"""Metadata Loader for GlaucoMap.

Ingests clinical and RNFL tabular metadata from CSV/JSON files, normalizing
column names to standardized ClinicalData and RNFLData schemas.
"""

import json
import os
from typing import Any, Dict, Optional
import pandas as pd

from ml.preprocessing.schema import ClinicalData, EyeLaterality, RNFLData


class MetadataLoader:
    """Parses tabular clinical records and joins with imaging studies."""

    def __init__(self):
        pass

    def load_tabular_file(self, file_path: str) -> pd.DataFrame:
        """Load tabular data from CSV or Excel file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Metadata file not found: {file_path}")

        _, ext = os.path.splitext(file_path.lower())
        if ext == ".csv":
            return pd.read_csv(file_path)
        elif ext in {".xlsx", ".xls"}:
            return pd.read_excel(file_path)
        elif ext == ".json":
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported metadata extension: {ext}")

    def parse_clinical_row(self, row: pd.Series) -> ClinicalData:
        """Extract standardized ClinicalData from a row without inventing values."""
        # Convert index to lower case for case-insensitive lookup
        row_dict = {str(k).lower().strip(): v for k, v in row.items()}

        def get_val(keys: list, cast_func=None):
            for k in keys:
                if k in row_dict and pd.notna(row_dict[k]):
                    val = row_dict[k]
                    if cast_func:
                        try:
                            return cast_func(val)
                        except (ValueError, TypeError):
                            return None
                    return val
            return None

        age = get_val(["age", "patient_age"], int)
        gender = get_val(["gender", "sex"])
        iop = get_val(["iop", "iop_mmhg", "intraocular_pressure", "pressure"], float)
        cdr = get_val(["cdr", "cup_to_disc_ratio", "vcdr", "cup_disc_ratio"], float)
        vf_md = get_val(["vf_md", "visual_field_md", "md", "mean_deviation"], float)
        vf_psd = get_val(["vf_psd", "psd", "pattern_standard_deviation"], float)
        vfi = get_val(["vfi", "visual_field_index"], float)
        visit_month = get_val(["visit_month", "month", "visit", "timeline_month"], int)

        # Progression & glaucoma labels
        glaucoma_diag = get_val(["glaucoma", "glaucoma_diagnosed", "diagnosis", "label", "glaucoma_label"])
        if isinstance(glaucoma_diag, (int, float)):
            glaucoma_diag_bool = bool(glaucoma_diag)
        elif isinstance(glaucoma_diag, str):
            glaucoma_diag_bool = glaucoma_diag.lower() in {"1", "true", "yes", "glaucoma", "positive"}
        else:
            glaucoma_diag_bool = None

        glaucoma_grade = get_val(["glaucoma_grade", "grade", "stage", "severity"])
        progression_label = get_val(["progression", "progressing", "progression_label", "progression_status"])

        return ClinicalData(
            age=age,
            gender=str(gender) if gender is not None else None,
            intraocular_pressure_mmhg=iop,
            cup_to_disc_ratio=cdr,
            visual_field_md_db=vf_md,
            visual_field_psd_db=vf_psd,
            visual_field_index_percent=vfi,
            visit_month=visit_month,
            glaucoma_diagnosed=glaucoma_diag_bool,
            glaucoma_grade=str(glaucoma_grade) if glaucoma_grade is not None else None,
            progression_label=str(progression_label) if progression_label is not None else None,
        )

    def parse_rnfl_row(self, row: pd.Series) -> RNFLData:
        """Extract standardized RNFLData from a row if available."""
        row_dict = {str(k).lower().strip(): v for k, v in row.items()}

        def get_val(keys: list):
            for k in keys:
                if k in row_dict and pd.notna(row_dict[k]):
                    try:
                        return float(row_dict[k])
                    except (ValueError, TypeError):
                        return None
            return None

        avg = get_val(["rnfl_avg", "rnfl_average", "average_rnfl", "global_rnfl", "g_thickness"])
        sup = get_val(["rnfl_sup", "rnfl_superior", "superior_rnfl", "s_thickness"])
        inf = get_val(["rnfl_inf", "rnfl_inferior", "inferior_rnfl", "i_thickness"])
        nasal = get_val(["rnfl_nasal", "nasal_rnfl", "n_thickness"])
        temp = get_val(["rnfl_temp", "rnfl_temporal", "temporal_rnfl", "t_thickness"])

        return RNFLData(
            average_thickness_um=avg,
            superior_thickness_um=sup,
            inferior_thickness_um=inf,
            nasal_thickness_um=nasal,
            temporal_thickness_um=temp,
        )
