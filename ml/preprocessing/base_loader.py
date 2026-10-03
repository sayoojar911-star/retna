"""Abstract Base Data Loader for GlaucoMap.

Defines the contract all dataset loaders must implement to ingest diverse
ophthalmic data into the standard OCTStudy internal representation.
"""

from abc import ABC, abstractmethod
from typing import Generator, List, Optional

from ml.preprocessing.quality_checks import TechnicalValidator
from ml.preprocessing.schema import OCTStudy


class BaseDataLoader(ABC):
    """Abstract base class for all dataset and format loaders."""

    def __init__(self, source_name: str, validator: Optional[TechnicalValidator] = None):
        self.source_name = source_name
        self.validator = validator or TechnicalValidator()

    @abstractmethod
    def load_study(self, file_path: str, **kwargs) -> OCTStudy:
        """Load a single study file or series into an OCTStudy instance."""
        pass

    @abstractmethod
    def discover_studies(self, root_dir: str) -> List[OCTStudy]:
        """Discover and load all valid studies located under a root directory."""
        pass

    def stream_studies(self, root_dir: str) -> Generator[OCTStudy, None, None]:
        """Generator yielding studies one-by-one to support large datasets."""
        for study in self.discover_studies(root_dir):
            yield study

    def attach_quality_status(self, study: OCTStudy) -> OCTStudy:
        """Run technical quality validation and attach status to the study."""
        if study.image_path:
            image_check = self.validator.validate_image(study.image_path)
            study.quality_status = image_check.status
            if image_check.image_shape and not study.image_shape:
                study.image_shape = image_check.image_shape
        else:
            completeness = self.validator.validate_study_completeness(study)
            study.quality_status = completeness.status

        return study
