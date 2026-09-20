/**
 * Nuxt 3 Client-Side Dental Clinical Charting Type Definitions
 */

export interface DentalPatientChart {
  patientId: string;
  chartNumber: string;
  primaryDentistId: string;
  assignedBranchId: string;
  lastVisitIsoDate?: string;
  systemicConditions: string[];
  activeTreatmentPlanId?: string;
}

export interface OdontogramInteractionEvent {
  toothFdi: number;
  selectedSurface: 'OCCLUSAL' | 'MESIAL' | 'DISTAL' | 'BUCCAL' | 'LINGUAL';
  appliedProcedureCode: string;
  costEstimate: number;
  timestampEpoch: number;
}
