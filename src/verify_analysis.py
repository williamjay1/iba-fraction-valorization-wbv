"""Independent arithmetic, source-cell and fixed-reference-table checks.

These are implementation/transcription checks, NOT peer review, field
validation or an independently reproduced licensed-background LCA.
"""
from pathlib import Path
from collections import defaultdict
import csv, json, math, re, os, hashlib
from decimal import Decimal

ROOT=Path(os.environ.get('PROJECT30_WORK',Path(__file__).resolve().parent.parent))
OUT=ROOT/'results'/'verification'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as s:return list(csv.DictReader(s))

def close(x,y,tol=1e-8):
    assert abs(float(x)-float(y))<=tol,(x,y,tol)

def numeric(text):
    return float(text.strip().replace('−','-').replace('%',''))

def table(reference, number):
    return reference[f'Table {number}']

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reference_path=ROOT/'validation'/'reference_tables.json'
    reference=json.loads(reference_path.read_text(encoding='utf-8'))
    expected_keys=[f'Table {i}' for i in range(1,5)]+[f'Table S{i}' for i in range(1,6)]
    assert list(reference)==expected_keys, 'The nine fixed reference tables are required'
    checks=[]
    ger=ROOT/'results'/'quality_conditioned_credit_v110'
    swe=ROOT/'results'/'sweden_qualification_order_v111'
    chem=ROOT/'results'/'response_magnitude_v110'
    abis=ROOT/'results'/'abis_reported_variability_v111'
    a=read(ger/'source_anchor.csv')
    masses=read(ger/'source_mass_balance.csv')
    close(sum(float(r['mass_kg_per_source_FU']) for r in masses),1000)
    checks.append('German disjoint mass closure')
    tab=table(reference,2)
    cases=read(ger/'conditional_frontier_cases.csv')
    case_names=['both_streams_realise_direct_credit','fine_only_realises_direct_credit','medium_only_realises_direct_credit','half_each_realises_direct_credit']
    for c,r in enumerate(a,1):
        g=float(r['original_climate_kg_CO2eq_per_FU'])
        d=float(r['published_direct_calcination_credit_kg_CO2eq_per_FU'])
        remainder=float(r['remaining_source_contributions_kg_CO2eq_per_FU'])
        dm=float(r['medium_direct_credit_kg_CO2eq_per_FU'])
        df=float(r['fine_direct_credit_kg_CO2eq_per_FU'])
        close(g+d,remainder);close(dm+df,d)
        mm=float(r['source_medium_mass_kg_per_FU']);mf=float(r['source_fine_mass_kg_per_FU'])
        displayed_mass=list(map(numeric,tab[1][c].split('/')))
        close(displayed_mass[0],mf,.0051);close(displayed_mass[1],mm,.0051)
        close(numeric(tab[2][c]),100*mf/(mm+mf),.0051)
        close(numeric(tab[3][c]),100*df/d,.0051)
        displayed_credit=list(map(numeric,tab[4][c].split('/')))
        close(displayed_credit[0],df,.0051);close(displayed_credit[1],dm,.0051)
        vals=[1000*df/mf,1000*dm/mm,g,remainder]
        vals += [float(next(x for x in cases if x['source_scenario']==r['source_scenario'] and x['stress_case']==case)['maximum_signed_other_exchange_adjustment_for_climate_break_even']) for case in case_names[:3]]
        for row,v in zip(tab[5:],vals):close(numeric(row[c]),v,.0051)
    checks.append('German Table 2 masses, shares, credits, densities, source totals and margins against outputs and independent identities')
    massdir=ROOT/'results'/'mass_only_identification_v112'
    massgrid=read(massdir/'mass_only_budget_bounds.csv')
    intervals=read(massdir/'mass_only_break_even_intervals.csv')
    assert len(massgrid)==3003 and len(intervals)==3
    anchors={r['source_scenario']:r for r in a}
    # Independent constrained calculation: for any fixed accepted mass x,
    # accepted fine mass y is in [max(0,x-mm), min(x,mf)]. Evaluate feasible
    # compositions directly, not using the analysis script's min/max formula.
    def feasible_credit_limits(x,src):
        mm=float(src['source_medium_mass_kg_per_FU']);mf=float(src['source_fine_mass_kg_per_FU'])
        vm=float(src['medium_direct_credit_kg_CO2eq_per_FU'])/mm
        vf=float(src['fine_direct_credit_kg_CO2eq_per_FU'])/mf
        low=max(0,x-mm);high=min(x,mf)
        values=[(x-(low+(high-low)*i/16))*vm+(low+(high-low)*i/16)*vf for i in range(17)]
        return min(values),max(values)
    for r in massgrid:
        src=anchors[r['source_scenario']];x=float(r['accepted_mass_kg_per_FU'])
        lo,hi=feasible_credit_limits(x,src);rest=float(src['remaining_source_contributions_kg_CO2eq_per_FU'])
        close(lo,r['lower_direct_credit_kgCO2eq_per_FU']);close(hi,r['upper_direct_credit_kgCO2eq_per_FU'])
        close(lo-rest,r['lower_Delta_max']);close(hi-rest,r['upper_Delta_max'])
        proxy=float(src['published_direct_calcination_credit_kg_CO2eq_per_FU'])*x/(float(src['source_medium_mass_kg_per_FU'])+float(src['source_fine_mass_kg_per_FU']))
        close(proxy,r['uniform_mass_proxy_direct_credit']);assert lo-1e-9<=proxy<=hi+1e-9
    for c,r in enumerate(intervals,1):
        src=anchors[r['source_scenario']]
        total=float(src['source_medium_mass_kg_per_FU'])+float(src['source_fine_mass_kg_per_FU'])
        target=float(src['remaining_source_contributions_kg_CO2eq_per_FU'])
        roots=[]
        for bound in (1,0):
            left,right=0,total
            for _ in range(80):
                mid=(left+right)/2
                if feasible_credit_limits(mid,src)[bound]<target:left=mid
                else:right=mid
            roots.append((left+right)/2)
        close(roots[0],r['minimum_mass_for_possible_break_even_kg'])
        close(roots[1],r['minimum_mass_for_guaranteed_break_even_kg'])
        widths=[float(x['upper_Delta_max'])-float(x['lower_Delta_max']) for x in massgrid if x['source_scenario']==r['source_scenario']]
        close(max(widths),r['maximum_unidentified_budget_width_kgCO2eq_per_FU'])
    checks.append('All 3,003 mass-only bounds against 17 feasible compositions each; independent bisection roots')
    priority=read(ger/'fraction_priority_reversal.csv')
    for r,p in zip(a,priority):
        premium=1000*(float(r['fine_direct_credit_kg_CO2eq_per_FU'])/float(r['source_fine_mass_kg_per_FU'])-float(r['medium_direct_credit_kg_CO2eq_per_FU'])/float(r['source_medium_mass_kg_per_FU']))
        close(premium,p['fine_minus_medium_credit_density_kgCO2eq_per_Mg_stream'])
    checks.append('Marginal fraction-priority reversal identity')
    grid=read(ger/'conditional_frontier_grid.csv')
    assert len(grid)==30603
    byscenario={r['source_scenario']:r for r in a}
    for r in grid:
        s=byscenario[r['source_scenario']]
        expected=float(r['q_medium'])*float(s['medium_direct_credit_kg_CO2eq_per_FU'])+float(r['q_fine'])*float(s['fine_direct_credit_kg_CO2eq_per_FU'])-float(s['remaining_source_contributions_kg_CO2eq_per_FU'])
        close(expected,r['Delta_max_kg_CO2eq_per_FU'])
    checks.append('All 30,603 deterministic German grid cells')
    sw=read(swe/'source_anchors.csv')
    t3=table(reference,'S5')
    for row in t3[1:]:
        case=1 if row[0].startswith('Project 1') else 2
        hvo=re.search(r'HVO (10|30|100)$',row[0]).group(1)
        setting={'10':'HVO10_source_base','30':'HVO30','100':'HVO100'}[hvo]
        r=next(x for x in sw if int(x['case'])==case and x['road_type']=='single' and x['transport_setting']==setting)
        b=-1000*float(r['source_net_tCO2eq_per_km'])/float(r['MIBA_Mg_per_km'])
        close(b,r['benefit_kgCO2eq_per_Mg_MIBA'])
        close(numeric(row[1]),b,.0051);close(numeric(row[2].split(':')[0]),10/b,.00051)
        close(numeric(row[3]),b-10,.0051)
    for r in read(swe/'source_processing_rounding_checks.csv'):
        assert abs(float(r['error_kgCO2eq_per_Mg']))<=float(r['printed_rounding_bound'])
    checks.append('Every Swedish Table S5 entry; all 12 source processing increments')
    endpoints=read(chem/'endpoint_magnitudes.csv'); pairing=read(chem/'condition_pairing_evidence.csv')
    by=defaultdict(lambda:defaultdict(list))
    for r in endpoints:
        if r['relative_change_percent']:
            v=float(r['relative_change_percent']);by[r['condition_id']][r['endpoint']].append(v)
        if r['evidence_type']=='absolute_numeric_pair' and r['relative_change_percent']:
            close(float(r['relative_change_percent']),100*(float(r['treated_value'])/float(r['baseline_value'])-1))
    assert len(pairing)==56 and len({r['source_lineage_id'] for r in pairing})==8
    quantitative=[r for r in pairing if r['all_three_salts_have_numeric_relative_changes']=='True']
    absolute=[r for r in pairing if r['all_three_salts_have_absolute_numeric_pairs']=='True']
    assert len(quantitative)==47 and len(absolute)==46
    def count(pool,st,et):
        result=[]
        for r in pool:
            e=by[r['condition_id']]
            low=lambda v: v<0 if st==0 else v<=-st
            high=lambda v:v>0 if et==0 else v>=et
            if all(e[k] and all(low(v) for v in e[k]) for k in ('EC','Cl','SO4')) and any(e[k] and all(high(v) for v in e[k]) for k in ('Cr','Cu')):result.append(r)
        return len(result),len({r['source_lineage_id'] for r in result})
    assert count(quantitative,0,0)==(10,3)
    assert count(quantitative,10,20)==(9,3)
    without=[r for r in quantitative if r['study_id']!='AUDOYE2026']
    assert len(without)==17 and count(without,10,20)==(3,2)
    t4=table(reference,'S3')
    for row,cid in zip(t4[1:],('LEG-011','LEG-016','LEG-019')):
        for col,k in ((1,'EC'),(2,'Cl'),(3,'SO4')):close(numeric(row[col]),by[cid][k][0],.051)
    checks.append('Independent within-pair changes, lineage/denominator counts, common-panel contrasts and Table S3 salts')
    multi=read(ger/'source_multicategory_results.csv')
    assert len(multi)==16
    assert [sum(float(r[s])<0 for r in multi) for s in ('laboratory_scale_2023','high_ambition_2030','worst_case_2030')]==[14,14,6]
    economic=read(ger/'source_relative_cost_budget.csv')[0]
    close(float(economic['product_revenue_EUR_per_FU'])-float(economic['cost_EUR_per_FU']),economic['valorization_net_revenue_EUR_per_FU'])
    close(float(economic['valorization_net_revenue_EUR_per_FU'])-float(economic['reference_landfill_construction_net_revenue_EUR_per_FU']),economic['relative_cost_advantage_EUR_per_FU'])
    close(float(economic['relative_cost_advantage_EUR_per_FU'])/.23736,economic['additional_cost_budget_if_only_fine_is_further_conditioned_EUR_per_Mg_fine'])
    checks.append('All-category sign counts and economic reference/unit identities')
    design=ROOT/'results'/'design_decisions_v113'
    strata=read(design/'lineage_stratified_contrasts.csv')
    assert len(strata)==32
    broad={'As','Cd','Co','Cr','Cu','Hg','Ni','Pb','Sb','V','Zn'}
    for r in strata:
        panel={'Cr','Cu'} if r['panel']=='Cr_Cu' else broad
        pool=[p for p in pairing if p['source_lineage_id']==r['source_lineage_id']]
        eligible=[p for p in pool if all(by[p['condition_id']][k] for k in ('EC','Cl','SO4')) and any(by[p['condition_id']][k] for k in panel)]
        st=float(r['salt_decrease_percent']);et=float(r['element_increase_percent'])
        hits=[]
        for p in eligible:
            e=by[p['condition_id']]
            low=lambda v:v<0 if st==0 else v<=-st
            high=lambda v:v>0 if et==0 else v>=et
            if all(all(low(v) for v in e[k]) for k in ('EC','Cl','SO4')) and any(e[k] and all(high(v) for v in e[k]) for k in panel):hits.append(p)
        assert len(pool)==int(r['master_conditions']) and len(eligible)==int(r['evaluable_conditions']) and len(hits)==int(r['contrast_conditions'])
        assert ';'.join(p['condition_id'] for p in hits)==r['condition_ids']
        if eligible:close(len(hits)/len(eligible),r['descriptive_fraction'])
        else:assert r['descriptive_fraction']==''
    t5=table(reference,'S4')
    common=[r for r in strata if r['panel']=='Cr_Cu' and r['salt_decrease_percent']=='10']
    wider=[r for r in strata if r['panel']=='reported_elements' and r['salt_decrease_percent']=='10']
    assert len(t5[1:])==len(common)==8
    for row,c,b in zip(t5[1:],common,wider):
        assert c['source_lineage_id']==b['source_lineage_id']
        assert row[1]==c['master_conditions'] and row[2]==c['evaluable_conditions']
        for text,r in ((row[3],c),(row[4],b)):
            n=int(r['contrast_conditions']);N=int(r['evaluable_conditions'])
            expected=f'{n}/{N} ({100*n/N:.1f})' if N else 'Not evaluable'
            assert text==expected,(text,expected)
    checks.append('All 32 lineage-stratified records from endpoint magnitudes and every Table S4 denominator/fraction')
    C=float(economic['cost_EUR_per_FU']);V=float(economic['product_revenue_EUR_per_FU'])
    L=-float(economic['reference_landfill_construction_net_revenue_EUR_per_FU']);A=V-C+L
    for r in read(design/'economic_break_even_perturbations.csv'):
        fraction=float(r['break_even_fraction'])
        c=C*(1+fraction) if r['perturbation'] in ('cost_increase','joint_equal_adverse_fraction') else C
        v=V*(1-fraction) if r['perturbation'] in ('revenue_decrease','joint_equal_adverse_fraction') else V
        l=L*(1-fraction) if r['perturbation'] in ('reference_cost_decrease','joint_equal_adverse_fraction') else L
        close(v-c+l,0)
    egrid=read(design/'economic_stress_grid.csv');assert len(egrid)==125
    for r in egrid:
        expected=(V*(1+float(r['revenue_fractional_change']))-C*(1+float(r['cost_fractional_change']))+L*(1+float(r['reference_cost_fractional_change'])))
        close(expected,r['relative_advantage_EUR_per_FU'])
    minimum=min(float(r['relative_advantage_EUR_per_FU']) for r in egrid)
    maximum=max(float(r['relative_advantage_EUR_per_FU']) for r in egrid)
    ten=V*.9-C*1.1+L*.9
    checks.append('Economic break-even via perturbed costs/revenues/reference and all 125 grid outcomes')
    worked=read(design/'worked_design_decisions.csv');assert len(worked)==12
    for r in worked:
        src=anchors[r['source_scenario']]
        mm=float(src['source_medium_mass_kg_per_FU']);mf=float(src['source_fine_mass_kg_per_FU'])
        um=float(src['medium_direct_credit_kg_CO2eq_per_FU'])/mm;uf=float(src['fine_direct_credit_kg_CO2eq_per_FU'])/mf
        R=float(src['remaining_source_contributions_kg_CO2eq_per_FU']);x=float(r['accepted_total_mass_kg_per_FU'])
        fine=[float(r['accepted_fine_mass_low_kg']),float(r['accepted_fine_mass_high_kg'])]
        delta=[float(r['Delta_low_kgCO2eq_per_FU']),float(r['Delta_high_kgCO2eq_per_FU'])]
        assert max(0,x-mm)<=fine[0]<=fine[1]<=min(x,mf)
        nets=[R-(x-y)*um-y*uf+d for y in fine for d in delta]
        close(min(nets),r['climate_net_low']);close(max(nets),r['climate_net_high'])
        correct='benefit_for_all_bounded_values' if max(nets)<0 else 'no_strict_benefit_for_any_bounded_value' if min(nets)>=0 else 'unresolved'
        assert r['decision']==correct
        threshold=float(r['fine_mass_threshold_at_Delta_high_kg'])
        close(R-(x-threshold)*um-threshold*uf+max(delta),0)
    for r in read(design/'fraction_information_resolution.csv'):
        src=anchors[r['source_scenario']]
        premium=float(src['fine_direct_credit_kg_CO2eq_per_FU'])/float(src['source_fine_mass_kg_per_FU'])-float(src['medium_direct_credit_kg_CO2eq_per_FU'])/float(src['source_medium_mass_kg_per_FU'])
        close(float(r['maximum_fine_mass_interval_width_kg'])*premium,r['selected_credit_budget_width_kgCO2eq_per_FU'])
    wc=next(r for r in worked if r['source_scenario']=='worst_case_2030' and r['case']=='illustrative_fine_110_to_120_Delta_0_to_2')
    examples_table=table(reference,'S1')
    worst=[r for r in worked if r['source_scenario']=='worst_case_2030']
    assert len(examples_table[1:])==len(worst)==4
    for row,r in zip(examples_table[1:],worst):
        expected=f"{float(r['climate_net_low']):+.2f} to {float(r['climate_net_high']):+.2f}".replace('-','−')
        assert row[3]==expected,(row[3],expected)
    economic_table=table(reference,'S2')
    for row,r in zip(economic_table[1:],read(design/'economic_break_even_perturbations.csv')):
        close(numeric(row[1]),float(r['break_even_percent']),.000051)
    checks.append('All 12 worked envelope decisions and 12 information-resolution equations')
    checks.append('Fixed supplementary worked-decision and economic-threshold tables')
    # A lognormal ratio has an exact normal log distribution, independent
    # of the Monte Carlo implementation used by the analysis script.
    inp=read(ROOT/'results'/'paired_response_dataset_v98_2026-09-28.csv')+read(ROOT/'datasets'/'treatment_synthesis'/'abis2021_ec_leachate_pairs_v111_metadata_corrected.csv')
    aliases={'Cl':'Cl-','SO4':'SO4(2-)','EC':'electrical conductivity'}
    diagnostic=[]
    for r in read(abis/'endpoint_marginal_probabilities.csv'):
        e=aliases.get(r['endpoint'],r['endpoint'])
        src=next(x for x in inp if x['study_id']=='ABIS2021' and x['treatment_id']==r['condition'] and x['endpoint'] in (e,r['endpoint']))
        mb,mt=float(src['baseline_mean']),float(src['treated_mean'])
        divisor=1 if r['mode']=='reported_SD' else math.sqrt(3)
        vb=math.log1p((float(src['baseline_sd'])/divisor/mb)**2)
        vt=math.log1p((float(src['treated_sd'])/divisor/mt)**2)
        mu=math.log(mt/mb)-(vt-vb)/2
        sd=math.sqrt(vt+vb-2*float(r['within_endpoint_log_correlation'])*math.sqrt(vt*vb))
        cdf=lambda t:.5*(1+math.erf((math.log(t)-mu)/sd/math.sqrt(2)))
        for field,p in [('probability_ratio_at_most_0_9',cdf(.9)),('probability_ratio_at_least_1_2',1-cdf(1.2))]:
            error=abs(float(r[field])-p)
            bound=6*math.sqrt(max(p*(1-p),1/200000)/200000)+2/200000
            assert error<=bound,(r,error,bound)
            diagnostic.append({'condition':r['condition'],'endpoint':r['endpoint'],'mode':r['mode'],'rho':r['within_endpoint_log_correlation'],'event':field,'exact_probability_under_assumed_model':p,'MC_probability':r[field],'absolute_error':error,'diagnostic_tolerance':bound})
    with (OUT/'analytical_ratio_distribution_check.csv').open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(diagnostic[0]));w.writeheader();w.writerows(diagnostic)
    for r in read(abis/'unknown_cross_analyte_dependence_bounds.csv'):
        assert 0<=float(r['joint_probability_lower_bound'])<=float(r['joint_probability_upper_bound'])+1e-12<=1+1e-12
    checks.append('All 336 Monte Carlo marginal probabilities against exact log-ratio distributions; probability-bound ordering')
    # Same-material verification uses a separate join and calculation from
    # source cells, not imports/calls to the production extraction script.
    cache=ROOT/'datasets'/'same_material_v114'
    cells=json.loads((cache/'mantovani_cell_cache.json').read_text(encoding='utf-8'))
    phase=cells['1']['rows']; xrf=cells['2']['rows']; leach=cells['3']['rows']
    new=ROOT/'results'/'same_material_v114'
    Italian=read(new/'mantovani_joint_samples.csv')
    assert len(Italian)==25 and len({r['sample_key'] for r in Italian})==25
    phase_keys={};interval=None
    for col in range(2,len(phase[2])):
        if phase[3][col] is not None:interval=str(phase[3][col]).replace('_','-')
        phase_keys[(phase[2][col],interval)]=col
    xlookup={(r[0],r[1]):r for r in xrf[4:] if r[0] is not None}
    llookup={(r[0],r[1]):r for r in leach[4:] if r[0] is not None}
    independently=[]
    for r in Italian:
        plant=r['plant'];lo=float(r['fraction_lower_mm']);hi=float(r['fraction_upper_mm'])
        frac=f'{lo:g}-{hi:g}';col=phase_keys[(plant,frac)]
        xx=xlookup[(plant,hi)];ll=llookup[(plant,hi)]
        ca=float(xx[8]);known=sum(float(phase[k][col]) for k in (5,12) if isinstance(phase[k][col],(int,float)))
        ceiling=1000*(ca/100*44.0095/56.0774-known/100*44.0095/100.0869)
        close(ca,r['CaO_wt_percent']);close(known,r['identified_CaCO3_floor_wt_percent'])
        close(max(0,ceiling),r['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'])
        for name,index,divisor in [('Cl_mg_per_L',6,1),('SO4_mg_per_L',7,1),('Cu_mg_per_L',21,1000),('Cr_mg_per_L',19,1000),('Ba_mg_per_L',13,1000)]:
            close(float(ll[index])/divisor,r[name])
        assert r['mass_yield']=='not tabulated; plot only' and r['process_LCI']=='not reported'
        assert r['comparative_Cl_screen_pass']=='False'
        independently.append((r,ceiling))
    assert leach[2][2].strip()=='mg/l' and leach[2][11].strip()=='ug/l'
    audit=read(new/'mantovani_leach_censor_audit.csv');assert len(audit)==875
    for arow in audit:
        s=next(r for r in Italian if r['sample_key']==arow['sample_key'])
        original=llookup[(s['plant'],float(s['fraction_upper_mm']))][int(arow['column_index'])-1]
        assert arow['raw_token']==('' if original is None else str(original))
        assert arow['unit']==('mg/L' if int(arow['column_index'])<=11 else 'ug/L')
        if str(original).strip()=='<0':
            assert arow['status']=='left_censored_unspecified_limit' and arow['upper']==''
    assert any(a['status']=='left_censored_unspecified_limit' for a in audit)
    psummary=read(new/'mantovani_plant_priority.csv');mt4=table(reference,3)
    assert len(psummary)==len(mt4[1:])==5
    for display,r in zip(mt4[1:],psummary):
        assert display[0]==r['plant']
        for column,key in ((1,'oxide_priority_fraction'),(2,'corrected_priority_fraction')):
            assert display[column].replace('–','-')==r[key].split(':')[-1].removesuffix('mm')
        close(numeric(display[3]),r['ceiling_loss_if_oxide_priority_kg_per_Mg_fraction'],.0051)
        low,high=map(numeric,display[5].split('–'));close(low,r['Cl_min'],.051);close(high,r['Cl_max'],.051)
        candidates=[s for s in Italian if s['plant']==r['plant']]
        old=max(candidates,key=lambda x:float(x['oxide_only_CO2_ceiling_kg_per_Mg_fraction']))
        current=max(candidates,key=lambda x:float(x['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction']))
        close(float(current['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'])-float(old['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction']),r['ceiling_loss_if_oxide_priority_kg_per_Mg_fraction'])
        robust=(current['sample_key']!=old['sample_key'] and
            float(current['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'])-float(current['XRD_display_rounding_Ceiling_half_width_kg_per_Mg'])>
            float(old['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'])+float(old['XRD_display_rounding_Ceiling_half_width_kg_per_Mg']))
        assert robust==(r['display_rounding_robust_priority_change']=='True')
        assert display[4]==('Yes' if robust else 'No' if r['priority_changes']=='True' else 'No change')
    assert sum(r['priority_changes']=='True' for r in psummary)==3
    assert sum(r['display_rounding_robust_priority_change']=='True' for r in psummary)==2
    for r in read(new/'mantovani_leave_one_plant.csv'):
        selected=[s for s in psummary if s['plant']!=r['omitted_plant']]
        assert int(r['priority_changes_in_other_four'])==sum(s['priority_changes']=='True' for s in selected)
        assert int(r['Cl_screen_pass_other_four'])==0
    checks.append('25 independent Italian key/stoichiometry joins, all 875 censor/unit cells, Table 3 and leave-one-plant summaries')
    sp=read(new/'spain_joint_samples.csv');assert len(sp)==6
    st={str(i):json.loads((cache/f'marco_gibert2026_table_{i}_tables.json').read_text(encoding='utf-8'))[0] for i in (2,4,5)}
    expected_strength=[False,True,True,True,False,True]
    mt5=table(reference,4)
    for index,(r,display) in enumerate(zip(sp,mt5[1:]),1):
        assert r['reported_fraction_label']==st['2'][1][index]==st['4'][index][0]==st['5'][index][0]
        close(sum(float(st['2'][k][index]) for k in (2,4,5)),r['oxide_sum_Si_Al_Fe_wt_percent'])
        assert (r['strength_75_percent_screen_pass']=='True')==expected_strength[index-1]
        for k,column in [('Mo',3),('Cl',13),('SO4',14),('pH',15)]:
            suffix='pH' if k=='pH' else f'{k}_mg_per_kg'
            close(st['4'][index][column],r[f'raw_{suffix}']);close(st['5'][index][column],r[f'mortar_{suffix}'])
        close(numeric(display[3]),r['mortar_Mo_mg_per_kg'],.00001)
        salt_values=list(map(numeric,display[4].split('/')))
        close(salt_values[0],r['mortar_Cl_mg_per_kg']);close(salt_values[1],r['mortar_SO4_mg_per_kg'])
        if index<6:close(numeric(display[1])/100,r['approximate_feed_mass_fraction'])
    frac=sp[:5];share=lambda pool:sum(float(s['approximate_feed_mass_fraction']) for s in pool)
    close(share(frac),1)
    close(share([s for s in frac if s['strength_75_percent_screen_pass']=='True']),.54)
    close(share([s for s in frac if float(s['mortar_Mo_mg_per_kg'])<=.5]),.46)
    assert not any(s['strength_and_Mo_comparative_pass']=='True' for s in sp)
    spaudit=read(new/'spain_endpoint_screens.csv');assert len(spaudit)==168
    for row in spaudit:
        sample_index=next(i for i,s in enumerate(sp,1) if s['sample_key']==row['sample_key'])
        src=st['4'] if row['matrix']=='powdered_IBA' else st['5']
        col=src[0].index(row['analyte']);token=src[sample_index][col]
        assert token==row['raw_token'] and row['unit']=='mg/kg dry test solid'
        close(float(st['4'][7][col].replace(',','')),row['inert_comparison_limit'])
        if row['matrix']=='crushed_mortar' and row['analyte']!='Mo':
            assert row['nominal_screen_status']=='below_or_at_comparator'
    for row in read(new/'spain_joint_gate_frontier.csv'):
        limit=float(row['Mo_comparator_mg_per_kg']);margin=float(row['analyst_adverse_margin_mg_per_kg'])
        nominal=lambda value: Decimal(value)+Decimal(row['analyst_adverse_margin_mg_per_kg'])<=Decimal(row['Mo_comparator_mg_per_kg'])
        chosen=[s for s in frac if s['strength_75_percent_screen_pass']=='True' and nominal(s['mortar_Mo_mg_per_kg'])]
        close(share(chosen),row['joint_candidate_yield'])
        assert (row['bulk_mixture_strength_and_Mo_screen']=='True')==nominal(sp[-1]['mortar_Mo_mg_per_kg'])
        if row['Mo_comparator_mg_per_kg']=='0.7' and row['analyst_adverse_margin_mg_per_kg']=='0.05':
            # Exact printed equality .65+.05=.70 must not fail because
            # binary floating-point addition rounds upward.
            close(row['joint_candidate_yield'],.39)
    for row in read(new/'spain_test_order_thresholds.csv'):
        n=sum(float(s['mortar_Mo_mg_per_kg'])<=float(row['Mo_comparator_mg_per_kg']) for s in frac)
        assert int(row['Mo_first_strength_tests'])==n
        assert row['source_Mo_first_sequence_available']=='False'
        if n<5:close((5-n)*float(row['S_first_cheaper_if_cost_ratio_below']),2)
        else:assert math.isinf(float(row['S_first_cheaper_if_cost_ratio_below']))
    for row in read(new/'spain_order_equivalence.csv'):assert row['same_joint_set_for_both_orders']=='True'
    checks.append('Spanish raw/formulated release matrices, 168 endpoints, Table 4, mass intersections, all 36 margin cases and conditional test-order counts')
    regrets=read(new/'german_conditional_minimax_regret.csv');assert len(regrets)==12
    for row in regrets:
        ref=next(r for r in worked if r['source_scenario']==row['source_scenario'] and r['case']==row['case'])
        low=float(ref['climate_net_low']);high=float(ref['climate_net_high'])
        # Endpoint losses relative to an oracle with two actions, not a
        # repeat of the production max(0,g) helper.
        rloss=max(g-min(g,0) for g in (low,high));floss=max(0-min(g,0) for g in (low,high))
        close(rloss,row['recovery_worst_regret_kgCO2eq_per_source_Mg'])
        close(floss,row['reference_worst_regret_kgCO2eq_per_source_Mg'])
        close(min(rloss,floss),row['minimax_climate_regret'])
    checks.append('All 12 hypothetical German regret intervals independently checked; no Italian/Spanish qualification transplanted')
    report={
        'status':'PASS',
        'checks':checks,
        'counts':{'reference_tables_available':len(reference),
                  'mass_only_grid_cells':len(massgrid),
                  'German_conditional_grid_cells':len(grid),
                  'endpoint_magnitude_records':len(endpoints),
                  'lineage_stratified_records':len(strata),
                  'economic_grid_cells':len(egrid),
                  'worked_decisions':len(worked),
                  'Italian_linked_records':len(Italian),
                  'Italian_censor_audit_cells':len(audit),
                  'Spanish_formulations':len(sp),
                  'Spanish_endpoint_screens':len(spaudit)},
        'analytical_MC_comparisons':len(diagnostic),
        'maximum_absolute_MC_probability_error':max(r['absolute_error'] for r in diagnostic),
        'reference_tables_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        'independent_check_scope':'Production scripts are not imported. Arithmetic is checked using separately implemented feasible-composition searches, bisection, source-cell joins, endpoint loss calculations and the exact normal distribution of log ratios. Fixed reference tables are read independently of generated outputs. Input/output hashes are checked separately by the public runner.',
        'not_validated':['source prospective industrial performance','actual outlet qualification or rejection rates','full counterfactual residual inventory','EU-average performance','legal approval','editorial acceptance'],
    }
    (OUT/'analysis_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
