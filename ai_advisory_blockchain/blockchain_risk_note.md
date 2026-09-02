# Blockchain & Crypto Risk Appendix — "Paytm Crypto Insights"

This note looks at a hypothetical "Paytm Crypto Insights" feature for retail
users. It focuses on stablecoin and DeFi/DAO risks, a possible crypto
allocation, and fraud risks for a platform that combines payments, lending
and wealth products.

## Section 1 — Stablecoin and DeFi/DAO Governance Risk

Before Paytm could responsibly show crypto information to retail users, an
important distinction is between **fiat-collateralized** and **algorithmic** stablecoins, since
retail users routinely treat "stablecoin" as one safe category. Fiat-
collateralized stablecoins hold reserves — cash, short-term government
paper, bank deposits — nominally equal to the tokens in circulation. The
real risks here are reserve quality (genuinely liquid and fully backing
the float, or partly invested in riskier assets?), redemption risk (can a
holder actually convert back to fiat on demand, or does the issuer gate
redemptions under stress?), and transparency (a real-time or audited
attestation, or only the issuer's own claim?). Algorithmic stablecoins
carry a different type of risk because the peg depends on incentives and
market behaviour rather than conventional reserves. If confidence falls,
the mechanism can reinforce the decline. The 2022 TerraUSD collapse is a
well-known example. A watchlist that badges
both types identically as "stablecoin" would mislead users about what
they actually hold; Paytm would need differentiated risk labels and
explicit depeg-history disclosure per token.

For DeFi and DAOs, price alone would not be enough. The product should also
show governance and tokenomics risks, including: concentration of token
ownership and voting power A DAO can become highly concentrated if a small number of wallets control
most voting tokens. Governance attacks can also exploit voting systems,
while unaudited or new smart contracts create additional technical risk.
Finally, insider and investor token unlocks can create selling pressure
for later retail buyers. A responsible watchlist should therefore show governance concentration and
audit information alongside price rather than presenting a DeFi token in
the same way as a normal equity.

## Section 2 — Crypto Allocation Recommendation

**Recommendation: a maximum 2% portfolio allocation to crypto assets for
retail advisory users, with zero allocation as the default for
Conservative-risk-tolerance investors.**

I would keep the limit small rather than ban crypto completely because: crypto's low-to-negative
correlation with traditional equity and bond returns means a small
allocation can genuinely improve diversification even though the asset is
unattractive on a standalone basis. From a CAPM-style perspective, crypto does not provide the dividends,
coupons or business cash flows normally associated with traditional
assets. Its return mainly comes from changes in market price. There are also heavy-tailed and positively skewed returns, survivorship
bias in the assets that remain visible, and relatively high costs such as
spreads, gas fees and custody costs. A 2% cap keeps the
diversification benefit while keeping worst-case loss immaterial to any
investor's overall plan, and the zero default for Conservative investors
matches the risk-based pricing philosophy used elsewhere on this platform.

## Section 3 — T.A.N.G. Fraud Framework

For a platform combining UPI, wallet, lending and wealth, I would focus on
two social-engineering risks:

**1. Authority — fake bank/Paytm "KYC update" or "account suspension"
calls.** Fraudsters impersonate Paytm support or a bank official,
claiming an account will be frozen unless the victim "verifies" via a
screen-share app or shares an OTP. This is especially dangerous on a
platform where a single app spans payments, credit, and investments,
since a compromised login can be used to both drain a wallet and pull a
Postpaid credit line in one session. **Defense: real-time device-binding
combined with step-up authentication** — a login or high-value action
from a new/unrecognized device triggers mandatory additional
authentication (biometric or a fresh OTP tied to the registered device),
which breaks the remote-screen-share attack pattern even if the victim is
actively being coached by the scammer on the phone.

**2. Greed — fake investment/crypto "returns guaranteed" schemes**
promoted through social media or messaging apps, directing victims to
transfer funds via UPI or wallet to a "trading account." This is
particularly potent on a platform that also hosts genuine wealth-advisory
features, since it borrows legitimacy from the surrounding product.
**Defense: real-time transaction risk scoring with velocity controls** —
flagging and holding transfers to a newly-added beneficiary that are
unusually large relative to the sender's history, or that follow a burst
of similar transfers to the same beneficiary across many unrelated
sender accounts (a signature of a scaled scam collection account), for
manual review or a short cooling-off period before the funds settle.
