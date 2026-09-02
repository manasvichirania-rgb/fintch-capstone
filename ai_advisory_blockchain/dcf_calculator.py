"""
dcf_calculator.py

Part D: discounted-cash-flow valuation for a hypothetical Paytm Postpaid
(lending) business line. All assumptions are illustrative and stated
explicitly below and in the README -- this is not a real Paytm valuation.

Steps:
    1. Base-year unlevered FCFF (EBIT*(1-tax) + D&A - CapEx - ChangeNWC)
    2. 5-year FCFF projection with a growth rate fading toward terminal growth
    3. Cost of equity via CAPM (beta from STOCK_UNIVERSE, NOT analyst_expected_return)
    4. WACC (cost of equity blended with an illustrative after-tax cost of debt)
    5. Terminal value via growing perpetuity, discounted to present value
    6. Enterprise value = PV(FCFFs) + PV(terminal value)
    7. 3x3 WACC / terminal-growth sensitivity grid, with a programmatic
       check that WACC > terminal growth in every one of the 9 cells and
       that the worst-case spread is >= 1 percentage point
    8. EV/EBITDA cross-check against an illustrative multiple

Run:
    python dcf_calculator.py
"""

from stock_universe import STOCK_UNIVERSE, RISK_FREE_RATE, MARKET_RETURN

# ============================================================
# Stated assumptions (illustrative, for this exercise only)
# ============================================================

# --- Base-year unlevered FCFF inputs (INR crore) ---
EBIT_0 = 120.0          # base-year EBIT
TAX_RATE = 0.25         # illustrative effective tax rate
DA_0 = 20.0              # depreciation & amortization
CAPEX_0 = 35.0           # capital expenditure
DELTA_NWC_0 = 10.0       # change in net working capital

# --- 5-year growth path: fades from a strong initial rate toward the
#     terminal growth rate (chosen below) ---
YEARLY_GROWTH_RATES = [0.18, 0.15, 0.12, 0.09, 0.06]

# --- Cost of equity: CAPM using PAYFIN's beta (financial-services /
#     lending vertical, the closest analogue in STOCK_UNIVERSE to a
#     Postpaid/BNPL business line). Beta ONLY -- never analyst_expected_return. ---
DCF_BETA_TICKER = "PAYFIN"

# --- Illustrative capital structure and cost of debt ---
PRETAX_COST_OF_DEBT = 0.09
EQUITY_WEIGHT = 0.70
DEBT_WEIGHT = 0.30

# --- Terminal growth: MUST be >= 3 percentage points below base-case WACC
#     (checked programmatically below; this literal is the deliberately
#     conservative choice, not the source of truth) ---
TERMINAL_GROWTH = 0.05

# --- EV/EBITDA cross-check ---
ILLUSTRATIVE_EBITDA = EBIT_0 + DA_0   # = 140 crore
ILLUSTRATIVE_EV_EBITDA_MULTIPLE = 8.0  # illustrative multiple for a fintech/BNPL line


def base_fccf():
    """Unlevered FCFF = EBIT*(1-tax) + D&A - CapEx - ChangeNWC."""
    return EBIT_0 * (1 - TAX_RATE) + DA_0 - CAPEX_0 - DELTA_NWC_0


def project_fcff(base, growth_rates):
    """5-year FCFF projection given a list of 5 yearly growth rates."""
    fcff = []
    prev = base
    for g in growth_rates:
        prev = prev * (1 + g)
        fcff.append(prev)
    return fcff


def cost_of_equity(beta):
    """CAPM: E(Re) = Rf + beta * (Rm - Rf). Uses ONLY beta."""
    return RISK_FREE_RATE + beta * (MARKET_RETURN - RISK_FREE_RATE)


def compute_wacc(re, pretax_cod, tax_rate, equity_w, debt_w):
    aftertax_cod = pretax_cod * (1 - tax_rate)
    wacc = equity_w * re + debt_w * aftertax_cod
    return wacc, aftertax_cod


def discount_factors(rate, n_years):
    return [1 / (1 + rate) ** t for t in range(1, n_years + 1)]


def terminal_value(final_year_fcff, wacc, terminal_growth):
    """Growing-perpetuity terminal value: TV = FCFF_n * (1+g) / (WACC - g)."""
    return final_year_fcff * (1 + terminal_growth) / (wacc - terminal_growth)


def enterprise_value(fcff_list, wacc, terminal_growth):
    dfs = discount_factors(wacc, len(fcff_list))
    pv_fcff = [f * df for f, df in zip(fcff_list, dfs)]
    tv = terminal_value(fcff_list[-1], wacc, terminal_growth)
    pv_tv = tv * dfs[-1]
    ev = sum(pv_fcff) + pv_tv
    return {
        "pv_fcff": pv_fcff,
        "sum_pv_fcff": sum(pv_fcff),
        "terminal_value": tv,
        "pv_terminal_value": pv_tv,
        "enterprise_value": ev,
    }


def main():
    print("=" * 90)
    print("STEP 1 -- Base-year unlevered FCFF")
    print("=" * 90)
    fcff0 = base_fccf()
    print(f"EBIT: INR {EBIT_0:.1f} crore | Tax rate: {TAX_RATE:.0%} | D&A: INR {DA_0:.1f} crore | "
          f"CapEx: INR {CAPEX_0:.1f} crore | ChangeNWC: INR {DELTA_NWC_0:.1f} crore")
    print(f"FCFF = EBIT*(1-tax) + D&A - CapEx - ChangeNWC = "
          f"{EBIT_0}*(1-{TAX_RATE}) + {DA_0} - {CAPEX_0} - {DELTA_NWC_0} = INR {fcff0:.2f} crore")

    print()
    print("=" * 90)
    print("STEP 2 -- 5-year FCFF projection (growth fading toward terminal growth)")
    print("=" * 90)
    fcff_projection = project_fcff(fcff0, YEARLY_GROWTH_RATES)
    for yr, (g, f) in enumerate(zip(YEARLY_GROWTH_RATES, fcff_projection), start=1):
        print(f"  Year {yr}: growth {g:.0%} -> FCFF = INR {f:.2f} crore")

    print()
    print("=" * 90)
    print("STEP 3 & 4 -- Cost of equity (CAPM) and WACC")
    print("=" * 90)
    beta = STOCK_UNIVERSE[DCF_BETA_TICKER]["beta"]
    re = cost_of_equity(beta)
    wacc, aftertax_cod = compute_wacc(re, PRETAX_COST_OF_DEBT, TAX_RATE, EQUITY_WEIGHT, DEBT_WEIGHT)
    print(f"Beta selected ({DCF_BETA_TICKER}): {beta}")
    print(f"Risk-free rate: {RISK_FREE_RATE:.2%}  |  Market return: {MARKET_RETURN:.2%}")
    print(f"Cost of equity = Rf + beta*(Rm-Rf) = {RISK_FREE_RATE:.2%} + {beta}*({MARKET_RETURN:.2%}-{RISK_FREE_RATE:.2%}) = {re:.4%}")
    print(f"Pre-tax cost of debt: {PRETAX_COST_OF_DEBT:.2%}  |  Tax rate: {TAX_RATE:.0%}  |  "
          f"After-tax cost of debt: {aftertax_cod:.4%}")
    print(f"Equity weight: {EQUITY_WEIGHT:.0%}  |  Debt weight: {DEBT_WEIGHT:.0%}")
    print(f"WACC = {EQUITY_WEIGHT:.0%}*{re:.4%} + {DEBT_WEIGHT:.0%}*{aftertax_cod:.4%} = {wacc:.4%}")

    print()
    print("=" * 90)
    print("STEP 5 -- Terminal growth constraint check")
    print("=" * 90)
    spread_base = wacc - TERMINAL_GROWTH
    print(f"Base-case WACC: {wacc:.4%}  |  Terminal growth: {TERMINAL_GROWTH:.2%}  |  "
          f"Spread: {spread_base:.4%}")
    required_min_spread = 0.03
    print(f"Terminal growth >= 3pp below base WACC: "
          f"{spread_base >= required_min_spread} (spread {spread_base:.2%} >= {required_min_spread:.0%})")

    worst_wacc = wacc - 0.01
    worst_growth = TERMINAL_GROWTH + 0.01
    worst_spread = worst_wacc - worst_growth
    print(f"Worst-case WACC - terminal growth spread: {worst_spread:.2%}")
    print(f"Terminal growth constraint satisfied (worst-case spread >= 1pp): {worst_spread >= 0.01}")
    assert worst_spread >= 0.01, "Terminal growth assumption fails the required worst-case spread -- fix assumptions."

    print()
    print("=" * 90)
    print("STEP 6 -- DCF valuation (base case)")
    print("=" * 90)
    base_result = enterprise_value(fcff_projection, wacc, TERMINAL_GROWTH)
    for yr, pv in enumerate(base_result["pv_fcff"], start=1):
        print(f"  PV of Year {yr} FCFF: INR {pv:.2f} crore")
    print(f"Sum of PV(FCFF, years 1-5): INR {base_result['sum_pv_fcff']:.2f} crore")
    print(f"Terminal value (growing perpetuity): INR {base_result['terminal_value']:.2f} crore")
    print(f"PV of terminal value: INR {base_result['pv_terminal_value']:.2f} crore")
    print(f"Enterprise value = PV(FCFFs) + PV(TV) = INR {base_result['enterprise_value']:.2f} crore")

    print()
    print("=" * 90)
    print("STEP 7 -- 3x3 sensitivity table (WACC x terminal growth, +/- 1pp)")
    print("=" * 90)
    wacc_scenarios = [wacc - 0.01, wacc, wacc + 0.01]
    growth_scenarios = [TERMINAL_GROWTH - 0.01, TERMINAL_GROWTH, TERMINAL_GROWTH + 0.01]

    sensitivity = {}
    all_cells_valid = True
    print(f"{'WACC \\ Growth':<16}" + "".join(f"{g:>12.1%}" for g in growth_scenarios))
    for w in wacc_scenarios:
        row_vals = []
        for g in growth_scenarios:
            valid = w > g
            all_cells_valid = all_cells_valid and valid
            ev = enterprise_value(fcff_projection, w, g)["enterprise_value"] if valid else float("nan")
            sensitivity[(round(w, 4), round(g, 4))] = ev
            row_vals.append(ev)
        print(f"{w:<16.2%}" + "".join(f"{v:>12.1f}" for v in row_vals))
    print(f"\n(All values are Enterprise Value in INR crore)")
    print(f"All 9 sensitivity cells satisfy WACC > terminal growth: {all_cells_valid}")
    assert all_cells_valid, "A sensitivity cell has WACC <= terminal growth -- fix assumptions."

    print()
    print("=" * 90)
    print("STEP 8 -- EV/EBITDA cross-check")
    print("=" * 90)
    ev_multiple_estimate = ILLUSTRATIVE_EBITDA * ILLUSTRATIVE_EV_EBITDA_MULTIPLE
    print(f"Illustrative EBITDA (EBIT + D&A): INR {ILLUSTRATIVE_EBITDA:.1f} crore")
    print(f"Illustrative EV/EBITDA multiple: {ILLUSTRATIVE_EV_EBITDA_MULTIPLE:.1f}x")
    print(f"EV/EBITDA-implied enterprise value: INR {ev_multiple_estimate:.2f} crore")
    print(f"DCF enterprise value: INR {base_result['enterprise_value']:.2f} crore")
    pct_diff = (base_result["enterprise_value"] - ev_multiple_estimate) / ev_multiple_estimate
    print(f"Difference (DCF vs multiple): {pct_diff:+.1%}")

    return {
        "fcff0": fcff0,
        "fcff_projection": fcff_projection,
        "wacc": wacc,
        "cost_of_equity": re,
        "terminal_growth": TERMINAL_GROWTH,
        "base_result": base_result,
        "sensitivity": sensitivity,
        "ev_multiple_estimate": ev_multiple_estimate,
        "pct_diff": pct_diff,
    }


if __name__ == "__main__":
    main()
