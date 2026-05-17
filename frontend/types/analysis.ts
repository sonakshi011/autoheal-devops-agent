export interface AIDiagnosis {
  root_cause: string;
  severity: "low" | "medium" | "high" | "critical";
  remediation_steps: string[];
  code_suggestion?: string;
  confidence_score: number;
  model_used: string;
  diagnosis_timestamp: string;
}
