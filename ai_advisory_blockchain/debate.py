"""
Part C - Simple bull/bear debate for one stock.

The three parts are kept as separate functions. The mock version uses the
values in STOCK_UNIVERSE directly, so it can be run offline.

Run:
    python debate.py
"""

import os

from stock_universe import STOCK_UNIVERSE

# Stock used for the example debate.
DEBATE_TICKER = "PAYFIN"


def bull_argument(ticker: str, data: dict, mock_llm: bool) -> str:
    if not mock_llm:
        raise NotImplementedError("Real LLM mode is not included.")
    r = data["analyst_expected_return"]
    b = data["beta"]
    return (
        f"Bull case for {ticker}: With an expected return of {r:.1%} against a beta of "
        f"{b:.2f}, this offers attractive risk-adjusted upside relative to lower-beta "
        f"names in the universe -- {ticker} is priced to reward investors who can "
        f"tolerate above-market volatility."
    )


def bear_argument(ticker: str, data: dict, mock_llm: bool) -> str:
    if not mock_llm:
        raise NotImplementedError("Real LLM mode is not included.")
    s = data["std_dev"]
    b = data["beta"]
    return (
        f"Bear case for {ticker}: A standard deviation of {s:.1%} combined with a beta of "
        f"{b:.2f} means {ticker} will amplify market drawdowns, not just rallies -- "
        f"in a risk-off scenario this is one of the first names to give back its "
        f"expected-return premium, and the volatility alone could breach a "
        f"conservative investor's risk budget."
    )


def synthesizer_summary(ticker: str, data: dict, bull_text: str, bear_text: str, mock_llm: bool) -> str:
    if not mock_llm:
        raise NotImplementedError("Real LLM mode is not included.")
    r = data["analyst_expected_return"]
    s = data["std_dev"]
    b = data["beta"]
    return (
        f"Overall view on {ticker}'s {r:.1%} expected return and {b:.2f} beta make the "
        f"bull case real, but its {s:.1%} standard deviation makes the bear case just "
        f"as real -- this is a name suited to investors with a longer horizon and "
        f"higher risk tolerance, not a core holding for a conservative allocation."
    )


def run_debate(ticker: str = DEBATE_TICKER):
    mock_llm = os.environ.get("MOCK_LLM", "1") != "0"
    data = STOCK_UNIVERSE[ticker]

    bull = bull_argument(ticker, data, mock_llm)
    bear = bear_argument(ticker, data, mock_llm)
    synthesis = synthesizer_summary(ticker, data, bull, bear, mock_llm)

    print(f"Mock mode: {mock_llm}")
    print(f"Debate ticker: {ticker}")
    print(f"Beta: {data['beta']}, expected return: {data['analyst_expected_return']:.1%}, "
          f"standard deviation: {data['std_dev']:.1%}\n")
    print(bull)
    print()
    print(bear)
    print()
    print(synthesis)

    return {"ticker": ticker, "bull": bull, "bear": bear, "synthesis": synthesis}


if __name__ == "__main__":
    run_debate()
