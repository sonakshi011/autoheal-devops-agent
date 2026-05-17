export interface WorkflowRun {
  id: number;
  name: string;
  status: string;
  conclusion: string | null;
  event: string;
  html_url: string;
  created_at: string | null;
}

export interface PipelineRunsData {
  runs: WorkflowRun[];
  is_mock: boolean;
}
