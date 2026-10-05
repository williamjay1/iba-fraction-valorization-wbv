"""Check pairing evidence and relative-change tolerance in the IBA corpus.

Percent changes printed in a source are distinguished from absolute pairs.
Direction-only evidence is never assigned a magnitude. Conditions, fractions
and months remain nested in their material lineage. Tolerances are deterministic
analytical checks, not detection limits, confidence levels or legal criteria.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(os.environ.get("PROJECT30_WORK", Path(__file__).resolve().parent.parent))
LEGACY = ROOT / "results" / "paired_response_dataset_v98_2026-09-28.csv"
AUDOYE = ROOT / "datasets" / "treatment_synthesis" / "audoye_paired_leachate_responses_v103_2026-09-28.csv"
ABIS_EC = ROOT / "datasets" / "treatment_synthesis" / "abis2021_ec_leachate_pairs_v111_metadata_corrected.csv"
CONDITIONS = ROOT / "results" / "ionic_pte_matched_conditions_v108_text_direction_sensitivity_2026-09-30.csv"
OUT = ROOT / "results" / "response_magnitude_v110"
KEY = ("study_id", "source_lineage_id", "treatment_id", "particle_fraction", "response_matrix", "leaching_protocol", "liquid_solid_ratio")
SALTS = {"ec": "EC", "conductivity": "EC", "electrical conductivity": "EC", "cl-": "Cl", "cl": "Cl", "chloride": "Cl", "so4": "SO4", "so4(2-)": "SO4", "so42-": "SO4", "sulfate": "SO4"}
PTE = {"As", "Cd", "Co", "Cr", "Cu", "Hg", "Ni", "Pb", "Sb", "V", "Zn"}


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if any(None in row for row in rows):
        raise ValueError(f"CSV schema failure: {path}")
    return rows


def num(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def canonical(name):
    lower = name.strip().lower()
    if lower in SALTS:
        return SALTS[lower]
    match = next((element for element in PTE if element.lower() == lower), None)
    return match


def pair(row, before_field, after_field, source_locator):
    before, after = num(row.get(before_field)), num(row.get(after_field))
    if before is not None and after is not None:
        pct = 100 * (after / before - 1) if before > 0 else None
        return before, after, pct, "absolute_numeric_pair", source_locator
    if row.get("baseline_value_status") == "relative_change_only_no_absolute_pair":
        pct = num(row.get("reported_percent_change"))
        if pct is not None:
            return None, None, pct, "source_reported_numeric_percent_only", source_locator
    return None, None, None, "censored_missing_or_not_quantified", source_locator


def main():
    legacy, audoye, abis, conditions = map(read, (LEGACY, AUDOYE, ABIS_EC, CONDITIONS))
    lookup = {tuple(c.get(k, "") for k in KEY): c for c in conditions if c["study_id"] != "AUDOYE2026"}
    if len(lookup) != 24:
        raise ValueError("Legacy condition identity is not one-to-one")
    aud_lookup = {(c["monthly_batch"], c["particle_fraction"], c["treatment_or_arm"], c["leaching_protocol"]): c for c in conditions if c["study_id"] == "AUDOYE2026"}
    records = []

    def append(c, endpoint, values, unit, source):
        if endpoint is None:
            return
        before, after, pct, kind, locator = values
        records.append({
            "condition_id": c["condition_id"], "study_id": c["study_id"],
            "source_lineage_id": c["source_lineage_id"], "endpoint": endpoint,
            "baseline_value": before, "treated_value": after,
            "relative_change_percent": pct, "evidence_type": kind,
            "unit_native": unit, "source_locator": locator, "source_dataset": source,
        })

    for row in legacy:
        c = lookup[tuple(row.get(k, "") for k in KEY)]
        append(c, canonical(row["endpoint"]), pair(row, "baseline_mean", "treated_mean", row["exact_locator"]), row["unit"], "frozen_v98_source_extraction")
    for row in abis:
        candidates = [c for c in conditions if c["study_id"] == "ABIS2021" and c["source_lineage_id"] == row["source_lineage_id"] and c["treatment_id"] == row["treatment_id"]]
        if len(candidates) != 1:
            raise ValueError("Abis EC failed same-lineage condition join")
        append(candidates[0], "EC", pair(row, "baseline_mean", "treated_mean", row["exact_locator"]), row["unit"], "Abis_Table3_source_transcription")
    for row in audoye:
        c = aud_lookup[(row["monthly_batch"], row["fraction_mm"], row["post_feed_condition"], row["protocol"])]
        append(c, canonical(row["variable_native"]), pair(row, "baseline_value_numeric", "post_value_numeric", f"Supplement Table {row['si_table']}; {row['sample_id_baseline']} -> {row['sample_id_post']}"), row["unit_native"], "Audoye_official_SI_transcription")
    by_condition = defaultdict(lambda: defaultdict(list))
    for row in records:
        by_condition[row["condition_id"]][row["endpoint"]].append(row)
    evidence_summary = []
    for c in conditions:
        eps = by_condition[c["condition_id"]]
        salt_rows = [r for endpoint in ("EC", "Cl", "SO4") for r in eps.get(endpoint, [])]
        has_each = all(eps.get(endpoint) for endpoint in ("EC", "Cl", "SO4"))
        abs_complete = has_each and all(r["evidence_type"] == "absolute_numeric_pair" for r in salt_rows)
        pct_complete = has_each and all(r["relative_change_percent"] is not None for r in salt_rows)
        evidence_summary.append({
            "condition_id": c["condition_id"], "study_id": c["study_id"],
            "source_lineage_id": c["source_lineage_id"],
            "previous_complete_direction_panel": c["complete_EC_Cl_SO4_direction_panel"],
            "all_three_salts_have_absolute_numeric_pairs": abs_complete,
            "all_three_salts_have_numeric_relative_changes": pct_complete,
            "salt_evidence_types": ";".join(sorted({r["evidence_type"] for r in salt_rows})),
        })

    def consistent(eps, endpoint, predicate, numeric_only):
        rows = eps.get(endpoint, [])
        return bool(rows) and all(
            r["relative_change_percent"] is not None
            and (not numeric_only or r["evidence_type"] == "absolute_numeric_pair")
            and predicate(r["relative_change_percent"])
            for r in rows
        )

    summary = []
    identified = []
    for scope in ("all_sources", "Audoye_excluded"):
        cc = [c for c in conditions if scope == "all_sources" or c["study_id"] != "AUDOYE2026"]
        for numeric_only in (False, True):
            for panel_name, panel in (("study_specific_priority_panel", PTE), ("common_Cr_Cu_panel", {"Cr", "Cu"})):
                for salt_tol in (0, 5, 10, 20):
                    for pte_tol in (0, 5, 10, 20, 50):
                        # The zero tolerance recovers the strict sign rule.
                        lower = lambda x: x < 0 if salt_tol == 0 else x <= -salt_tol
                        higher = lambda x: x > 0 if pte_tol == 0 else x >= pte_tol
                        evaluable, hits = [], []
                        for c in cc:
                            eps = by_condition[c["condition_id"]]
                            salts_evaluable = all(consistent(eps, k, lambda x: True, numeric_only) for k in ("EC", "Cl", "SO4"))
                            pte_evaluable = [p for p in sorted(panel) if consistent(eps, p, lambda x: True, numeric_only)]
                            if not salts_evaluable or not pte_evaluable:
                                continue
                            evaluable.append(c)
                            salts_down = all(consistent(eps, k, lower, numeric_only) for k in ("EC", "Cl", "SO4"))
                            pte_up = [p for p in pte_evaluable if consistent(eps, p, higher, numeric_only)]
                            if salts_down and pte_up:
                                hits.append(c)
                                if salt_tol == 10 and pte_tol == 20 and not numeric_only:
                                    identified.append({
                                        "scope": scope, "panel": panel_name, "condition_id": c["condition_id"],
                                        "source_lineage_id": c["source_lineage_id"],
                                        "higher_elements": ";".join(sorted(pte_up)),
                                        "salt_changes_percent": json.dumps({k: [r["relative_change_percent"] for r in eps[k]] for k in ("EC", "Cl", "SO4")}),
                                        "higher_element_changes_percent": json.dumps({p: [r["relative_change_percent"] for r in eps[p]] for p in pte_up}),
                                    })
                        summary.append({
                            "scope": scope, "absolute_pairs_only": numeric_only, "element_panel": panel_name,
                            "minimum_each_salt_decrease_percent": salt_tol,
                            "minimum_element_increase_percent": pte_tol,
                            "evaluable_conditions": len(evaluable),
                            "evaluable_lineages": len({c["source_lineage_id"] for c in evaluable}),
                            "counterexample_conditions": len(hits),
                            "counterexample_lineages": len({c["source_lineage_id"] for c in hits}),
                            "counterexample_lineage_ids": ";".join(sorted({c["source_lineage_id"] for c in hits})),
                            "condition_ids": ";".join(c["condition_id"] for c in hits),
                        })
    OUT.mkdir(parents=True, exist_ok=True)

    def save(name, rows):
        with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    save("endpoint_magnitudes.csv", records)
    save("condition_pairing_evidence.csv", evidence_summary)
    save("relative_change_tolerance_analysis.csv", summary)
    if identified:
        save("counterexamples_10pct_salt_20pct_element.csv", identified)
    abs_rows = [x for x in evidence_summary if x["all_three_salts_have_absolute_numeric_pairs"]]
    pct_rows = [x for x in evidence_summary if x["all_three_salts_have_numeric_relative_changes"]]
    manifest = {
        "inputs": [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in (LEGACY, AUDOYE, ABIS_EC, CONDITIONS)],
        "absolute_salt_pair_conditions": len(abs_rows),
        "absolute_salt_pair_lineages": len({x["source_lineage_id"] for x in abs_rows}),
        "numeric_relative_change_salt_conditions": len(pct_rows),
        "numeric_relative_change_salt_lineages": len({x["source_lineage_id"] for x in pct_rows}),
        "data_structure": "condition-level changes nested in material lineages; no EU prevalence or inferential meta-analysis",
        "tolerance_status": "exploratory deterministic sensitivity; no analytical error distribution or legal cut-off inferred",
        "source_direction_only_handling": "not included in magnitude analysis",
        "no_missing_or_censored_imputation": True,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    selected = [r for r in summary if not r["absolute_pairs_only"] and ((r["minimum_each_salt_decrease_percent"] == 0 and r["minimum_element_increase_percent"] == 0) or (r["minimum_each_salt_decrease_percent"] == 10 and r["minimum_element_increase_percent"] == 20))]
    print(json.dumps({"pairing_audit": manifest, "selected_tolerances": selected}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
