"""
Part A - Portfolio advisory

The agent is split into three simple steps:
THINK -> choose an allocation, ACT -> get stock data, and
OBSERVE -> calculate return and risk.

Run:
    python advisory_agent.py
"""

import os
import math

from stock_universe import STOCK_UNIVERSE, RISK_FREE_RATE, MARKET_RETURN
from investor_profiles import INVESTOR_PROFILES

RHO = 0.3  # pairwise correlation assumed between every pair of tickers
STD_DEV_ESCALATION_THRESHOLD = 0.20  # 20%

# Stocks used for each risk category. Each gets an equal weight.
ALLOCATION_TABLE = {
    "Conservative": ["PAYBOND", "PAYGOLD", "PAYRETAIL"],
    "Moderate":     ["PAYRETAIL", "PAYINFRA", "PAYGOLD"],
    "Aggressive":   ["PAYTECH", "PAYFIN", "PAYINFRA"],
}


def think_decide_allocation(risk_tolerance: str):
    """Choose the equal-weighted portfolio for the investor."""
    tickers = ALLOCATION_TABLE[risk_tolerance]
    weight = 1 / 3
    return {ticker: weight for ticker in tickers}


# Get the stock information from the local data.
def get_stock_data(ticker: str) -> dict:
    """Return the data available for a ticker."""
    return STOCK_UNIVERSE[ticker]


# Calculate expected return, portfolio risk and the escalation flag.
def capm_expected_return(beta: float) -> float:
    """CAPM expected return using beta."""
    return RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)


def compute_portfolio_metrics(allocation: dict):
    """Calculate the portfolio return and standard deviation."""
    tickers = list(allocation.keys())

    stock_data = {t: get_stock_data(t) for t in tickers}
    capm_returns = {t: capm_expected_return(stock_data[t]["beta"]) for t in tickers}

    portfolio_return = sum(allocation[t] * capm_returns[t] for t in tickers)

    # Individual variance terms
    variance = sum(
        (allocation[t] ** 2) * (stock_data[t]["std_dev"] ** 2)
        for t in tickers
    )

    # Add the covariance terms for each pair
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            ti, tj = tickers[i], tickers[j]
            cov_ij = RHO * stock_data[ti]["std_dev"] * stock_data[tj]["std_dev"]
            variance += 2 * allocation[ti] * allocation[tj] * cov_ij

    portfolio_std = math.sqrt(variance)

    return {
        "tickers": tickers,
        "weights": allocation,
        "capm_returns": capm_returns,
        "portfolio_return": portfolio_return,
        "portfolio_variance": variance,
        "portfolio_std": portfolio_std,
        "escalate": portfolio_std > STD_DEV_ESCALATION_THRESHOLD,
    }


# Short explanation shown with each recommendation.
def build_narrative(investor: dict, metrics: dict) -> str:
    mock_llm = os.environ.get("MOCK_LLM", "1") != "0"

    if mock_llm:
        # Keep the mock response simple and reproducible.
        return (
            f"For {investor['risk_tolerance']} investor {investor['investor_id']}, "
            f"we recommend an allocation across {', '.join(metrics['tickers'])} "
            f"with an expected portfolio return of {metrics['portfolio_return']:.1%} "
            f"and volatility of {metrics['portfolio_std']:.1%}."
        )
    else:
        raise NotImplementedError(
            "MOCK_LLM=0 is not implemented. Use the default mock mode."
        )


def run_advisory_agent(investor: dict) -> dict:
    """Run the advisory calculation for one investor."""
    allocation = think_decide_allocation(investor["risk_tolerance"])
    metrics = compute_portfolio_metrics(allocation)
    narrative = build_narrative(investor, metrics)

    result = {
        "investor_id": investor["investor_id"],
        "risk_tolerance": investor["risk_tolerance"],
        "tickers": metrics["tickers"],
        "weights": metrics["weights"],
        "capm_returns": metrics["capm_returns"],
        "portfolio_return": metrics["portfolio_return"],
        "portfolio_variance": metrics["portfolio_variance"],
        "portfolio_std": metrics["portfolio_std"],
        "escalated": metrics["escalate"],
        "narrative": narrative,
    }

    print(f"Investor: {result['investor_id']} ({result['risk_tolerance']})")
    print("Allocation:", ", ".join(
        f"{t} ({w:.1%})" for t, w in result["weights"].items()
    ))
    print("CAPM returns:", ", ".join(
        f"{t}={r:.1%}" for t, r in result["capm_returns"].items()
    ))
    print(f"Expected portfolio return: {result['portfolio_return']:.1%}")
    print(f"Portfolio standard deviation: {result['portfolio_std']:.1%}")
    if result["escalated"]:
        print("Decision: Escalate to human advisor")
    else:
        print("Decision: No escalation")
    print(f"Comment: {result['narrative']}")
    print()

    return result


def main():
    mock_llm = os.environ.get("MOCK_LLM", "1") != "0"
    print(f"Mock mode: {mock_llm}\n")

    all_results = [run_advisory_agent(inv) for inv in INVESTOR_PROFILES]

    print("Escalation summary:")
    for r in all_results:
        flag = "escalate" if r["escalated"] else "no escalation"
        print(f"  {r['investor_id']}: {r['portfolio_std']:.1%} -> {flag}")

    return all_results


if __name__ == "__main__":
    main()
