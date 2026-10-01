"""Patient-Level Dataset Splitter for GlaucoMap.

Guarantees zero longitudinal data leakage by partitioning cohorts strictly
at the unique patient/subject level, ensuring all visits of a patient
remain exclusively in either Train, Validation, or Test.
"""

from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from ml.preprocessing.schema import OCTStudy


class SplitSummary(BaseModel):
    """Statistical summary of a partitioned dataset split."""
    total_patients: int
    total_studies: int
    train_patients: int
    train_studies: int
    val_patients: int
    val_studies: int
    test_patients: int
    test_studies: int
    train_label_distribution: Dict[str, int] = Field(default_factory=dict)
    val_label_distribution: Dict[str, int] = Field(default_factory=dict)
    test_label_distribution: Dict[str, int] = Field(default_factory=dict)
    data_leakage_detected: bool = False


class PatientLevelSplitter:
    """Partitions studies at patient level with deterministic random seed."""

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int = 42,
    ):
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Split ratios must sum to 1.0"
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_seed = random_seed

    def split(
        self,
        studies: List[OCTStudy],
    ) -> Tuple[List[OCTStudy], List[OCTStudy], List[OCTStudy], SplitSummary]:
        """Perform deterministic patient-level split across the provided studies."""
        if not studies:
            summary = SplitSummary(
                total_patients=0, total_studies=0,
                train_patients=0, train_studies=0,
                val_patients=0, val_studies=0,
                test_patients=0, test_studies=0,
            )
            return [], [], [], summary

        # 1. Group studies by unique patient_id
        patient_to_studies = defaultdict(list)
        for s in studies:
            pid = s.patient_id or s.study_id
            patient_to_studies[pid].append(s)

        unique_patients = sorted(list(patient_to_studies.keys()))
        n_patients = len(unique_patients)

        # 2. Deterministic shuffle
        rng = np.random.RandomState(self.random_seed)
        shuffled_patients = rng.permutation(unique_patients)

        # 3. Partition patient indices
        n_train = int(np.floor(self.train_ratio * n_patients))
        n_val = int(np.floor(self.val_ratio * n_patients))
        
        train_pids = set(shuffled_patients[:n_train])
        val_pids = set(shuffled_patients[n_train:n_train + n_val])
        test_pids = set(shuffled_patients[n_train + n_val:])

        # Guard against zero-patient test splits in small sample cohorts
        if n_patients >= 3 and len(test_pids) == 0:
            test_pids.add(shuffled_patients[-1])
            if shuffled_patients[-1] in val_pids:
                val_pids.remove(shuffled_patients[-1])
            elif shuffled_patients[-1] in train_pids:
                train_pids.remove(shuffled_patients[-1])

        # 4. Strict Data Leakage Verification
        overlap_train_val = train_pids.intersection(val_pids)
        overlap_train_test = train_pids.intersection(test_pids)
        overlap_val_test = val_pids.intersection(test_pids)
        has_leakage = bool(overlap_train_val or overlap_train_test or overlap_val_test)

        if has_leakage:
            raise ValueError(
                f"Data leakage detected! Overlapping patient IDs: "
                f"Train-Val: {overlap_train_val}, Train-Test: {overlap_train_test}, Val-Test: {overlap_val_test}"
            )

        # 5. Assemble studies for each partition
        train_studies = [s for pid in train_pids for s in patient_to_studies[pid]]
        val_studies = [s for pid in val_pids for s in patient_to_studies[pid]]
        test_studies = [s for pid in test_pids for s in patient_to_studies[pid]]

        # 6. Compute label distribution statistics
        def get_dist(study_list: List[OCTStudy]) -> Dict[str, int]:
            counts = Counter()
            for s in study_list:
                if s.labels:
                    if s.labels.glaucoma is not None:
                        counts[f"glaucoma_{s.labels.glaucoma}"] += 1
                    if s.labels.progression is not None:
                        counts[f"progression_{s.labels.progression}"] += 1
                elif s.clinical_data and s.clinical_data.glaucoma_diagnosed is not None:
                    counts[f"glaucoma_{int(s.clinical_data.glaucoma_diagnosed)}"] += 1
            return dict(counts)

        summary = SplitSummary(
            total_patients=n_patients,
            total_studies=len(studies),
            train_patients=len(train_pids),
            train_studies=len(train_studies),
            val_patients=len(val_pids),
            val_studies=len(val_studies),
            test_patients=len(test_pids),
            test_studies=len(test_studies),
            train_label_distribution=get_dist(train_studies),
            val_label_distribution=get_dist(val_studies),
            test_label_distribution=get_dist(test_studies),
            data_leakage_detected=has_leakage,
        )

        return train_studies, val_studies, test_studies, summary
