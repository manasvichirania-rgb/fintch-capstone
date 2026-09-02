"""
Part B - Extract a few useful signals from company disclosures.

The extraction uses simple keyword and regex rules so that the results
are reproducible without an API.

Run:
    python extract_disclosure.py
"""

import os
import re

from disclosure_snippets import DISCLOSURE_SNIPPETS

# Keywords used to identify the main risk areas.
RISK_KEYWORDS = {
    "litigation": ["litigation", "lawsuit", "legal proceeding"],
    "regulatory": ["regulatory", "regulator", "compliance notice"],
    "customer_concentration": ["customer concentration"],  # explicit phrase
}

# Phrases that indicate uncertainty or hedging.
HEDGING_PHRASES = ["assuming", "cautiously", "visibility"]

# Words used for a positive/confident tone.
CONFIDENT_KEYWORDS = ["confident", "approved"]

CUSTOMER_CONCENTRATION_PATTERN = re.compile(
    r"(top\s+\w+\s+customers|customers?\s+(together\s+)?account\s+for|customer concentration)",
    re.IGNORECASE,
)


def _detect_risk_flags(text: str) -> list:
    lower = text.lower()
    flags = []

    if "litigation" in lower or "lawsuit" in lower:
        flags.append("litigation")

    if "regulatory" in lower or "regulator" in lower:
        flags.append("regulatory")

    # Check both the explicit phrase and the wording used in doc_03.
    if "customer concentration" in lower or CUSTOMER_CONCENTRATION_PATTERN.search(text):
        flags.append("customer_concentration")

    return flags


def _detect_hedging(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in HEDGING_PHRASES)


def _detect_sentiment(text: str, hedging_detected: bool) -> str:
    lower = text.lower()
    if any(kw in lower for kw in CONFIDENT_KEYWORDS):
        return "confident"
    if hedging_detected:
        return "cautious"
    return "neutral"


def extract_signals(snippet: str) -> dict:
    """Extract risk flags, hedging and sentiment from one snippet."""
    risk_flags = _detect_risk_flags(snippet)
    hedging_detected = _detect_hedging(snippet)
    sentiment = _detect_sentiment(snippet, hedging_detected)

    return {
        "risk_flags": risk_flags,
        "hedging_detected": hedging_detected,
        "sentiment": sentiment,
    }


def main():
    mock_llm = os.environ.get("MOCK_LLM", "1") != "0"
    print(f"Mock mode: {mock_llm}\n")

    results = []
    for snippet in DISCLOSURE_SNIPPETS:
        doc_id = snippet.split(":", 1)[0]
        signals = extract_signals(snippet)
        results.append((doc_id, signals))
        print(f"{doc_id}:")
        print(f"  Text: {snippet}")
        print(f"  risk_flags:       {signals['risk_flags']}")
        print(f"  hedging_detected: {signals['hedging_detected']}")
        print(f"  sentiment:        {signals['sentiment']}")
        print()

    print(f"Processed {len(results)} disclosure snippets.")

    return results


if __name__ == "__main__":
    main()
