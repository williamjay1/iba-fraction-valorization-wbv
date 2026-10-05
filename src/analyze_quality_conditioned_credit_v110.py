"""Reanalyse the published German IBA model's direct calcination credit.

This is a source-specific, partial counterfactual accounting analysis. It
does not run ecoinvent, replace the original LCA, impute regulatory pass
rates, or combine leaching data from other materials with the German feed.
All changes to non-calcination exchanges are represented by a signed
adjustment, Delta, whose allowable value is calculated rather than assumed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import warnings
from types import SimpleNamespace
from pathlib import Path

import openpyxl

ROOT = Path(os.environ.get("PROJECT30_WORK", Path(__file__).resolve().parent.parent))
RAW = Path(os.environ.get("PROJECT30_GERMAN_XLSX", ROOT / "original_files_not_distributed" / "german.xlsx"))
EXPECTED_SHA = "a8aeb1d6bfade6921bd5761eff294a8441602df7a916a535a957a846306734a9"
OUT = ROOT / "results" / "quality_conditioned_credit_v110"
SCENARIOS = (
    ("laboratory_scale_2023", "O", 6, 17, "J"),
    ("high_ambition_2030", "P", 24, 35, "J"),
    ("worst_case_2030", "Q", 44, 55, "K"),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(name: str, records: list[dict]) -> None:
    with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def n(sheet, address: str) -> float:
    value = sheet[address].value
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Not a cached numeric result: {sheet.title}!{address}: {value!r}")
    return float(value)


def main() -> None:
    warnings.filterwarnings("ignore", message="Sparkline Group extension")
    if RAW.exists():
        input_path=RAW; raw_sha=sha(RAW)
        if raw_sha != EXPECTED_SHA:raise ValueError("Immutable source hash changed")
        book = openpyxl.load_workbook(RAW, data_only=True, read_only=False)
        evidence_mode="original public workbook"
    else:
        input_path=ROOT/'datasets'/'published_output_cells'/'german_source_cells.csv'
        meta=json.loads((input_path.parent/'source_cache_manifest.json').read_text(encoding='utf-8'))
        assert meta['german_original_sha256']==EXPECTED_SHA
        raw_sha=sha(input_path);assert raw_sha==meta['german_cell_export_sha256']
        class CellSheet(dict):
            def __init__(self,title):super().__init__();self.title=title
            def __getitem__(self,key):return SimpleNamespace(value=super().get(key))
        book={}
        with input_path.open(encoding='utf-8',newline='') as s:
            for r in csv.DictReader(s):
                if r['sheet'] not in book:book[r['sheet']]=CellSheet(r['sheet'])
                book[r['sheet']][r['cell']]=json.loads(r['value_json'])
        evidence_mode="derived source-cell export; not an original workbook or full-background LCA"
    result = book["Results substitution"]
    carbon = book["CO2 balance raw meal"]
    operating = book["Operating costs-revenue"]
    params = book["Model-Parameter"]
    cf = n(carbon, "L8") / 1000.0
    primary_caco3 = n(carbon, "L13")
    medium_mass = n(carbon, "E42")
    fine_mass = n(carbon, "E43")
    gamma_medium = n(carbon, "C24") / n(carbon, "C23")
    gamma_fine = n(carbon, "C30") / n(carbon, "C29")
    source_results = []
    stream_results = []
    endpoint_results = []
    grid = []
    checks = []
    priority = []

    # Use only disjoint leaves; summary/group rows would double count.
    mass_rows = [5, 6, 7, 12, 14, 15, 16, 17, 18, 19, 20]
    mass_records = [{
        "source_sheet": "Operating costs-revenue",
        "source_cell": f"C{r}",
        "source_product": operating[f"B{r}"].value,
        "mass_kg_per_source_FU": n(operating, f"C{r}"),
        "reported_destination": operating[f"H{r}"].value or "see grouped destination",
    } for r in mass_rows]
    mass_sum = sum(r["mass_kg_per_source_FU"] for r in mass_records)
    assert math.isclose(mass_sum, 1000.0, abs_tol=1e-8), mass_sum
    assert math.isclose(medium_mass + fine_mass, 407.93, abs_tol=1e-8)

    cases = {
        "both_streams_realise_direct_credit": (1.0, 1.0),
        "fine_only_realises_direct_credit": (0.0, 1.0),
        "medium_only_realises_direct_credit": (1.0, 0.0),
        "neither_stream_realises_direct_credit": (0.0, 0.0),
        "half_each_realises_direct_credit": (0.5, 0.5),
    }
    for scenario, column, root_row, clinker_row, carbonate_column in SCENARIOS:
        original = n(result, f"G{root_row}")
        direct_credit = -n(result, f"H{clinker_row}")
        leaves = [n(result, f"{column}{r}") for r in range(6, 14)]
        groups = [n(result, f"{column}{r}") for r in (13, 16, 17, 18)]
        assert math.isclose(sum(leaves), original, abs_tol=2e-9)
        assert math.isclose(sum(groups), original, abs_tol=2e-9)
        medium_caco3 = n(carbon, f"{carbonate_column}33")
        fine_caco3 = n(carbon, f"{carbonate_column}34")
        theoretical_medium = medium_mass * cf * (
            primary_caco3 - medium_caco3 - gamma_medium * (1.0 - primary_caco3)
        )
        theoretical_fine = fine_mass * cf * (
            primary_caco3 - fine_caco3 - gamma_fine * (1.0 - primary_caco3)
        )
        theoretical_total = theoretical_medium + theoretical_fine
        discrepancy = theoretical_total - direct_credit
        # OpenLCA export rounded the direct flow to 4-7 significant digits.
        assert abs(discrepancy) < 0.0001, discrepancy
        medium_credit = direct_credit * theoretical_medium / theoretical_total
        fine_credit = direct_credit * theoretical_fine / theoretical_total
        rest = original + direct_credit
        v_medium = 1000.0 * medium_credit / medium_mass
        v_fine = 1000.0 * fine_credit / fine_mass
        priority.append({
            "source_scenario": scenario,
            "medium_direct_credit_kgCO2eq_per_Mg_stream": v_medium,
            "fine_direct_credit_kgCO2eq_per_Mg_stream": v_fine,
            "fine_minus_medium_credit_density_kgCO2eq_per_Mg_stream": v_fine-v_medium,
            "fine_to_medium_credit_density_ratio": v_fine/v_medium,
            "decision_rule": "For equal masses with source-fixed composition/function and separable marginal other-exchange burdens a_j, fine priority holds only when a_fine-a_medium < v_fine-v_medium. All common, nonlinear and changed coproduct effects still belong in Delta; no measured treatment burden is supplied.",
        })
        # q is realised direct calcination credit, not a legal pass rate.
        threshold = rest / direct_credit
        source_results.append({
            "source_scenario": scenario,
            "source_FU": "1 Mg valorized IBA in the published German model",
            "original_climate_kg_CO2eq_per_FU": original,
            "published_direct_calcination_credit_kg_CO2eq_per_FU": direct_credit,
            "remaining_source_contributions_kg_CO2eq_per_FU": rest,
            "source_medium_mass_kg_per_FU": medium_mass,
            "source_fine_mass_kg_per_FU": fine_mass,
            "medium_direct_credit_kg_CO2eq_per_FU": medium_credit,
            "fine_direct_credit_kg_CO2eq_per_FU": fine_credit,
            "fine_share_of_clinker_mass": fine_mass / (fine_mass + medium_mass),
            "fine_share_of_direct_credit": fine_credit / direct_credit,
            "uniform_direct_credit_realisation_threshold_if_Delta_zero": threshold,
            "leaf_sum_error": sum(leaves) - original,
            "group_sum_error": sum(groups) - original,
            "stoichiometric_vs_export_credit_error": discrepancy,
            "root_locator": f"Results substitution!G{root_row}",
            "direct_credit_locator": f"Results substitution!H{clinker_row}",
        })
        for stream, mass, caco3, gamma, theory, credit in (
            ("medium", medium_mass, medium_caco3, gamma_medium, theoretical_medium, medium_credit),
            ("fine", fine_mass, fine_caco3, gamma_fine, theoretical_fine, fine_credit),
        ):
            stream_results.append({
                "source_scenario": scenario, "stream": stream,
                "mass_kg_per_FU": mass, "CaCO3_mass_fraction": caco3,
                "correction_CaCO3_kg_per_kg_secondary_stream": gamma,
                "stoichiometric_credit_kg_CO2eq_per_FU": theory,
                "export_reconciled_credit_kg_CO2eq_per_FU": credit,
                "credit_kg_CO2eq_per_kg_stream": credit / mass,
            })
        for case, (q_medium, q_fine) in cases.items():
            realised = q_medium * medium_credit + q_fine * fine_credit
            headroom = realised - rest
            endpoint_results.append({
                "source_scenario": scenario, "stress_case": case,
                "q_medium_direct_credit": q_medium, "q_fine_direct_credit": q_fine,
                "realised_direct_credit_kg_CO2eq_per_FU": realised,
                "maximum_signed_other_exchange_adjustment_for_climate_break_even": headroom,
                "partial_climate_if_other_exchange_adjustment_zero": -headroom,
                "interpretation": "conditional accounting frontier; changed outlet/disposal/washing/transport exchanges must enter Delta",
            })
        for i in range(101):
            for j in range(101):
                qm, qf = i / 100.0, j / 100.0
                headroom = qm * medium_credit + qf * fine_credit - rest
                grid.append({
                    "source_scenario": scenario, "q_medium": qm, "q_fine": qf,
                    "Delta_max_kg_CO2eq_per_FU": headroom,
                    "climate_if_Delta_zero": -headroom,
                })
        checks.append({
            "scenario": scenario, "reconstruct_original": True,
            "original_recovered_at_q1_and_Delta0": math.isclose(rest-medium_credit-fine_credit, original, abs_tol=1e-9),
            "monotone_in_q_medium": medium_credit > 0,
            "monotone_in_q_fine": fine_credit > 0,
        })

    # Keep the complete 16-category published totals; no aggregation of units.
    multi = []
    for r in range(6, 22):
        multi.append({
            "impact_category": result[f"AS{r}"].value,
            "unit_native": result[f"AT{r}"].value,
            "laboratory_scale_2023": n(result, f"AU{r}"),
            "high_ambition_2030": n(result, f"AV{r}"),
            "worst_case_2030": n(result, f"AW{r}"),
            "source_locator": f"Results substitution!AS{r}:AW{r}",
            "interpretation": "original published category total; no q perturbation outside climate",
        })
    overview = book["Overview"]
    source_cost = n(overview, "L24")
    source_product_revenue = n(overview, "L25")
    source_net_revenue = source_product_revenue - source_cost
    source_reference_net_revenue = n(overview, "L27")
    source_cost_advantage = source_net_revenue - source_reference_net_revenue
    assert math.isclose(source_net_revenue, n(overview, "L26"), abs_tol=1e-10)
    assert math.isclose(source_cost_advantage, n(overview, "L28"), abs_tol=1e-10)
    economic = [{
        "source_scenario": "laboratory_scale_2023",
        "cost_EUR_per_FU": source_cost,
        "product_revenue_EUR_per_FU": source_product_revenue,
        "valorization_net_revenue_EUR_per_FU": source_net_revenue,
        "reference_landfill_construction_net_revenue_EUR_per_FU": source_reference_net_revenue,
        "relative_cost_advantage_EUR_per_FU": source_cost_advantage,
        "additional_net_cost_budget_if_reference_unchanged_EUR_per_FU": source_cost_advantage,
        "additional_cost_budget_if_only_fine_is_further_conditioned_EUR_per_Mg_fine": source_cost_advantage / (fine_mass / 1000.0),
        "source_locator": "Overview!L24:L28",
        "interpretation": "source outlets and revenues retained; this is the extra net cost budget if only the fine stream is further conditioned, NOT a fine-only reuse route; negative absolute net revenue does not equal lack of advantage over the negative reference",
    }]
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv("source_anchor.csv", source_results)
    write_csv("stream_credit_decomposition.csv", stream_results)
    write_csv("conditional_frontier_cases.csv", endpoint_results)
    write_csv("conditional_frontier_grid.csv", grid)
    write_csv("source_mass_balance.csv", mass_records)
    write_csv("source_multicategory_results.csv", multi)
    write_csv("source_relative_cost_budget.csv", economic)
    write_csv("fraction_priority_reversal.csv", priority)
    manifest = {
        "analysis": "public-output reanalysis of a named German model",
        "source_doi": "10.1016/j.wasman.2026.115762",
        "input": (input_path.relative_to(ROOT).as_posix() if input_path.is_relative_to(ROOT) else input_path.name), "input_sha256": raw_sha,
        "original_workbook_sha256":EXPECTED_SHA,
        "source_evidence_mode":evidence_mode,
        "source_not_modified": sha(input_path) == raw_sha,
        "mass_closure_kg": mass_sum,
        "total_electricity_kWh_per_FU": n(operating, "R19"),
        "gas_GJ_per_FU": n(params, "E12") / (n(params, "E8") / n(params, "E7")),
        "equation": "G_cf = G_source + D_source - q_medium*D_medium - q_fine*D_fine + Delta",
        "Delta_definition": "signed difference in all remaining exchanges vs the source scenario; includes rejected product fate, changed substitution, transport, wastewater, further treatment and end-of-life effects",
        "q_definition": "fraction of each stream's baseline direct calcination credit realised under the fixed source composition/correction; not measured acceptance or legal compliance probability",
        "carbon_credit_scope": "avoided kiln calcination; no permanent carbonation-removal credit added",
        "scenario_grid": "q_medium and q_fine: 0..1 at 0.01 spacing; deterministic stress grid, not sampled probabilities",
        "checks": checks,
        "claims_not_supported": [
            "EU-average IBA performance", "observed treatment rejection rates",
            "a full counterfactual LCA without Delta inventories", "field safety",
            "net climate benefit of a specific rejected-product route", "economic profitability",
        ],
        "economic_scope": "2023 laboratory-based model scenario only; source reference is landfill construction; all new costs, lost revenues and reference changes enter a separate net cost adjustment",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"source_anchors": source_results, "endpoint_cases": endpoint_results, "checks": checks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
