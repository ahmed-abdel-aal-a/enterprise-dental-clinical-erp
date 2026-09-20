from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class ToothSurface(str, Enum):
    OCCLUSAL = "OCCLUSAL"
    MESIAL = "MESIAL"
    DISTAL = "DISTAL"
    BUCCAL = "BUCCAL"
    LINGUAL = "LINGUAL"

class ToothCondition(str, Enum):
    SOUND = "SOUND"
    CARIES = "CARIES"
    RESTORED = "RESTORED"
    CROWN = "CROWN"
    ENDODONTIC = "ENDODONTIC"
    MISSING = "MISSING"
    IMPLANT = "IMPLANT"

@dataclass
class ToothStateModel:
    fdi_number: int  # 11 to 48 (Adult), 51 to 85 (Deciduous)
    general_condition: ToothCondition
    affected_surfaces: List[ToothSurface]
    periodontal_pocket_depth_mm: Optional[float] = None
    mobility_grade: int = 0
