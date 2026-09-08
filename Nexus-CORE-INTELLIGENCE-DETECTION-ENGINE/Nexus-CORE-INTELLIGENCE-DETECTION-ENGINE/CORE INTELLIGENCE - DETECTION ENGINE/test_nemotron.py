"""
Standalone connection test CLI for NVIDIA Nemotron NIM API.
Imports ONLY fir_intelligence.config and the openai package.

Usage:
    python test_nemotron.py
"""

import sys
from fir_intelligence.config import NemotronConfig


def main():
    print("NVIDIA NIM TEST")
    print("----------------")

    config = NemotronConfig()

    key_status = "LOADED" if config.api_key else "MISSING"
    print(f"Base URL: {config.base_url}")
    print(f"Model: {config.model}")
    print(f"API Key: {key_status}")

    if not config.is_configured():
        print("\nDIRECT NIM TEST: FAIL — Missing API Key in .env file (set NVIDIA_NIM_API_KEY).")
        sys.exit(1)

    try:
        import openai
    except ImportError:
        print("\nDIRECT NIM TEST: FAIL — openai package is not installed.")
        sys.exit(1)

    try:
        client = openai.OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
        )

        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=10,
        )

        content = response.choices[0].message.content or ""
        cleaned = content.strip()
        print(f"\nDIRECT NIM TEST: PASS -- HTTP 200 -- {cleaned}")

    except Exception as e:
        print(f"\nDIRECT NIM TEST: FAIL -- {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
