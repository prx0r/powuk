# cool.md — visionary stuff from the zips

> Interesting ideas, research, and future directions found in powpowpow email zips.

---

## The master equation (pow-scarcity-lab)

For technology `T`, future demand for physical input `i`:

```
new_build_demand_i(t)
  = sum_T intensity[T,i] * d(installed_base_T)/dt

maintenance_demand_i(t)
  = sum_T sum_age cohort_T(t-age) * hazard_T,i(age)

total_load_i
  = new_build + maintenance + replacement + inventory_build

supply_i = current_capacity + inventory + qualified_substitute_capacity

pressure_i = total_load_i / max(effective_supply_i, eps)
```

The better quantity is an LP dual / shadow price: **how much does system objective improve if one more unit of resource `i` becomes available?**

That makes "what becomes valuable?" mathematically testable.

---

## Seesaw mechanism (POW_SYSTEMS)

```
Innovation → ΔConstraint → ΔShadowPrice → Capital Allocation → Supply Response → Constraint Relaxation → repeat
```

This is the whole POW thesis in one line. Every constraint we detect feeds this loop.

---

## Causal assimilation latency

For physical precursor `X` and financial/narrative response `Y`:

```
L(X -> Y) = t(first statistically durable Y response) - t(first X state transition)
```

Store the full empirical lag distribution across historical shocks. A useful edge is one that repeats across episodes and survives walk-forward validation.

**Future application:** When we detect a grid constraint, how long until it shows up as a planning application? How long until a trade shortage appears in job postings? The lag distribution IS the predictive signal.

---

## Synergy detection (Rajpal / Guerrero 2025)

The important constraint may be a **combination** — not just "not enough electricians" but "not enough electricians AND not enough inverters AND not enough roof space."

Their PNAS Nexus paper uses partial information decomposition to infer synergistic input interactions without imposing a production function.

**Future application:** Detect when two constraints co-occur more than expected. (e.g. EV charger shortage + electrician shortage = compound bottleneck)

---

## Technology diffusion S-curves (Wagenvoort / Lafond 2026)

120 mature technologies show surprisingly regular S-curve diffusion. A Bayesian Bertalanffy–Richards model outperformed alternatives in out-of-sample backtests.

**Future application:** The derivative of an adoption curve is a latent physical demand curve. If heat pump adoption follows an S-curve, we can predict when installer demand will peak.

---

## Labour mobility networks (del Rio-Chanona / Mealy / Farmer)

Labour adjustment after automation depends on feasible transitions between occupations, not simply aggregate unemployed-worker counts. Skills are a production network.

**Future application:** When EV charger installation demand spikes, can solar installers retrain? The skill overlap graph tells us.

---

## Directed technical change (Acemoglu)

After detecting a new bottleneck:
- **Price effect:** the scarce thing becomes expensive → innovation to economize
- **Market-size effect:** the large market attracts complementary innovation

**Future application:** When grid constraints appear, predict where substitute/complement R&D will accelerate. Solar + battery storage as substitutes for grid capacity.

---

## Inventory amplification / bullwhip (Ferrari)

Final-demand shocks amplify upstream. Inventory behaviour explains heterogeneous output elasticities. Distributor stock snapshots and procurement timing are structurally important variables.

**Future application:** When EV charger demand spikes, does component inventory amplify or dampen the signal? Track Mouser/DigiKey stock levels as leading indicators.

---

## Finite-shock systemic criticality (Inoue & Todo)

Indirect production losses can dominate direct losses and are more persistent when substitution is difficult and networks contain complex cycles.

**Future application:** What happens if a major DNO substation goes offline? Model cascading failures through the constraint graph.

---

## Path-dependent input adoption (Carvalho / Voigtländer)

Firms/sectors are more likely to adopt inputs already used in the network neighbourhood of their existing suppliers.

**Future application:** When a new EV charger model appears, adoption probability depends on what installers already know/work with. Track supplier neighbourhood as prior for adoption likelihood.

---

## Synthetic supply networks (Ng / Mungo / Bertrand / Lafond)

When firm-to-firm links are missing, generate an ensemble of plausible supply networks consistent with observed properties. Propagate shocks across ensemble and report bottlenecks robust to network uncertainty.

**Future application:** We don't know every electrician's supply chain. Generate plausible supply networks and find constraints that appear across ALL plausible networks.

---

## Product-space / capability proximity (Hidalgo/Hausmann)

New activities/inputs are more likely near existing productive/supplier capabilities. For frontier technologies, use network proximity as a prior for which new dependencies are plausible.

**Future application:** When a region has existing electrical infrastructure, EV charger installation is more likely nearby. The constraint graph should be spatially autocorrelated.

---

## What to build next

1. **Shadow price calculator** — LP dual over the constraint graph → "what's the most valuable unit of capacity right now?"
2. **Lag distribution tracker** — measure time between constraint detection and market response
3. **Synergy detector** — find co-occurring constraints that compound
4. **Diffusion forecaster** — S-curve models for UK heat pump/EV/solar adoption
5. **Skill overlap graph** — SOC code similarity → retraining pathway predictions
6. **Inventory leading indicators** — Mouser/DigiKey stock as early warning
7. **Ensemble shock simulator** — propagate failures through plausible supply networks
