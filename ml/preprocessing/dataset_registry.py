"""Dataset Registry for GlaucoMap.

Provides centralized registration and discovery of dataset loaders,
ensuring extensibility as new research sources are onboarded.
"""

from typing import Callable, Dict, List, Optional
from ml.preprocessing.base_loader import BaseDataLoader
from ml.preprocessing.image_loader import StandardImageLoader
from ml.preprocessing.harvard_gdp_loader import HarvardGDPLoader
from ml.preprocessing.harvard_gd_loader import HarvardGDLoader


class DatasetRegistry:
    """Registry managing available data loaders for diverse ophthalmic sources."""

    _loaders: Dict[str, Callable[[], BaseDataLoader]] = {}

    @classmethod
    def register(cls, name: str, loader_factory: Callable[[], BaseDataLoader]):
        """Register a new loader factory under a unique key."""
        cls._loaders[name.lower()] = loader_factory

    @classmethod
    def get_loader(cls, name: str, **kwargs) -> BaseDataLoader:
        """Instantiate and return the loader registered under the given key."""
        key = name.lower()
        if key not in cls._loaders:
            raise KeyError(
                f"No loader registered under name '{name}'. Registered: {sorted(cls._loaders.keys())}"
            )
        return cls._loaders[key]()

    @classmethod
    def list_registered_loaders(cls) -> List[str]:
        """List all currently registered loader keys."""
        return sorted(list(cls._loaders.keys()))


# Register standard default loaders
DatasetRegistry.register(
    "generic_image_loader",
    lambda: StandardImageLoader(source_name="generic_image_source")
)
DatasetRegistry.register(
    "harvard_gdp",
    lambda: HarvardGDPLoader(data_dir="data/raw/harvard_gdp")
)
DatasetRegistry.register(
    "harvard_gd",
    lambda: HarvardGDLoader(data_dir="data/raw/harvard_gd")
)
DatasetRegistry.register(
    "gamma",
    lambda: StandardImageLoader(source_name="gamma")
)

