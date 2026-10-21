"""
Core AI Review Engine for CodeSentinel.
Integrates Gemini API, OpenAI API, and intelligent local heuristic analysis.
"""
import os
import json
import requests
from typing import Dict, Any, List, Optional
from rules import scan_code_with_rules

class CodeAnalyzer:
    def __init__(self, api_key: Optional[str] = None, provider: str = "auto", model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.provider = provider
        self.model = model

        # Auto-detect provider if auto
        if self.provider == "auto":
            if os.getenv("GEMINI_API_KEY"):
                self.provider = "gemini"
                self.api_key = os.getenv("GEMINI_API_KEY")
            elif os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.api_key and self.api_key.startswith("AIza"):
                self.provider = "gemini"
            elif self.api_key and self.api_key.startswith("sk-"):
                self.provider = "openai"
            else:
                self.provider = "heuristic"

    def analyze(self, code_or_diff: str, file_path: str = "code.py", strictness: str = "standard", focus_areas: List[str] = None) -> Dict[str, Any]:
        """Performs comprehensive code review using LLM or local rule engine."""
        focus_areas = focus_areas or ["security", "performance", "architecture", "style"]

        # If provider is gemini and we have an API key, call Gemini
        if self.provider == "gemini" and self.api_key:
            try:
                return self._call_gemini(code_or_diff, file_path, strictness, focus_areas)
            except Exception as e:
                print(f"[Warning] Gemini API call failed ({e}), falling back to heuristic engine.")
                return self._heuristic_fallback(code_or_diff, file_path, fallback_reason=str(e))

        # If provider is openai and we have an API key, call OpenAI
        elif self.provider == "openai" and self.api_key:
            try:
                return self._call_openai(code_or_diff, file_path, strictness, focus_areas)
            except Exception as e:
                print(f"[Warning] OpenAI API call failed ({e}), falling back to heuristic engine.")
                return self._heuristic_fallback(code_or_diff, file_path, fallback_reason=str(e))

        # Default to high-precision local heuristic engine
        return self._heuristic_fallback(code_or_diff, file_path)

    def _call_gemini(self, code: str, file_path: str, strictness: str, focus_areas: List[str]) -> Dict[str, Any]:
        model = self.model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        system_instruction = self._build_prompt(code, file_path, strictness, focus_areas)
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": system_instruction}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        
        resp = requests.post(url, json=payload, timeout=40)
        if resp.status_code != 200:
            raise Exception(f"Gemini API error {resp.status_code}: {resp.text}")
            
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(raw_text)
        result["engine_used"] = f"Google Gemini ({model})"
        return self._normalize_result(result, code, file_path)

    def _call_openai(self, code: str, file_path: str, strictness: str, focus_areas: List[str]) -> Dict[str, Any]:
        model = self.model or "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_instruction = self._build_prompt(code, file_path, strictness, focus_areas)
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are CodeSentinel AI, a Staff Security Engineer & Principal Architect performing an automated code review. Always respond in strict JSON matching the requested schema."},
                {"role": "user", "content": system_instruction}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=40)
        if resp.status_code != 200:
            raise Exception(f"OpenAI API error {resp.status_code}: {resp.text}")
            
        data = resp.json()
        raw_text = data["choices"][0]["message"]["content"]
        result = json.loads(raw_text)
        result["engine_used"] = f"OpenAI ({model})"
        return self._normalize_result(result, code, file_path)

    def _build_prompt(self, code: str, file_path: str, strictness: str, focus_areas: List[str]) -> str:
        return f"""
Analyze the following code / git diff for file '{file_path}'.
Strictness Level: {strictness.upper()}
Focus Areas: {", ".join(focus_areas)}

CODE / DIFF TO REVIEW:
```
{code}
```

You must return a valid JSON object strictly adhering to this schema:
{{
  "verdict": "APPROVE" | "REQUEST_CHANGES" | "COMMENT",
  "score": number between 0 and 100,
  "grade": "A+" | "A" | "B" | "C" | "D" | "F",
  "executive_summary": "High-level summary of the PR, key findings, and deployment readiness.",
  "counts": {{
    "critical": number,
    "high": number,
    "medium": number,
    "low": number
  }},
  "comments": [
    {{
      "file_path": "{file_path}",
      "line_number": integer,
      "severity": "critical" | "high" | "medium" | "low",
      "category": "security" | "performance" | "architecture" | "style",
      "title": "Short title",
      "description": "Clear explanation of the problem, why it is dangerous, and edge cases.",
      "suggestion": "Recommended corrected code snippet or patch."
    }}
  ],
  "key_risks": ["Bullet point risk 1", "Bullet point risk 2"],
  "positive_notes": ["Good practice identified 1", "Good practice 2"]
}}
"""

    def _heuristic_fallback(self, code: str, file_path: str, fallback_reason: Optional[str] = None) -> Dict[str, Any]:
        """Analyzes code using the built-in rule engine."""
        raw_issues = scan_code_with_rules(code, file_path)
        
        # Calculate stats
        crit_count = sum(1 for i in raw_issues if i["severity"] == "critical")
        high_count = sum(1 for i in raw_issues if i["severity"] == "high")
        med_count = sum(1 for i in raw_issues if i["severity"] == "medium")
        low_count = sum(1 for i in raw_issues if i["severity"] == "low")
        
        # Calculate penalty & score
        penalty = (crit_count * 30) + (high_count * 15) + (med_count * 8) + (low_count * 3)
        score = max(0, min(100, 100 - penalty))

        # Calculate Grade
        if score >= 95:
            grade = "A+"
        elif score >= 85:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 45:
            grade = "D"
        else:
            grade = "F"

        # Determine Verdict
        if crit_count > 0 or high_count > 1 or score < 60:
            verdict = "REQUEST_CHANGES"
        elif med_count > 2 or score < 85:
            verdict = "COMMENT"
        else:
            verdict = "APPROVE"

        # Generate summary
        if crit_count > 0:
            summary = f"Identified {crit_count} Critical security vulnerability(ies) and {high_count} high-priority issue(s). Immediate refactoring required before merging to prevent exploitation."
        elif high_count > 0 or med_count > 0:
            summary = f"Found {high_count + med_count} potential issues covering performance, security, and error handling. Resolving these will ensure system stability."
        else:
            summary = "No major vulnerabilities or severe performance bottlenecks detected. Code is well-structured and follows good engineering practices."

        key_risks = []
        if crit_count > 0:
            key_risks.append("Critical credential leak or remote code execution / injection vulnerability present in commit.")
        if med_count > 0:
            key_risks.append("Potential unhandled exception or unbounded resource consumption under production load.")
        if not key_risks:
            key_risks.append("Standard deployment safeguards apply; low architectural risk.")

        positive_notes = [
            "Clear function modularity and readability.",
            "Fast execution path with localized logic."
        ]

        engine_name = "CodeSentinel Heuristic & AST Engine"
        if fallback_reason:
            engine_name += f" (Fallback: {fallback_reason[:40]}...)"

        return {
            "verdict": verdict,
            "score": score,
            "grade": grade,
            "executive_summary": summary,
            "engine_used": engine_name,
            "counts": {
                "critical": crit_count,
                "high": high_count,
                "medium": med_count,
                "low": low_count
            },
            "comments": raw_issues,
            "key_risks": key_risks,
            "positive_notes": positive_notes
        }

    def _normalize_result(self, result: Dict[str, Any], code: str, file_path: str) -> Dict[str, Any]:
        """Guarantees consistency in response structure."""
        comments = result.get("comments", [])
        counts = result.get("counts", {})
        
        # Recalculate counts if missing
        if not counts or not isinstance(counts, dict):
            counts = {
                "critical": sum(1 for c in comments if c.get("severity") == "critical"),
                "high": sum(1 for c in comments if c.get("severity") == "high"),
                "medium": sum(1 for c in comments if c.get("severity") == "medium"),
                "low": sum(1 for c in comments if c.get("severity") == "low")
            }

        return {
            "verdict": result.get("verdict", "COMMENT"),
            "score": result.get("score", 70),
            "grade": result.get("grade", "B"),
            "executive_summary": result.get("executive_summary", "Review completed."),
            "engine_used": result.get("engine_used", "AI Engine"),
            "counts": counts,
            "comments": comments,
            "key_risks": result.get("key_risks", []),
            "positive_notes": result.get("positive_notes", [])
        }
