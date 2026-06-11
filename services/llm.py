import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b" # or any lightweight local model

def summarize_dossier_with_llm(dossier_text: str) -> str:
    """Sends the dossier text to a local Ollama LLM to generate an intelligence summary."""
    prompt = f"""
    You are an expert OSINT and SIGINT analyst. Read the following intelligence dossier 
    and provide a concise, high-level tactical summary of the target's identity, location, and network context.
    Keep it strictly professional and do not hallucinate data.

    DOSSIER:
    {dossier_text}
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = httpx.post(OLLAMA_URL, json=payload, timeout=60.0)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Error: LLM returned empty response.")
    except httpx.ConnectError:
        return "Error: Local LLM is not running. Please start Ollama (http://localhost:11434)."
    except Exception as e:
        return f"LLM Summarization failed: {e}"
