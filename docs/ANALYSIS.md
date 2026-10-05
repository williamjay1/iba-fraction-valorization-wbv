# Analysis definitions and interpretation

The question is whether coarse proxy screens preserve the material information
needed for conditional bottom-ash valorization decisions. All analyses are
exploratory secondary analyses. Threshold perturbations, cost scenarios and
distributional assumptions were selected for sensitivity analysis and were not
preregistered. No new experimental observations are imputed.

## Seven numerical modules

| Script | Main input and calculation | Output directory |
| --- | --- | --- |
| `analyze_quality_conditioned_credit_v110.py` | German published worksheet cells; reconcile source mass, direct avoided-calcination credit and climate/cost anchors | `quality_conditioned_credit_v110` |
| `analyze_mass_only_identification_v112.py` | German stream decomposition; sharp accepted-mass credit bounds and break-even intervals | `mass_only_identification_v112` |
| `analyze_sweden_qualification_order_v111.py` | Swedish supplementary table cells; retain source road masses and compare conditional processing allocations | `sweden_qualification_order_v111` |
| `propagate_abis_reported_variability_v111.py` | Abis published mean/SD pairs; moment-matched lognormal marginal sensitivities and dependence bounds | `abis_reported_variability_v111` |
| `audit_response_magnitude_v110.py` | Paired published responses and metadata; censoring, completeness, tolerances and source-deletion analyses | `response_magnitude_v110` |
| `analyze_design_decisions_v113.py` | Source-stratified responses and German anchors; conditional composition resolution and economic stress grids | `design_decisions_v113` |
| `analyze_same_material_v114.py` | Italian composition/mineral/leaching joins and Spanish fraction/formulation tables; comparator intersections, threshold sensitivities and conditional decision loss | `same_material_v114` |

Version suffixes retain the numerical modules' historical provenance. They do
not denote extra samples or later experimental campaigns.

## Units, functions and sign conventions

**German case.** One source functional unit (FU) is one Mg source ash. Medium
and fine clinker-directed fractions contain 170.57 and 237.36 kg/FU, respectively;
the combined candidate stream is 407.93 kg/FU. Direct credit densities are
positive avoided-calcination credits per kg of the corresponding stream.
`G = R - D + Delta` expresses net climate impact in kg CO₂-eq/FU: `R` is the
remaining source contributions, `D` the accepted direct credit, and `Delta` a
signed change in other exchanges. Negative `G` is favourable relative to the
source reference. The maximum admissible adjustment is `D - R`; a positive
margin can be exceeded by additional changed exchanges.

For accepted mass `x`, medium/fine masses `m_m,m_f`, and credit densities
`v_f > v_m`, the sharp bounds are:

```text
D_min(x) = v_m min(x,m_m) + v_f max(0,x-m_m)
D_max(x) = v_f min(x,m_f) + v_m max(0,x-m_f)
```

They assume unchanged within-fraction composition and equivalent receiving
function. The 1,001 mass-grid points per source scenario are deterministic,
not confidence intervals. An unknown diversion distribution is not estimated.

**Italian case.** Each ceiling concerns one Mg of isolated dry fraction.
CaO is converted to conditional stoichiometric CO₂ displacement potential;
identified calcite/vaterite already contain carbonate and provide the phase
correction. All 25 fraction records are retained within five plant composites.
Displayed phase precision is handled separately from left-censoring and
unquantified phases. Display-rounding sensitivity is not analytical uncertainty.
The 100 mg/kg chloride comparator is source-specific and not a kiln criterion.

**Spanish case.** Approximate feed shares are 32%, 18%, 15%, 21% and 14%. Fractions
were ground below 90 μm for mortars with 25 wt.% binder replacement. The 28-day
strength screen uses the source 75% SAI comparator. Mo is measured on dry
crushed corresponding mortars at L/S 10 L/kg; the source inert-landfill
comparator is ≤0.5 mg/kg. The same-fraction intersection has zero feed share.
The whole-mixture mortar is separately retained without adding a second yield.
Thresholds of 0.54, 0.65 and 0.70 mg/kg and a ±0.02 mg/kg analyst-selected margin are
analyst sensitivities, not estimated measurement uncertainty. Mo specimens
follow compression, so the reversed test order is not demonstrated as executable.

**Swedish case.** Source road comparisons are first reported per km constructed
road, then normalized per Mg candidate material using printed source masses.
The source geometric/density rounding discrepancy is reported rather than
silently repaired. With positive source benefit `B`, eligible share `q`, added
burden `p` and signed adjustment `Delta`, whole-batch processing gives
`p - qB + Delta`; eligible-only processing gives `q(p-B) + Delta`.
Prior eligibility must be independently available for the latter. Eligibility,
processing burden and changed exchanges are scenarios, not measured washing
results. HVO 100 and unfavourable outcomes are retained.

**Economic case.** Amounts are EUR/source Mg. Relative advantage is
`revenue - cost + reference-cost magnitude`. ±10%/±25% changes and joint adverse
perturbations are deterministic stress tests; no empirical price distribution
or absolute profitability claim is inferred.

## Paired responses and technical variability

A relative change is `100*(treated/baseline - 1)` only for compatible numerical
pairs with a positive baseline. Missing, censored, percentage-only and
direction-only values retain their status. Zero is a numerical observation;
a blank is unavailable or inapplicable and is never automatically set to zero.
Conductivity, chloride and sulfate form the salt panel; the main elemental
contrast is Cr/Cu and the broader panel retains the specified reported elements.
Conditions remain grouped by source lineage, protocol and response matrix.

The Abis module uses 200,000 draws per setting and
`numpy.random.default_rng(20261001)`. Moment-matched lognormal parameters are
`sigma²=ln(1+(SD/mean)²)` and `mu=ln(mean)-sigma²/2`. Pre/post log correlations
0, 0.5 and 0.9 are sensitivities. Reported SD and SD/√3 are distinct assumptions;
SD/√3 is not an observed standard error without the raw paired replicates.
Technical columns do not replicate plants.

For salt-decrease marginal probabilities `p1,p2,p3` and named-element-increase
probabilities `u1,u2`, unknown cross-analyte dependence gives conservative joint
bounds:

```text
lower = max(0, p1+p2+p3+max(u1,u2)-3)
upper = min(p1,p2,p3,min(1,u1+u2))
```

The separate verifier checks marginal Monte Carlo probabilities against the
analytical normal distribution of log ratios. These conditional bounds are
not European compliance probabilities or observed harm risks.

## Independent implementation checks and remaining limits

`verify_analysis.py` does not import production modules. It uses separate
feasible-composition enumeration, bisection, source-table joins, endpoint-loss
calculations and analytical probability calculations, and compares fixed rounded
reference tables. `reproduce.py` separately checks input immutability, the
38-result inventory and every reference/output SHA-256.

Successful checks establish computational and transcription consistency within
the released inputs. They do not establish industrial prospective performance,
actual qualification rates, a complete new route LCA, legal product approval,
cross-country coefficient transfer or journal acceptance. The full same-material
counterfactual processing/residual inventory remains unavailable.
