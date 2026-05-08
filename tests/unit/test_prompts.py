import pytest
from ai_engine.prompts.templates import PromptBuilder
from ai_engine.exceptions import PromptError

def test_prompt_builder_init_success():
    builder = PromptBuilder()
    assert builder.env is not None

def test_prompt_builder_init_invalid_dir():
    with pytest.raises(PromptError, match="Templates directory not found"):
        PromptBuilder(templates_dir="non_existent_dir")

def test_build_failure_diagnosis_prompt():
    builder = PromptBuilder()
    logs = "Traceback (most recent call last):\n  File 'app.py', line 10\nZeroDivisionError"
    
    prompt = builder.build_failure_diagnosis_prompt(
        logs=logs,
        exit_code=1,
        workflow_name="CI Pipeline"
    )
    
    assert "CI Pipeline" in prompt
    assert "Exit Code: 1" in prompt
    assert "ZeroDivisionError" in prompt
    assert "Your output MUST be a valid JSON object" in prompt
