import os
from jinja2 import Environment, FileSystemLoader

from ai_engine.exceptions import PromptError

class PromptBuilder:
    """Helper class to render Jinja2 prompt templates."""
    
    def __init__(self, templates_dir: str = "prompts"):
        # Resolve templates dir relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.templates_path = os.path.join(project_root, templates_dir)
        
        if not os.path.isdir(self.templates_path):
            raise PromptError(f"Templates directory not found: {self.templates_path}")
            
        self.env = Environment(loader=FileSystemLoader(self.templates_path), autoescape=False)
        
    def build_failure_diagnosis_prompt(self, logs: str, exit_code: int, workflow_name: str) -> str:
        """Render the failure diagnosis template."""
        try:
            template = self.env.get_template("failure_diagnosis.j2")
            return template.render(
                logs=logs,
                exit_code=exit_code,
                workflow_name=workflow_name
            )
        except Exception as e:
            raise PromptError(f"Failed to build failure diagnosis prompt: {str(e)}") from e
