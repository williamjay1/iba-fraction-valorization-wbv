"""Same-material linkage and benchmark-specific qualification audit.

No treatment LCI, legal product approval, emissions factor or exact mass yield
is imputed. Italian calcination quantities are stoichiometric CEILINGS only.
Spanish strength/leaching gates are comparative tests, NOT construction EoW.
"""
from pathlib import Path
import csv, json, math, os, re, hashlib, itertools
from decimal import Decimal
import openpyxl

ROOT=Path(os.environ.get('PROJECT30_WORK',Path(__file__).resolve().parent.parent))
CACHE=ROOT/'datasets'/'same_material_v114'
OUT=ROOT/'results'/'same_material_v114'
UPPER=[.2,.3,.5,1,2]
LOWER={.2:.063,.3:.2,.5:.3,1:.5,2:1}
PLANTS=['PR','PC','TO','FE','FC']

def save(name,records):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)

def load_sources():
    """Require the distributed source-cell cache; never consult a local archive."""
    p=CACHE/'mantovani_cell_cache.json'
    if not p.is_file():
        raise FileNotFoundError(f"Required Italian source-cell cache missing: {p}")
    return json.loads(p.read_text(encoding='utf-8'))

def source_interval(token):
    """Preserve censoring; <0 in SI is not an actual zero detection limit."""
    if isinstance(token,(int,float)):
        return float(token),float(token),'rounded_zero_unresolved' if token==0 else 'reported_numeric'
    if token is None:return None,None,'missing'
    compact=re.sub(r'\s+','',str(token))
    if compact.startswith('<'):
        v=float(compact[1:])
        return 0.,v if v>0 else None,'left_censored_known_limit' if v>0 else 'left_censored_unspecified_limit'
    v=float(compact);return v,v,'reported_numeric'

def main():
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    src=load_sources();phase=src['1']['rows'];xrf=src['2']['rows'];leach=src['3']['rows']
    xkeys={};lkeys={};pkeys={}
    for i,row in enumerate(xrf[4:],5):
        if row[0] in PLANTS and row[1] in UPPER:
            key=(row[0],float(row[1]));assert key not in xkeys;xkeys[key]=(i,row)
    for i,row in enumerate(leach[4:],5):
        if row[0] in PLANTS and row[1] in UPPER:
            key=(row[0],float(row[1]));assert key not in lkeys;lkeys[key]=(i,row)
    for c in range(7,32):
        plant=phase[2][c];block=(c-2)//5;upper=UPPER[block-1]
        assert plant in PLANTS and phase[3][2+block*5] is not None
        key=(plant,float(upper));assert key not in pkeys;pkeys[key]=c
    expected={(p,float(u)) for p in PLANTS for u in UPPER}
    assert set(xkeys)==set(lkeys)==set(pkeys)==expected
    joints=[];endpoints=[];plant_results=[]
    # Source article's printed comparative limits; no current-law or clinker qualification claim.
    panel={'Cl-':100.,'SO42-':250.,'Ba':1.,'Cr':.05,'Cu':.05}
    for key in sorted(expected,key=lambda k:(PLANTS.index(k[0]),k[1])):
        xr,x=xkeys[key];lr,l=lkeys[key];pc=pkeys[key]
        ca=float(x[8]);calcite=phase[5][pc];vaterite=phase[12][pc]
        assert isinstance(calcite,(int,float))
        # Missing vaterite = unquantified, not confirmed absent; known carbonate floor only.
        known_carbonate=float(calcite)+(float(vaterite) if isinstance(vaterite,(int,float)) else 0.)
        # Display rounding only: XRD tabulated to 0.1 wt%; not analytical error bars.
        round_half_width=.05*(1+int(isinstance(vaterite,(int,float))))
        oxide_ceiling=10*ca*44.0095/56.0774
        retained_co2=10*known_carbonate*44.0095/100.0869
        ceiling=max(0.,oxide_ceiling-retained_co2)
        frac=f'{LOWER[key[1]]:g}-{key[1]:g}'
        q={'sample_key':f'Mantovani2023:{key[0]}:{frac}mm','plant':key[0],
            'fraction_lower_mm':LOWER[key[1]],'fraction_upper_mm':key[1],
            'CaO_wt_percent':ca,'calcite_wt_percent':float(calcite),'vaterite_raw':vaterite,
            'identified_CaCO3_floor_wt_percent':known_carbonate,
            'amorphous_wt_percent':float(phase[22][pc]),
            'oxide_only_CO2_ceiling_kg_per_Mg_fraction':oxide_ceiling,
            'carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction':ceiling,
            'known_carbonate_CO2_kg_per_Mg_fraction':retained_co2,
            'XRD_display_rounding_Ceiling_half_width_kg_per_Mg':10*round_half_width*44.0095/100.0869,
            'Cl_mg_per_L':float(l[6]),'SO4_mg_per_L':float(l[7]),
            'Cu_mg_per_L':float(l[21])/1000,'Cr_mg_per_L':float(l[19])/1000,
            'Ba_mg_per_L':float(l[13])/1000,
            'XRF_locator':f"Table S2 {src['2']['sheet']} row {xr}",
            'XRD_locator':f"Table S1 {src['1']['sheet']} column {openpyxl.utils.get_column_letter(pc+1)}",
            'leach_locator':f"Table S3 {src['3']['sheet']} row {lr}",
            'L_S_L_per_kg':10,'duration_h':24,'pH':'plant-owner range only, not sample value',
            'mass_yield':'not tabulated; plot only','process_LCI':'not reported',
            'functional_equivalence':'not tested for this clinker scenario',
            'interpretation':'same-plant composite/fraction, not paired aliquots or certified clinker credit'}
        assert ceiling<=oxide_ceiling and math.isclose(oxide_ceiling-ceiling,retained_co2,abs_tol=1e-9)
        joints.append(q)
        for c in range(2,37):
            token=l[c];lo,hi,status=source_interval(token)
            unit='mg/L' if c<11 else 'ug/L'
            endpoints.append({'sample_key':q['sample_key'],'analyte':leach[3][c],
                  'column_index':c+1,'raw_token':token,'unit':unit,'lower':lo,'upper':hi,
                  'status':status,'locator':f"Table S3 {src['3']['sheet']} {openpyxl.utils.get_column_letter(c+1)}{lr}"})
        q['comparative_Cl_screen_pass']=q['Cl_mg_per_L']<=100
        q['comparative_panel_pass']=all(q[field]<=limit for field,limit in
            [('Cl_mg_per_L',100),('SO4_mg_per_L',250),('Ba_mg_per_L',1),('Cr_mg_per_L',.05),('Cu_mg_per_L',.05)])
    for p in PLANTS:
        rs=[j for j in joints if j['plant']==p];o=max(rs,key=lambda r:r['oxide_only_CO2_ceiling_kg_per_Mg_fraction'])
        c=max(rs,key=lambda r:r['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'])
        plant_results.append({'plant':p,'n_fraction_records':len(rs),
            'oxide_priority_fraction':o['sample_key'],'corrected_priority_fraction':c['sample_key'],
            'priority_changes':o['sample_key']!=c['sample_key'],
            'ceiling_loss_if_oxide_priority_kg_per_Mg_fraction':c['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction']-o['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'],
            'display_rounding_robust_priority_change':c['sample_key']!=o['sample_key'] and
                c['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction']-c['XRD_display_rounding_Ceiling_half_width_kg_per_Mg']>
                o['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction']+o['XRD_display_rounding_Ceiling_half_width_kg_per_Mg'],
            'ceiling_min':min(r['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'] for r in rs),
            'ceiling_max':c['carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction'],
            'Cl_min':min(r['Cl_mg_per_L'] for r in rs),'Cl_max':max(r['Cl_mg_per_L'] for r in rs),
            'interpretation':'upper-bound composition sensitivity only; no actual route regret'})
    save('mantovani_joint_samples.csv',joints);save('mantovani_leach_censor_audit.csv',endpoints)
    save('mantovani_plant_priority.csv',plant_results)
    save('mantovani_one_plant_two_fraction_pilot.csv',[j for j in joints if j['plant']=='PR' and j['fraction_upper_mm'] in (.2,2)])

    # Spain: table rows join by identical powdered-fraction labels, NOT Italy/Germany keys.
    tables={str(i):json.loads((CACHE/f'marco_gibert2026_table_{i}_tables.json').read_text(encoding='utf-8'))[0] for i in (2,3,4,5)}
    sizes=['0-2','2-4','4-8','8-16','>16','Entire'];weights=[.32,.18,.15,.21,.14,None]
    S=[False,True,True,True,False,True] # source Sec3.2 explicit >75 vs about70/87
    spanish=[];sp_end=[]
    for i,(size,w,s) in enumerate(zip(sizes,weights,S),1):
        raw=tables['4'][i];mort=tables['5'][i]
        assert raw[0]==mort[0]==tables['2'][1][i]
        si=float(tables['2'][2][i]);al=float(tables['2'][4][i]);fe=float(tables['2'][5][i])
        rec={'sample_key':f'MarcoGibert2026:Mataro:{size}mm','reported_fraction_label':raw[0],
             'fraction':size,'approximate_feed_mass_fraction':w,
             'oxide_sum_Si_Al_Fe_wt_percent':si+al+fe,
             'chemistry_70_percent_comparative_pass':si+al+fe>=70,
             'strength_75_percent_screen_pass':s,
             'SAI_percent_reported':99 if size=='4-8' else 87 if size=='Entire' else 'about70' if size in ('0-2','>16') else '>75',
             'raw_Mo_mg_per_kg':float(raw[3]),'mortar_Mo_mg_per_kg':float(mort[3]),
             'raw_Cl_mg_per_kg':float(raw[13]),'mortar_Cl_mg_per_kg':float(mort[13]),
             'raw_SO4_mg_per_kg':float(raw[14]),'mortar_SO4_mg_per_kg':float(mort[14]),
             'raw_pH':float(raw[15]),'mortar_pH':float(mort[15]),
             'mortar_salt_comparative_pass':float(mort[13])<=800 and float(mort[14])<=1000,
             'mortar_Mo_comparative_pass':float(mort[3])<=.5,
             'strength_and_Mo_comparative_pass':s and float(mort[3])<=.5,
             'same_end_use':'25 wt% cement replacement in 28-d mortar',
             'mass_locator':'Sec 2.1 rounded approximate PSD proportions',
             'strength_locator':'Sec 3.2 and Fig5 narrative; no graph precision imputed',
             'chemical_locator':f'Table2 fraction column {i+1}',
             'release_locator':f'Table4/Table5 fraction row {i+1}',
             'process_LCI':'not reported; milling time is not electrical consumption',
             'interpretation':'SCM comparative benchmark, not legal approval or equivalent cement credit'}
        spanish.append(rec)
        for matrix,t in [('powdered_IBA',tables['4']),('crushed_mortar',tables['5'])]:
            for c in range(1,15):
                token=t[i][c];lo,hi,status=source_interval(token)
                limit=float(tables['4'][7][c].replace(',',''))
                # A printed equality passes the nominal screen; no uncertainty inferred.
                pass_supported=hi is not None and hi<=limit
                fail_supported=lo is not None and lo>limit
                sp_end.append({'sample_key':rec['sample_key'],'matrix':matrix,'analyte':t[0][c],
                   'raw_token':token,'unit':'mg/kg dry test solid','lower':lo,'upper':hi,
                   'censor_status':status,'inert_comparison_limit':limit,
                   'nominal_screen_status':'below_or_at_comparator' if pass_supported else 'exceeds_comparator' if fail_supported else 'unresolved',
                   'locator':f"Table{'4' if matrix=='powdered_IBA' else '5'} row {i+1} column {c+1}"})
    fractions=spanish[:5]
    assert math.isclose(sum(r['approximate_feed_mass_fraction'] for r in fractions),1)
    assert math.isclose(sum(r['approximate_feed_mass_fraction'] for r in fractions if r['strength_75_percent_screen_pass']),.54)
    assert sum(r['strength_and_Mo_comparative_pass'] for r in fractions)==0
    save('spain_joint_samples.csv',spanish);save('spain_endpoint_screens.csv',sp_end)
    gates=[];orders=[]
    # Comparator perturbations, not proposed lawful limits or measured errors.
    for tmo in (.45,.46,.5,.54,.63,.65,.7,.75,1.):
        for margin in (0,.02,.05,.1):
            # Adverse absolute Mo margin probes threshold robustness without guessing an SD.
            meets=lambda value: Decimal(str(value))+Decimal(str(margin))<=Decimal(str(tmo))
            passing=[r for r in fractions if r['strength_75_percent_screen_pass'] and meets(r['mortar_Mo_mg_per_kg'])]
            Y=sum(r['approximate_feed_mass_fraction'] for r in passing)
            bulk=meets(spanish[-1]['mortar_Mo_mg_per_kg'])
            gates.append({'Mo_comparator_mg_per_kg':tmo,'analyst_adverse_margin_mg_per_kg':margin,
                'strength_only_candidate_yield':.54,'joint_candidate_yield':Y,
                'bulk_mixture_strength_and_Mo_screen':bulk,
                'potential_credit_ceiling_in_units_of_verified_service_credit_per_Mg_ash':Y,
                'status':'benchmark sensitivity only; credit and treatment emissions unmeasured'})
        np=sum(r['mortar_Mo_mg_per_kg']<=tmo for r in fractions)
        strength_first=(5,3);mo_first=(np,5)
        # costs are numbers of TESTS, not money/carbon. S-first cheaper if (5-np)cS<2cM.
        thresh=2/(5-np) if np<5 else math.inf
        orders.append({'Mo_comparator_mg_per_kg':tmo,'strength_first_strength_tests':5,
           'strength_first_Mo_tests':3,'Mo_first_strength_tests':np,'Mo_first_Mo_tests':5,
           'S_first_cheaper_if_cost_ratio_below':thresh,
           'source_Mo_first_sequence_available':False,
           'reason':'source leach solids are fragments obtained after compressive strength testing',
           'status':'conditional test-count illustration ONLY if independent equivalent test solids exist; no demonstrated source reordering'})
    save('spain_joint_gate_frontier.csv',gates);save('spain_test_order_thresholds.csv',orders)
    # All orderings of two benchmark gates return the SAME candidate set; costs differ only.
    order_equivalence=[]
    for tmo in (.5,.54,.63,.65,.7):
        sset={r['sample_key'] for r in fractions if r['strength_75_percent_screen_pass']}
        mset={r['sample_key'] for r in fractions if r['mortar_Mo_mg_per_kg']<=tmo}
        assert sset.intersection(mset)==mset.intersection(sset)
        order_equivalence.append({'Mo_comparator':tmo,'same_joint_set_for_both_orders':True,
            'nominal_joint_fraction_count':len(sset.intersection(mset)),
            'not_estimated':'new-lot expected cost, test errors, available bundled-test price'})
    save('spain_order_equivalence.csv',order_equivalence)
    leave=[]
    for omitted in PLANTS:
        remaining=[r for r in plant_results if r['plant']!=omitted]
        leave.append({'omitted_plant':omitted,'priority_changes_in_other_four':sum(r['priority_changes'] for r in remaining),
            'maximum_composition_ceiling_loss':max(r['ceiling_loss_if_oxide_priority_kg_per_Mg_fraction'] for r in remaining),
            'Cl_screen_pass_other_four':sum(r['comparative_Cl_screen_pass'] for r in joints if r['plant']!=omitted),
            'interpretation':'leave-one-plant descriptive stability, not fitted/predicted generalization error'})
    save('mantovani_leave_one_plant.csv',leave)
    # Climate regret is only evaluated where both routes are assumed qualified
    # and equivalent in an existing German source-calibrated interval; never
    # assign Spanish/Italian qualification to the German material.
    worked_path=ROOT/'results'/'design_decisions_v113'/'worked_design_decisions.csv'
    if worked_path.exists():
        with worked_path.open(encoding='utf-8-sig',newline='') as f:worked=list(csv.DictReader(f))
        regret=[]
        for r in worked:
            lo=float(r['climate_net_low']);hi=float(r['climate_net_high'])
            rr=max(0,hi);rf=max(0,-lo)
            brute_r=max(g-min(0,g) for g in (lo,hi,0) if lo<=g<=hi)
            brute_f=max(-min(0,g) for g in (lo,hi,0) if lo<=g<=hi)
            assert math.isclose(rr,brute_r,abs_tol=1e-12) and math.isclose(rf,brute_f,abs_tol=1e-12)
            regret.append({'source_scenario':r['source_scenario'],'case':r['case'],
                'G_low':lo,'G_high':hi,'recovery_worst_regret_kgCO2eq_per_source_Mg':rr,
                'reference_worst_regret_kgCO2eq_per_source_Mg':rf,
                'minimax_climate_regret':min(rr,rf),
                'climate_only_action':'recovery' if rr<rf else 'reference' if rf<rr else 'tie',
                'qualification_feasibility':'assumed for both candidates; not inferred from other samples',
                'status':'hypothetical German source-calibrated interval, not observed decision loss or expected value of testing'})
        save('german_conditional_minimax_regret.csv',regret)
    report={'linked_Italian_samples':len(joints),'leach_cells':len(endpoints),'Italian_plants':5,
      'Italian_Cl_nominal_screen_pass_count':sum(r['comparative_Cl_screen_pass'] for r in joints),
      'Italian_Cl_min_max':[min(r['Cl_mg_per_L'] for r in joints),max(r['Cl_mg_per_L'] for r in joints)],
      'Italian_priority_changes':sum(r['priority_changes'] for r in plant_results),
      'Italian_display_rounding_robust_changes':sum(r['display_rounding_robust_priority_change'] for r in plant_results),
      'Italian_ceiling_loss_max':max(r['ceiling_loss_if_oxide_priority_kg_per_Mg_fraction'] for r in plant_results),
      'Spanish_independent_composites':1,'Spanish_strength_candidate_yield':.54,
      'Spanish_Mo_screen_candidate_yield':.46,'Spanish_joint_screen_yield':0,
      'Spanish_non_source_TMo_values':'analyst counterfactual comparators, not regulations',
      'limitations':['same composite fraction != matched raw replicate','Italian exact mass yields/pH/replicate SD unavailable',
         'CaO/carbonate ceiling is not service-equivalent clinker credit','mortar chemistry diluted by cement and sand; no treatment removal calculation',
         'Spain landfill comparison is not SCM/construction authorization','no complete new LCA, paired treatment LCI or certified eligibility rate'],
      'checks':['one-to-one 25-key intersection','SI unit duplication separated','known carbonate stoichiometry',
         'Spanish reported approx fractions sum to one','same exact Spanish table labels',
         'technical and Mo nominal passing sets disjoint','full censor tokens retained']}
    (OUT/'calculation_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'summary':report,'plant_results':plant_results,'Spain':spanish},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
