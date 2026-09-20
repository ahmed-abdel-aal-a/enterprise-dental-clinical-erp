from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class IClinicalRepository(ABC):
    """
    Abstract contract for clinical electronic dental record (EDR) persistence
    and multi-branch tenant isolation.
    """

    @abstractmethod
    async def get_patient_clinical_summary(self, patient_id: str, branch_id: str) -> Dict[str, Any]:
        """Retrieves verified clinical history, allergies, and current medical alerts."""
        pass

    @abstractmethod
    async def record_odontogram_state_transition(
        self, 
        patient_id: str, 
        tooth_fdi_number: int, 
        surface: str, 
        procedure_code: str,
        practitioner_id: str
    ) -> bool:
        """Atomically records an odontogram surface state change with audit logging."""
        pass

    @abstractmethod
    async def stream_ai_copilot_triage(self, symptoms_transcript: str) -> Dict[str, Any]:
        """Generates differential clinical diagnostic recommendations via edge LLM inference."""
        pass
