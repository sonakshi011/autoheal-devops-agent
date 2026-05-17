export interface BanditFinding {
  ruleId: string;
  message: string;
  file: string;
  line: number;
  severity: "LOW" | "MEDIUM" | "HIGH";
  confidence: "LOW" | "MEDIUM" | "HIGH";
  code?: string;
}

export interface TrivyVulnerability {
  id: string;
  pkgName: string;
  installedVersion: string;
  fixedVersion?: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  title?: string;
  description?: string;
  url?: string;
}

export interface SecurityReport {
  bandit: BanditFinding[];
  trivy: TrivyVulnerability[];
}
