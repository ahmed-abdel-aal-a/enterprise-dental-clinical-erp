"""Module plugin system public API."""

from .base import BaseModule
from .context import ModuleContext
from .loader import mount_modules, register_discovered
from .manifest import Manifest, ManifestError
from .registry import module_registry
from .service import DoctorReport, ModuleInfo, ModuleOperationError, ModuleService
from .state import ModuleCategory, ModuleState

__all__ = [
    "BaseModule",
    "DoctorReport",
    "Manifest",
    "ManifestError",
    "ModuleCategory",
    "ModuleContext",
    "ModuleInfo",
    "ModuleOperationError",
    "ModuleService",
    "ModuleState",
    "mount_modules",
    "module_registry",
    "register_discovered",
]
