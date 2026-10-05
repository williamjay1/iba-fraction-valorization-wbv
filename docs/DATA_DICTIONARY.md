# Data dictionary and schemas

All CSV files use UTF-8, a header row and comma separators. A blank denotes
missing or inapplicable information; numerical zero is retained as zero.
Boolean outputs are written as `True`/`False`. Output inventories record exact
row counts, column order, file size and SHA-256 in
`validation/reference_results_manifest.json`.

## Input conventions

- `study_id`, `doi`, `citation`, `source_url` identify the publication.
- `source_lineage_id` groups records sharing a material origin; treatment rows
  and size fractions are not automatically independent samples.
- `treatment_id`, `particle_fraction`, `response_matrix`, `leaching_protocol`,
  `liquid_solid_ratio` and `duration_or_condition` define a compatible comparison.
- `endpoint` names the measured analyte or conductivity. `unit` is the source
  measurement unit; no mg/L-to-mg/kg conversion is implicit.
- `baseline_mean`, `treated_mean`, `baseline_sd`, `treated_sd` preserve reported
  values and SDs. Percentage-only and direction-only records retain that status.
- `baseline_value_status`, `treated_value_status`, `extraction_record_status`
  and limitation fields preserve censoring/access distinctions.
- `change_pct_calc`, `percent_change_calculated` and `log_response_ratio` are
  derived paired contrasts where a compatible positive baseline exists.
- `replication_note` and lineage notes distinguish technical columns, material
  composites and facilities. `exact_locator` identifies the source table/cell.
- `threshold_value`, `threshold_unit` and comparison fields apply only in the
  stated response matrix/protocol. Missing thresholds are not inferred approvals.
- `raw_source_sha256` fingerprints the originally obtained source, not the CSV.
- The original Abis EC cache retains a historical country metadata error. The
  corrected cache identifies Plant B as Sweden; numbers are unchanged. The code
  checks this explicit correction and does not overwrite either input.

German CSVs retain worksheet/cell locators. Swedish JSON retains printed table
matrices. Italian JSON retains worksheet matrices and original workbook hashes;
Spanish JSON retains the four published table matrices. These are source-cell
exports, not generated synthetic observations. The Abis XML contains the
publisher's original table markup and licence notice.

## Output field conventions

`source_scenario`, `case` and transport labels identify source scenarios.
`per_FU` uses the case-specific functional unit defined in `ANALYSIS.md`.
`kgCO2eq` is kg CO₂-equivalent. `kg_per_FU` is stream mass, `Mg` is one metric
tonne, `EUR` is euros. Fractions are 0–1; fields explicitly labelled `percent`
are 0–100. Raw/fraction and mortar release matrices are kept separate.
`lower`/`upper`, `min`/`max` and `break_even` values are conditional accounting
or sensitivity bounds unless an explicit probability field states the assumed
technical-variability model. They are not default confidence intervals.
`status`, `condition`, `interpretation` and locator columns carry essential
qualifications and should be read with numerical fields.

The exact source/transformations are documented in `SOURCES.md`; equations and
scenario choices are in `ANALYSIS.md`. The following schemas are generated from
the frozen result inventory, not inferred from column names alone.

## Frozen result schemas

### `quality_conditioned_credit_v110/conditional_frontier_cases.csv`

15 records. Columns in order:

`source_scenario`; `stress_case`; `q_medium_direct_credit`; `q_fine_direct_credit`; `realised_direct_credit_kg_CO2eq_per_FU`; `maximum_signed_other_exchange_adjustment_for_climate_break_even`; `partial_climate_if_other_exchange_adjustment_zero`; `interpretation`.

### `quality_conditioned_credit_v110/conditional_frontier_grid.csv`

30603 records. Columns in order:

`source_scenario`; `q_medium`; `q_fine`; `Delta_max_kg_CO2eq_per_FU`; `climate_if_Delta_zero`.

### `quality_conditioned_credit_v110/fraction_priority_reversal.csv`

3 records. Columns in order:

`source_scenario`; `medium_direct_credit_kgCO2eq_per_Mg_stream`; `fine_direct_credit_kgCO2eq_per_Mg_stream`; `fine_minus_medium_credit_density_kgCO2eq_per_Mg_stream`; `fine_to_medium_credit_density_ratio`; `decision_rule`.

### `quality_conditioned_credit_v110/source_anchor.csv`

3 records. Columns in order:

`source_scenario`; `source_FU`; `original_climate_kg_CO2eq_per_FU`; `published_direct_calcination_credit_kg_CO2eq_per_FU`; `remaining_source_contributions_kg_CO2eq_per_FU`; `source_medium_mass_kg_per_FU`; `source_fine_mass_kg_per_FU`; `medium_direct_credit_kg_CO2eq_per_FU`; `fine_direct_credit_kg_CO2eq_per_FU`; `fine_share_of_clinker_mass`; `fine_share_of_direct_credit`; `uniform_direct_credit_realisation_threshold_if_Delta_zero`; `leaf_sum_error`; `group_sum_error`; `stoichiometric_vs_export_credit_error`; `root_locator`; `direct_credit_locator`.

### `quality_conditioned_credit_v110/source_mass_balance.csv`

11 records. Columns in order:

`source_sheet`; `source_cell`; `source_product`; `mass_kg_per_source_FU`; `reported_destination`.

### `quality_conditioned_credit_v110/source_multicategory_results.csv`

16 records. Columns in order:

`impact_category`; `unit_native`; `laboratory_scale_2023`; `high_ambition_2030`; `worst_case_2030`; `source_locator`; `interpretation`.

### `quality_conditioned_credit_v110/source_relative_cost_budget.csv`

1 records. Columns in order:

`source_scenario`; `cost_EUR_per_FU`; `product_revenue_EUR_per_FU`; `valorization_net_revenue_EUR_per_FU`; `reference_landfill_construction_net_revenue_EUR_per_FU`; `relative_cost_advantage_EUR_per_FU`; `additional_net_cost_budget_if_reference_unchanged_EUR_per_FU`; `additional_cost_budget_if_only_fine_is_further_conditioned_EUR_per_Mg_fine`; `source_locator`; `interpretation`.

### `quality_conditioned_credit_v110/stream_credit_decomposition.csv`

6 records. Columns in order:

`source_scenario`; `stream`; `mass_kg_per_FU`; `CaCO3_mass_fraction`; `correction_CaCO3_kg_per_kg_secondary_stream`; `stoichiometric_credit_kg_CO2eq_per_FU`; `export_reconciled_credit_kg_CO2eq_per_FU`; `credit_kg_CO2eq_per_kg_stream`.

### `mass_only_identification_v112/mass_only_break_even_intervals.csv`

3 records. Columns in order:

`source_scenario`; `condition`; `clinker_stream_mass_kg_per_FU`; `minimum_mass_for_possible_break_even_kg`; `minimum_mass_for_guaranteed_break_even_kg`; `mass_only_uniform_proxy_break_even_kg`; `possible_break_even_fraction_of_clinker_mass`; `guaranteed_break_even_fraction_of_clinker_mass`; `uniform_proxy_break_even_fraction`; `maximum_unidentified_budget_width_kgCO2eq_per_FU`; `maximum_width_mass_interval_low_kg`; `maximum_width_mass_interval_high_kg`.

### `mass_only_identification_v112/mass_only_budget_bounds.csv`

3003 records. Columns in order:

`source_scenario`; `accepted_mass_fraction_of_clinker_streams`; `accepted_mass_kg_per_FU`; `lower_direct_credit_kgCO2eq_per_FU`; `upper_direct_credit_kgCO2eq_per_FU`; `uniform_mass_proxy_direct_credit`; `lower_Delta_max`; `upper_Delta_max`; `uniform_mass_proxy_Delta_max`; `climate_identification_if_Delta0`.

### `mass_only_identification_v112/mass_proxy_decision_windows.csv`

6 records. Columns in order:

`source_scenario`; `accepted_mass_case`; `accepted_mass_kg_per_FU`; `lower_true_Delta_max`; `proxy_Delta_max`; `upper_true_Delta_max`; `false_positive_Delta_window_low`; `false_positive_Delta_window_high`; `false_negative_Delta_window_low`; `false_negative_Delta_window_high`; `interpretation`.

### `sweden_qualification_order_v111/qualification_order_grid.csv`

5454 records. Columns in order:

`case`; `road_type`; `transport_setting`; `p`; `q`; `all_batch_net_if_Delta_zero`; `eligible_only_net_if_Delta_zero`; `all_batch_Delta_max`; `eligible_only_Delta_max`.

### `sweden_qualification_order_v111/qualification_order_thresholds.csv`

54 records. Columns in order:

`case`; `road_type`; `transport_setting`; `processing_kgCO2eq_per_Mg`; `all_batch_q_break_even_if_Delta_zero`; `q_break_even_printed_rounding_lower`; `q_break_even_printed_rounding_upper`; `all_batch_feasible_for_q_at_most_one`; `eligible_only_net_benefit_per_eligible_Mg`; `conditioning_order_penalty_at_q_half`; `interpretation`.

### `sweden_qualification_order_v111/source_anchors.csv`

18 records. Columns in order:

`case`; `road_type`; `transport_setting`; `source_FU`; `MIBA_Mg_per_km`; `source_net_tCO2eq_per_km`; `benefit_kgCO2eq_per_Mg_MIBA`; `locator`.

### `sweden_qualification_order_v111/source_geometry_check.csv`

3 records. Columns in order:

`road_type`; `reported_MIBA_Mg_per_km`; `geometry_times_printed_density_Mg_per_km`; `relative_mass_discrepancy_percent`; `implied_density_Mg_per_m3`; `analysis_rule`.

### `sweden_qualification_order_v111/source_processing_rounding_checks.csv`

12 records. Columns in order:

`case`; `road_type`; `processing_kgCO2eq_per_Mg`; `increment_from_source_kgCO2eq_per_Mg`; `error_kgCO2eq_per_Mg`; `printed_rounding_bound`.

### `abis_reported_variability_v111/endpoint_marginal_probabilities.csv`

168 records. Columns in order:

`condition`; `endpoint`; `country`; `mode`; `within_endpoint_log_correlation`; `probability_ratio_at_most_0_9`; `probability_ratio_at_least_1_2`; `native_mean_ratio`; `baseline_SD`; `treated_SD`; `interpretation`.

### `abis_reported_variability_v111/unknown_cross_analyte_dependence_bounds.csv`

48 records. Columns in order:

`condition`; `mode`; `rho`; `panel`; `joint_probability_lower_bound`; `joint_probability_upper_bound`; `interpretation`.

### `response_magnitude_v110/condition_pairing_evidence.csv`

56 records. Columns in order:

`condition_id`; `study_id`; `source_lineage_id`; `previous_complete_direction_panel`; `all_three_salts_have_absolute_numeric_pairs`; `all_three_salts_have_numeric_relative_changes`; `salt_evidence_types`.

### `response_magnitude_v110/counterexamples_10pct_salt_20pct_element.csv`

48 records. Columns in order:

`scope`; `panel`; `condition_id`; `source_lineage_id`; `higher_elements`; `salt_changes_percent`; `higher_element_changes_percent`.

### `response_magnitude_v110/endpoint_magnitudes.csv`

712 records. Columns in order:

`condition_id`; `study_id`; `source_lineage_id`; `endpoint`; `baseline_value`; `treated_value`; `relative_change_percent`; `evidence_type`; `unit_native`; `source_locator`; `source_dataset`.

### `response_magnitude_v110/relative_change_tolerance_analysis.csv`

160 records. Columns in order:

`scope`; `absolute_pairs_only`; `element_panel`; `minimum_each_salt_decrease_percent`; `minimum_element_increase_percent`; `evaluable_conditions`; `evaluable_lineages`; `counterexample_conditions`; `counterexample_lineages`; `counterexample_lineage_ids`; `condition_ids`.

### `design_decisions_v113/economic_break_even_perturbations.csv`

4 records. Columns in order:

`perturbation`; `break_even_fraction`; `break_even_percent`; `baseline_relative_advantage_EUR_per_FU`; `status`.

### `design_decisions_v113/economic_stress_grid.csv`

125 records. Columns in order:

`cost_fractional_change`; `revenue_fractional_change`; `reference_cost_fractional_change`; `cost_EUR_per_FU`; `revenue_EUR_per_FU`; `reference_cost_magnitude_EUR_per_FU`; `relative_advantage_EUR_per_FU`; `status`.

### `design_decisions_v113/fraction_information_resolution.csv`

12 records. Columns in order:

`source_scenario`; `selected_credit_budget_width_kgCO2eq_per_FU`; `maximum_fine_mass_interval_width_kg`; `status`.

### `design_decisions_v113/lineage_stratified_contrasts.csv`

32 records. Columns in order:

`source_lineage_id`; `country`; `master_conditions`; `panel`; `salt_decrease_percent`; `element_increase_percent`; `evaluable_conditions`; `absolute_salt_pair_conditions_in_denominator`; `contrast_conditions`; `descriptive_fraction`; `condition_ids`; `interpretation`.

### `design_decisions_v113/worked_design_decisions.csv`

12 records. Columns in order:

`source_scenario`; `case`; `accepted_total_mass_kg_per_FU`; `accepted_fine_mass_low_kg`; `accepted_fine_mass_high_kg`; `Delta_low_kgCO2eq_per_FU`; `Delta_high_kgCO2eq_per_FU`; `direct_credit_low`; `direct_credit_high`; `climate_net_low`; `climate_net_high`; `decision`; `fine_mass_threshold_at_Delta_high_kg`; `status`.

### `same_material_v114/german_conditional_minimax_regret.csv`

12 records. Columns in order:

`source_scenario`; `case`; `G_low`; `G_high`; `recovery_worst_regret_kgCO2eq_per_source_Mg`; `reference_worst_regret_kgCO2eq_per_source_Mg`; `minimax_climate_regret`; `climate_only_action`; `qualification_feasibility`; `status`.

### `same_material_v114/mantovani_joint_samples.csv`

25 records. Columns in order:

`sample_key`; `plant`; `fraction_lower_mm`; `fraction_upper_mm`; `CaO_wt_percent`; `calcite_wt_percent`; `vaterite_raw`; `identified_CaCO3_floor_wt_percent`; `amorphous_wt_percent`; `oxide_only_CO2_ceiling_kg_per_Mg_fraction`; `carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction`; `known_carbonate_CO2_kg_per_Mg_fraction`; `XRD_display_rounding_Ceiling_half_width_kg_per_Mg`; `Cl_mg_per_L`; `SO4_mg_per_L`; `Cu_mg_per_L`; `Cr_mg_per_L`; `Ba_mg_per_L`; `XRF_locator`; `XRD_locator`; `leach_locator`; `L_S_L_per_kg`; `duration_h`; `pH`; `mass_yield`; `process_LCI`; `functional_equivalence`; `interpretation`; `comparative_Cl_screen_pass`; `comparative_panel_pass`.

### `same_material_v114/mantovani_leach_censor_audit.csv`

875 records. Columns in order:

`sample_key`; `analyte`; `column_index`; `raw_token`; `unit`; `lower`; `upper`; `status`; `locator`.

### `same_material_v114/mantovani_leave_one_plant.csv`

5 records. Columns in order:

`omitted_plant`; `priority_changes_in_other_four`; `maximum_composition_ceiling_loss`; `Cl_screen_pass_other_four`; `interpretation`.

### `same_material_v114/mantovani_one_plant_two_fraction_pilot.csv`

2 records. Columns in order:

`sample_key`; `plant`; `fraction_lower_mm`; `fraction_upper_mm`; `CaO_wt_percent`; `calcite_wt_percent`; `vaterite_raw`; `identified_CaCO3_floor_wt_percent`; `amorphous_wt_percent`; `oxide_only_CO2_ceiling_kg_per_Mg_fraction`; `carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction`; `known_carbonate_CO2_kg_per_Mg_fraction`; `XRD_display_rounding_Ceiling_half_width_kg_per_Mg`; `Cl_mg_per_L`; `SO4_mg_per_L`; `Cu_mg_per_L`; `Cr_mg_per_L`; `Ba_mg_per_L`; `XRF_locator`; `XRD_locator`; `leach_locator`; `L_S_L_per_kg`; `duration_h`; `pH`; `mass_yield`; `process_LCI`; `functional_equivalence`; `interpretation`; `comparative_Cl_screen_pass`; `comparative_panel_pass`.

### `same_material_v114/mantovani_plant_priority.csv`

5 records. Columns in order:

`plant`; `n_fraction_records`; `oxide_priority_fraction`; `corrected_priority_fraction`; `priority_changes`; `ceiling_loss_if_oxide_priority_kg_per_Mg_fraction`; `display_rounding_robust_priority_change`; `ceiling_min`; `ceiling_max`; `Cl_min`; `Cl_max`; `interpretation`.

### `same_material_v114/spain_endpoint_screens.csv`

168 records. Columns in order:

`sample_key`; `matrix`; `analyte`; `raw_token`; `unit`; `lower`; `upper`; `censor_status`; `inert_comparison_limit`; `nominal_screen_status`; `locator`.

### `same_material_v114/spain_joint_gate_frontier.csv`

36 records. Columns in order:

`Mo_comparator_mg_per_kg`; `analyst_adverse_margin_mg_per_kg`; `strength_only_candidate_yield`; `joint_candidate_yield`; `bulk_mixture_strength_and_Mo_screen`; `potential_credit_ceiling_in_units_of_verified_service_credit_per_Mg_ash`; `status`.

### `same_material_v114/spain_joint_samples.csv`

6 records. Columns in order:

`sample_key`; `reported_fraction_label`; `fraction`; `approximate_feed_mass_fraction`; `oxide_sum_Si_Al_Fe_wt_percent`; `chemistry_70_percent_comparative_pass`; `strength_75_percent_screen_pass`; `SAI_percent_reported`; `raw_Mo_mg_per_kg`; `mortar_Mo_mg_per_kg`; `raw_Cl_mg_per_kg`; `mortar_Cl_mg_per_kg`; `raw_SO4_mg_per_kg`; `mortar_SO4_mg_per_kg`; `raw_pH`; `mortar_pH`; `mortar_salt_comparative_pass`; `mortar_Mo_comparative_pass`; `strength_and_Mo_comparative_pass`; `same_end_use`; `mass_locator`; `strength_locator`; `chemical_locator`; `release_locator`; `process_LCI`; `interpretation`.

### `same_material_v114/spain_order_equivalence.csv`

5 records. Columns in order:

`Mo_comparator`; `same_joint_set_for_both_orders`; `nominal_joint_fraction_count`; `not_estimated`.

### `same_material_v114/spain_test_order_thresholds.csv`

9 records. Columns in order:

`Mo_comparator_mg_per_kg`; `strength_first_strength_tests`; `strength_first_Mo_tests`; `Mo_first_strength_tests`; `Mo_first_Mo_tests`; `S_first_cheaper_if_cost_ratio_below`; `source_Mo_first_sequence_available`; `reason`; `status`.
