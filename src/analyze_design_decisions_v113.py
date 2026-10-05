"""Source-stratified chemistry and conditional design/economic decisions.

No new plant observations or estimated price distributions are introduced.
All hypothetical mass/Delta/cost perturbations are explicitly labelled.
"""
from pathlib import Path
from collections import defaultdict
import csv, json, os, math, hashlib

ROOT = Path(os.environ.get('PROJECT30_WORK', Path(__file__).resolve().parent.parent))
OUT = ROOT/'results'/'design_decisions_v113'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def save(name, rows):
    with (OUT/name).open('w', encoding='utf-8', newline='') as stream:
        writer=csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths=[ROOT/'results'/'response_magnitude_v110'/'endpoint_magnitudes.csv',
           ROOT/'results'/'response_magnitude_v110'/'condition_pairing_evidence.csv',
           ROOT/'results'/'ionic_pte_matched_conditions_v108_text_direction_sensitivity_2026-09-30.csv',
           ROOT/'results'/'quality_conditioned_credit_v110'/'source_anchor.csv',
           ROOT/'results'/'quality_conditioned_credit_v110'/'source_relative_cost_budget.csv']
    endpoints, pairing, metadata, anchors, costs = map(read, paths)
    values=defaultdict(lambda: defaultdict(list))
    for r in endpoints:
        if r['relative_change_percent']:
            values[r['condition_id']][r['endpoint']].append(float(r['relative_change_percent']))
    meta={r['condition_id']:r for r in metadata}
    bylineage=defaultdict(list)
    for r in pairing: bylineage[r['source_lineage_id']].append(r)
    strata=[]
    broad={'As','Cd','Co','Cr','Cu','Hg','Ni','Pb','Sb','V','Zn'}
    for lineage, pool in sorted(bylineage.items()):
        for panel_name, panel in [('Cr_Cu', {'Cr','Cu'}), ('reported_elements', broad)]:
            for salt_tol, element_tol in [(0,0), (10,20)]:
                eligible=[]; hits=[]
                for r in pool:
                    v=values[r['condition_id']]
                    if not all(v[k] for k in ('EC','Cl','SO4')) or not any(v[k] for k in panel): continue
                    eligible.append(r)
                    lower=lambda z:z<0 if salt_tol==0 else z<=-salt_tol
                    higher=lambda z:z>0 if element_tol==0 else z>=element_tol
                    if all(all(lower(z) for z in v[k]) for k in ('EC','Cl','SO4')) and any(v[k] and all(higher(z) for z in v[k]) for k in panel):
                        hits.append(r)
                strata.append({'source_lineage_id':lineage,'country':meta[pool[0]['condition_id']]['country'],
                    'master_conditions':len(pool),'panel':panel_name,'salt_decrease_percent':salt_tol,
                    'element_increase_percent':element_tol,'evaluable_conditions':len(eligible),
                    'absolute_salt_pair_conditions_in_denominator':sum(r['all_three_salts_have_absolute_numeric_pairs']=='True' for r in eligible),
                    'contrast_conditions':len(hits),'descriptive_fraction':len(hits)/len(eligible) if eligible else '',
                    'condition_ids':';'.join(r['condition_id'] for r in hits),
                    'interpretation':'selected nested conditions; no inferential prevalence or between-lineage significance test'})
    for panel in ('Cr_Cu','reported_elements'):
        chosen=[r for r in strata if r['panel']==panel and r['salt_decrease_percent']==10]
        assert sum(r['evaluable_conditions'] for r in chosen)==47
        assert sum(r['contrast_conditions'] for r in chosen)==(9 if panel=='Cr_Cu' else 28)
    save('lineage_stratified_contrasts.csv', strata)

    econ=costs[0]; C=float(econ['cost_EUR_per_FU']); V=float(econ['product_revenue_EUR_per_FU'])
    L=-float(econ['reference_landfill_construction_net_revenue_EUR_per_FU'])
    A=V-C+L
    thresholds=[]
    for name, base in [('cost_increase',C), ('revenue_decrease',V), ('reference_cost_decrease',L), ('joint_equal_adverse_fraction',C+V+L)]:
        t=A/base
        thresholds.append({'perturbation':name,'break_even_fraction':t,'break_even_percent':100*t,
                           'baseline_relative_advantage_EUR_per_FU':A,'status':'analytic scenario threshold, not estimated price uncertainty'})
        assert math.isclose(A-base*t,0,abs_tol=1e-12)
    save('economic_break_even_perturbations.csv', thresholds)
    stress=[]
    # Symmetric ±10/25% changes are analyst stress tests, not empirical ranges.
    for cost_shift in (-.25,-.1,0,.1,.25):
        for revenue_shift in (-.25,-.1,0,.1,.25):
            for reference_shift in (-.25,-.1,0,.1,.25):
                cp=C*(1+cost_shift);vp=V*(1+revenue_shift);lp=L*(1+reference_shift)
                stress.append({'cost_fractional_change':cost_shift,'revenue_fractional_change':revenue_shift,
                    'reference_cost_fractional_change':reference_shift,'cost_EUR_per_FU':cp,'revenue_EUR_per_FU':vp,
                    'reference_cost_magnitude_EUR_per_FU':lp,'relative_advantage_EUR_per_FU':vp-cp+lp,
                    'status':'deterministic analyst stress test, all source outlets held fixed; no probability assigned'})
    save('economic_stress_grid.csv', stress)

    examples=[]; resolution=[]
    for r in anchors:
        mm=float(r['source_medium_mass_kg_per_FU']);mf=float(r['source_fine_mass_kg_per_FU'])
        um=float(r['medium_direct_credit_kg_CO2eq_per_FU'])/mm;uf=float(r['fine_direct_credit_kg_CO2eq_per_FU'])/mf
        R=float(r['remaining_source_contributions_kg_CO2eq_per_FU']);x=(mm+mf)/2
        feasible_low=max(0,x-mm);feasible_high=min(x,mf)
        for fine_low, fine_high, delta_low, delta_high, label in [
            (feasible_low,feasible_high,0,0,'bulk_mass_only_Delta_zero'),
            (110,120,0,2,'illustrative_fine_110_to_120_Delta_0_to_2'),
            (80,90,0,2,'illustrative_fine_80_to_90_Delta_0_to_2'),
            (60,70,0,2,'illustrative_fine_60_to_70_Delta_0_to_2')]:
            assert feasible_low<=fine_low<=fine_high<=feasible_high
            dlo=um*x+(uf-um)*fine_low;dhi=um*x+(uf-um)*fine_high
            glo=R-dhi+delta_low;ghi=R-dlo+delta_high
            decision='benefit_for_all_bounded_values' if ghi<0 else 'no_strict_benefit_for_any_bounded_value' if glo>=0 else 'unresolved'
            threshold=(R+delta_high-um*x)/(uf-um)
            # Check all endpoints independently using separate mass components.
            nets=[R-((x-y)*um+y*uf)+delta for y in (fine_low,fine_high) for delta in (delta_low,delta_high)]
            assert math.isclose(min(nets),glo,abs_tol=1e-10) and math.isclose(max(nets),ghi,abs_tol=1e-10)
            examples.append({'source_scenario':r['source_scenario'],'case':label,'accepted_total_mass_kg_per_FU':x,
                'accepted_fine_mass_low_kg':fine_low,'accepted_fine_mass_high_kg':fine_high,
                'Delta_low_kgCO2eq_per_FU':delta_low,'Delta_high_kgCO2eq_per_FU':delta_high,
                'direct_credit_low':dlo,'direct_credit_high':dhi,
                'climate_net_low':glo,'climate_net_high':ghi,'decision':decision,
                'fine_mass_threshold_at_Delta_high_kg':threshold,
                'status':'source-calibrated hypothetical decision; no field measurement or observed Delta'})
        for precision in (1,2,5,10):
            width=precision/(uf-um)
            resolution.append({'source_scenario':r['source_scenario'],'selected_credit_budget_width_kgCO2eq_per_FU':precision,
                'maximum_fine_mass_interval_width_kg':width,
                'status':'analyst-selected information precision, not legal or empirical tolerance'})
    save('worked_design_decisions.csv',examples);save('fraction_information_resolution.csv',resolution)
    report={'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
            'stratified_records':len(strata),'economic_grid_records':len(stress),'worked_decisions':len(examples),
            'scope':'descriptive lineage counts, deterministic stress tests and hypothetical source-calibrated decision examples',
            'checks':['lineage totals match common/broad panel totals','economic threshold zeros','worked interval extrema'],
            'not_estimated':['empirical cost ranges','actual eligible compositions','Delta distribution','population prevalence','monetary value of testing']}
    (OUT/'calculation_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'lineages':[r for r in strata if r['panel']=='Cr_Cu' and r['salt_decrease_percent']==10],
        'economic_thresholds':thresholds,'economic_grid_min_max':[min(r['relative_advantage_EUR_per_FU'] for r in stress),max(r['relative_advantage_EUR_per_FU'] for r in stress)],
        'worst_case_examples':[r for r in examples if r['source_scenario']=='worst_case_2030'],'checks':report},indent=2))

if __name__=='__main__':main()
