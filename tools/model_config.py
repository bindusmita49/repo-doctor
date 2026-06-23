import os
from dotenv import load_dotenv

load_dotenv()

_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash"
]

_CURRENT_MODEL = "gemini-2.5-flash"

def get_available_model() -> str:
    """Return the currently selected model name. Defaults to gemini-2.5-flash."""
    return _CURRENT_MODEL

def fallback_to_next_model() -> str:
    """Switch the current model to the next one in the fallback list and update all active agents."""
    global _CURRENT_MODEL
    try:
        idx = _FALLBACK_MODELS.index(_CURRENT_MODEL)
        if idx < len(_FALLBACK_MODELS) - 1:
            _CURRENT_MODEL = _FALLBACK_MODELS[idx + 1]
        else:
            print("[ModelConfig] Already at final fallback model.")
    except ValueError:
        _CURRENT_MODEL = _FALLBACK_MODELS[0]

    # Mutate all agents' model property so they use the new fallback model immediately
    # We import these locally to avoid circular imports during module load
    try:
        from coordinator_agent.agent import root_agent as coordinator
        coordinator.model = _CURRENT_MODEL
    except Exception as e:
        print(f"[ModelConfig] Could not update coordinator_agent: {e}")

    try:
        from code_quality_agent.agent import root_agent as code_quality
        code_quality.model = _CURRENT_MODEL
    except Exception as e:
        print(f"[ModelConfig] Could not update code_quality_agent: {e}")

    try:
        from security_agent.agent import root_agent as security
        security.model = _CURRENT_MODEL
    except Exception as e:
        print(f"[ModelConfig] Could not update security_agent: {e}")

    try:
        from hello_agent.agent import root_agent as hello
        hello.model = _CURRENT_MODEL
    except Exception as e:
        print(f"[ModelConfig] Could not update hello_agent: {e}")

    print(f"[ModelConfig] Dynamic fallback triggered! Switched active model to: {_CURRENT_MODEL}")
    return _CURRENT_MODEL
