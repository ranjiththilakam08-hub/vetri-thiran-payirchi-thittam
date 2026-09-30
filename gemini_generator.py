import os
import random
import time
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=True)


# ============================================================
# MOCK GENERATOR
# ============================================================

def _mock_generate(
    document_type: str,
    parties: str,
    terms: str,
    effective_date: Optional[str] = None,
) -> str:
    """Generate a sample document when MOCK_AI=true."""

    date_text = effective_date or "Not specified"

    return f"""LEGAL DOCUMENT

DOCUMENT TYPE: {document_type}

PARTIES:
{parties}

EFFECTIVE DATE:
{date_text}

TERMS:
{terms}

AGREEMENT

This document records an agreement between the parties identified above.

1. PURPOSE
The parties agree to the terms and conditions described in this document.

2. OBLIGATIONS
Each party agrees to fulfill the obligations described in the terms.

3. EFFECTIVE DATE
This agreement becomes effective on {date_text}.

4. GENERAL TERMS
The parties agree to comply with the applicable terms of this agreement.

5. SIGNATURES

Party 1: ______________________________

Party 2: ______________________________

Date: _________________________________
"""


# ============================================================
# ERROR CLASSIFICATION
# ============================================================

def _is_retryable_error(exc: Exception) -> bool:
    """
    Determine whether an error is likely temporary and should
    trigger another Gemini attempt.
    """

    error_text = str(exc).lower()

    retryable_messages = [
        "429",
        "408",
        "500",
        "502",
        "503",
        "504",
        "resource_exhausted",
        "service_unavailable",
        "unavailable",
        "timeout",
        "timed out",
        "deadline",
        "winerror 10060",
        "connection",
        "network",
        "temporarily",
        "server disconnected",
        "high demand",
    ]

    return any(message in error_text for message in retryable_messages)


# ============================================================
# GEMINI GENERATOR
# ============================================================

def _gemini_generate(
    document_type: str,
    parties: str,
    terms: str,
    effective_date: Optional[str] = None,
) -> str:
    """
    Generate a legal document using Gemini.

    The configured model is tried first.
    If Gemini temporarily fails, fallback models are tried.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Please add your Gemini API key to the .env file."
        )

    configured_model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.7-flash",
    ).strip()

    # Primary model + fallback models.
    #
    # Duplicates are automatically removed below.
    candidate_models = [
        configured_model,
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
    ]

    models = []

    for model_name in candidate_models:
        if model_name and model_name not in models:
            models.append(model_name)

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = f"""
You are an AI legal document drafting assistant.

Create a professional legal document based on the information
provided by the user.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

TERMS / REQUIREMENTS:
{terms}

EFFECTIVE DATE:
{effective_date or "Not specified"}

IMPORTANT INSTRUCTIONS:

1. Generate ONLY the legal document.
2. Do not include explanations before or after the document.
3. Do not mention that you are an AI.
4. Use clear professional legal language.
5. Use appropriate headings and numbered clauses.
6. Include the parties correctly.
7. Include the effective date if provided.
8. Do not invent important facts that were not provided.
9. Where information is missing, use a reasonable neutral
   placeholder such as "Not specified" rather than inventing it.
10. Include signature sections where appropriate.
11. Make the document suitable for editing and export to DOCX/PDF.
12. Preserve all important user-provided terms.

Generate the complete {document_type}.
""".strip()

    # --------------------------------------------------------
    # Import Gemini SDK
    # --------------------------------------------------------

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "The Google GenAI SDK is not installed.\n"
            "Run:\n"
            "pip install -U google-genai"
        ) from exc

    # --------------------------------------------------------
    # Create client
    # --------------------------------------------------------

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=120000
            ),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Unable to initialize Gemini client: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Try each model
    # --------------------------------------------------------

    last_error = None

    for model_index, model in enumerate(models):

        # First model gets more attempts.
        # Fallback models get fewer attempts so the app does
        # not spend too long waiting.
        max_attempts = 3 if model_index == 0 else 2

        for attempt in range(1, max_attempts + 1):

            print(
                f"Gemini request: model={model}, "
                f"attempt={attempt}/{max_attempts}"
            )

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )

                # ------------------------------------------------
                # Extract response text
                # ------------------------------------------------

                generated_text = getattr(
                    response,
                    "text",
                    None,
                )

                if generated_text is None:
                    generated_text = ""

                generated_text = generated_text.strip()

                if not generated_text:

                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                print(
                    f"Gemini generation successful "
                    f"using model: {model}"
                )

                return generated_text

            except Exception as exc:

                last_error = exc

                print(
                    f"Gemini request failed for {model}: "
                    f"{exc}"
                )

                # ------------------------------------------------
                # Retry temporary failures
                # ------------------------------------------------

                if _is_retryable_error(exc):

                    if attempt < max_attempts:

                        # Exponential backoff:
                        # 2s -> 4s -> 8s ...
                        delay = min(
                            2 ** attempt,
                            20,
                        )

                        # Small random variation prevents
                        # synchronized retries.
                        jitter = random.uniform(
                            0.0,
                            1.0,
                        )

                        wait_time = delay + jitter

                        print(
                            "Temporary Gemini/network error. "
                            f"Retrying in {wait_time:.1f} seconds..."
                        )

                        time.sleep(wait_time)

                        continue

                    # This model failed all attempts.
                    # Move to the next fallback model.
                    print(
                        f"Model {model} failed after "
                        f"{max_attempts} attempts."
                    )

                    break

                # ------------------------------------------------
                # Non-retryable error
                # ------------------------------------------------

                raise RuntimeError(
                    f"Gemini API request failed:\n{exc}"
                ) from exc

    # ------------------------------------------------------------
    # All models failed
    # ------------------------------------------------------------

    raise RuntimeError(
        "Gemini API request failed after trying all "
        f"available models.\nLast error: {last_error}"
    ) from last_error


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def generate_legal_document(
    document_type: str,
    parties: str,
    terms: str,
    effective_date: Optional[str] = None,
) -> str:
    """
    Main document-generation function used by the backend.

    If MOCK_AI=true, a local sample document is generated.
    Otherwise, the Gemini API is used.
    """

    mock_ai = os.getenv(
        "MOCK_AI",
        "false",
    ).strip().lower()

    if mock_ai in {
        "true",
        "1",
        "yes",
        "on",
    }:
        print("MOCK_AI is enabled. Using mock document generator.")

        return _mock_generate(
            document_type=document_type,
            parties=parties,
            terms=terms,
            effective_date=effective_date,
        )

    return _gemini_generate(
        document_type=document_type,
        parties=parties,
        terms=terms,
        effective_date=effective_date,
    )