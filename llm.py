"""OpenAI + Ollama adapters with provider-isolated initialization."""
import os

try:
    import streamlit as st
except ImportError:
    st = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import ollama
except ImportError:
    ollama = None

from config import SETTINGS

SYSTEM = """You are a medical-information RAG assistant for an oncology education project. Use ONLY the supplied evidence. Do not invent facts or silently add outside medical knowledge. Return a concise answer followed by citations using ONLY immutable evidence IDs such as [E1]. If evidence is insufficient, say so. Distinguish direct evidence from cautious synthesis. Do not provide diagnosis, personalized treatment, dosing, or emergency instructions."""


def _secret(name, default=None):
    if st is not None:
        try:
            value = st.secrets.get(name)
            if value not in (None, ""):
                return value
        except Exception:
            pass
    return os.getenv(name, default)


def _openai_key():
    return _secret("OPENAI_API_KEY")


def generate(prompt, provider=None, model=None):
    provider = (provider or SETTINGS.llm_provider).strip().lower()

    if provider == "openai":
        if OpenAI is None:
            raise RuntimeError(
                "The 'openai' package is not installed. Install openai>=1.50."
            )

        key = _openai_key()
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Add it to Streamlit "
                "Secrets or the OPENAI_API_KEY environment variable."
            )

        selected_model = model or _secret(
            "OPENAI_MODEL", SETTINGS.openai_model
        )
        client = OpenAI(api_key=key, timeout=180, max_retries=2)

        if hasattr(client, "responses"):
            response = client.responses.create(
                model=selected_model,
                instructions=SYSTEM,
                input=prompt,
            )
            if getattr(response, "output_text", None):
                return response.output_text.strip()

        response = client.chat.completions.create(
            model=selected_model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty response.")
        return content.strip()

    if provider == "ollama":
        if ollama is None:
            raise RuntimeError(
                "The 'ollama' package is not installed. Install ollama."
            )

        selected_model = model or _secret(
            "OLLAMA_MODEL", SETTINGS.ollama_model
        )
        host = _secret("OLLAMA_BASE_URL", SETTINGS.ollama_base_url).rstrip("/")
        client = ollama.Client(host=host)
        response = client.chat(
            model=selected_model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": 0.1},
        )
        content = response.get("message", {}).get("content")
        if not content:
            raise RuntimeError("Ollama returned an empty response.")
        return content.strip()

    raise ValueError(f"Unsupported provider: {provider}")
