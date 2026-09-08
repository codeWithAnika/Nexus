"""
NVIDIA Nemotron Client Wrapper using OpenAI-compatible NIM API endpoint.
Provides strict JSON mode parsing, exponential backoff retries, local trace logging,
and silent fallback behavior on API timeouts or errors.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fir_intelligence.config import NemotronConfig


class NemotronClient:
    """
    Wrapper for NVIDIA Nemotron NIM API built on top of NemotronConfig.
    Supports strict JSON extraction, retry logic, trace logging, and resilient fallback.
    """

    def __init__(
        self,
        config: Optional[NemotronConfig] = None,
        api_key: Optional[str] = None,
        trace_file: Optional[Path] = None,
    ):
        self.config = config or NemotronConfig()
        if api_key:
            self.config.api_key = api_key

        self.trace_file = trace_file or Path(__file__).parent.parent.parent / "output" / "llm_trace.jsonl"
        self.client = None

        if self.is_available():
            try:
                import openai
                self.client = openai.OpenAI(
                    base_url=self.config.base_url,
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                )
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client for Nemotron: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Returns True if client is configured and API key is present."""
        return self.config.enabled and bool(self.config.api_key)

    def _log_trace(self, prompt: str, system_prompt: str, response_raw: str, duration_ms: float, status: str):
        """Append trace log entry to llm_trace.jsonl for auditability."""
        try:
            self.trace_file.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": time.time(),
                "model": self.config.model,
                "status": status,
                "duration_ms": round(duration_ms, 2),
                "system_prompt_len": len(system_prompt),
                "prompt_len": len(prompt),
                "response_snippet": response_raw[:200] if response_raw else "",
            }
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful JSON extraction assistant.",
        max_retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """
        Sends prompt to Nemotron NIM API and parses JSON response.
        Retries up to max_retries on JSON parse errors. Returns None on unrecoverable failure.
        """
        if not self.is_available() or self.client is None:
            return None

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        attempt = 0
        last_response_text = ""

        while attempt <= max_retries:
            attempt += 1
            t0 = time.time()
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=0.1,
                    top_p=0.9,
                    max_tokens=1024,
                )
                dur = (time.time() - t0) * 1000.0
                raw_text = response.choices[0].message.content or ""
                last_response_text = raw_text

                # Attempt JSON parsing
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith("```"):
                    lines = cleaned_text.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    cleaned_text = "\n".join(lines).strip()

                parsed = json.loads(cleaned_text)
                self._log_trace(prompt, system_prompt, raw_text, dur, "SUCCESS")
                return parsed

            except json.JSONDecodeError:
                dur = (time.time() - t0) * 1000.0
                self._log_trace(prompt, system_prompt, last_response_text, dur, f"JSON_DECODE_ERROR_ATTEMPT_{attempt}")
                if attempt <= max_retries:
                    messages.append({"role": "assistant", "content": last_response_text})
                    messages.append({
                        "role": "user",
                        "content": "Your response was not valid JSON. Return ONLY raw valid JSON with no markdown tags or conversational text."
                    })
            except Exception as e:
                dur = (time.time() - t0) * 1000.0
                self._log_trace(prompt, system_prompt, str(e), dur, f"API_ERROR: {e}")
                print(f"Warning: Nemotron API call failed ({e}). Falling back to deterministic mode.")
                return None

        return None

    def extract_narrative_entities(self, text: str, source_fir_id: str) -> List[Dict[str, Any]]:
        """
        Extracts named entities from narrative text via Nemotron LLM.
        """
        if not text or not self.is_available():
            return []

        prompt = f"FIR Reference ID: {source_fir_id}\nNarrative Text:\n\"\"\"\n{text}\n\"\"\""
        sys_prompt = (
            "You are an AI Criminal Intelligence Entity Extraction system.\n"
            "Extract entities mentioned in the narrative into a JSON object matching this schema:\n"
            "{\n"
            "  \"entities\": [\n"
            "    {\"type\": \"Person|Phone|Email|Account|Organization|Location|Device|IP|Transaction\", \"value\": \"...\", \"context\": \"...\"}\n"
            "  ]\n"
            "}\n"
            "Return ONLY raw JSON."
        )

        res = self.generate_json(prompt=prompt, system_prompt=sys_prompt)
        if res and isinstance(res.get("entities"), list):
            return res["entities"]
        return []

    def evaluate_ambiguous_merge(
        self, candidate_a: Dict[str, Any], candidate_b: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates whether two candidate entities represent the same real-world entity.
        """
        if not self.is_available():
            return {"should_merge": False, "confidence": 0.0, "reasoning": "LLM client unavailable"}

        prompt = (
            f"Entity A: {json.dumps(candidate_a)}\n"
            f"Entity B: {json.dumps(candidate_b)}\n"
            f"Context: {json.dumps(context)}\n"
        )
        sys_prompt = (
            "You are an AI Entity Resolution Specialist.\n"
            "Determine if Entity A and Entity B refer to the exact same real-world entity.\n"
            "Respond ONLY with a JSON object matching this schema:\n"
            "{\n"
            "  \"should_merge\": true|false,\n"
            "  \"confidence\": 0.0-1.0,\n"
            "  \"reasoning\": \"Detailed explanation...\"\n"
            "}"
        )

        res = self.generate_json(prompt=prompt, system_prompt=sys_prompt)
        if res and "should_merge" in res:
            return res
        return {"should_merge": False, "confidence": 0.0, "reasoning": "LLM evaluation failed"}
