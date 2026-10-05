"""Sharp direct-credit bounds given only accepted clinker-stream mass.

Original German material/composition/function and remaining exchanges are
fixed. These are accounting bounds, not plant observations, legal acceptance
probabilities or fully inventoried rejected-material routes. Input is the
verified published-output decomposition produced by the German reanalysis.
"""
from pathlib import Path
import csv, json, os, math

ROOT = Path(os.environ.get('PROJECT30_WORK', Path(__file__).resolve().parent.parent))
OUT = ROOT/'results'/'mass_only_identification_v112'

def write(name, rows):
    with (OUT/name).open('w', encoding='utf-8', newline='') as s:
        w=csv.DictWriter(s, fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (ROOT/'results'/'quality_conditioned_credit_v110'/'source_anchor.csv').open(encoding='utf-8') as s:
        source=list(csv.DictReader(s))
    grid=[];thresholds=[];windows=[]
    for r in source:
        scenario=r['source_scenario']
        mm=float(r['source_medium_mass_kg_per_FU']);mf=float(r['source_fine_mass_kg_per_FU']);mt=mm+mf
        dm=float(r['medium_direct_credit_kg_CO2eq_per_FU']);df=float(r['fine_direct_credit_kg_CO2eq_per_FU'])
        vm=dm/mm;vf=df/mf;rest=float(r['remaining_source_contributions_kg_CO2eq_per_FU'])
        assert vf>vm>0
        bounds=lambda x:(vm*min(x,mm)+vf*max(0,x-mm), vf*min(x,mf)+vm*max(0,x-mf))
        # Smallest accepted mass reaching a credit target, cheapest/highest
        # density first. A strict benefit requires mass above the endpoint.
        def inverse(target, first_mass, first_v, second_v):
            if target<=0:return 0.0
            if target>dm+df:return None
            return target/first_v if target<=first_mass*first_v else first_mass+(target-first_mass*first_v)/second_v
        possible=inverse(rest,mf,vf,vm);guaranteed=inverse(rest,mm,vm,vf)
        assert possible is not None and guaranteed is not None
        uniform=mt*rest/(dm+df)
        thresholds.append({'source_scenario':scenario,'condition':'Delta=0; fixed source compositions and equivalent clinker function; credits proportional within each stream',
            'clinker_stream_mass_kg_per_FU':mt,'minimum_mass_for_possible_break_even_kg':possible,
            'minimum_mass_for_guaranteed_break_even_kg':guaranteed,
            'mass_only_uniform_proxy_break_even_kg':uniform,
            'possible_break_even_fraction_of_clinker_mass':possible/mt,
            'guaranteed_break_even_fraction_of_clinker_mass':guaranteed/mt,
            'uniform_proxy_break_even_fraction':uniform/mt,
            'maximum_unidentified_budget_width_kgCO2eq_per_FU':mm*(vf-vm),
            'maximum_width_mass_interval_low_kg':mm,'maximum_width_mass_interval_high_kg':mf})
        for i in range(1001):
            x=mt*i/1000;lo,hi=bounds(x);proxy=(dm+df)*x/mt
            assert lo-1e-10<=proxy and proxy<=hi+1e-10, (scenario,x,lo,proxy,hi)
            if i==0:assert abs(lo)+abs(hi)<1e-9
            if i==1000:assert math.isclose(lo,dm+df,abs_tol=1e-9) and math.isclose(hi,dm+df,abs_tol=1e-9)
            grid.append({'source_scenario':scenario,'accepted_mass_fraction_of_clinker_streams':i/1000,'accepted_mass_kg_per_FU':x,
                'lower_direct_credit_kgCO2eq_per_FU':lo,'upper_direct_credit_kgCO2eq_per_FU':hi,
                'uniform_mass_proxy_direct_credit':proxy,'lower_Delta_max':lo-rest,'upper_Delta_max':hi-rest,
                'uniform_mass_proxy_Delta_max':proxy-rest,'climate_identification_if_Delta0':
                'benefit_under_all_stream_compositions' if lo>rest else 'no_benefit_under_any_stream_composition' if hi<=rest else 'composition_changes_sign'})
        for x,name in ((mm,'medium_stream_mass'),(mf,'fine_stream_mass')):
            lo,hi=bounds(x);proxy=(dm+df)*x/mt
            windows.append({'source_scenario':scenario,'accepted_mass_case':name,'accepted_mass_kg_per_FU':x,
                'lower_true_Delta_max':lo-rest,'proxy_Delta_max':proxy-rest,'upper_true_Delta_max':hi-rest,
                'false_positive_Delta_window_low':lo-rest,'false_positive_Delta_window_high':proxy-rest,
                'false_negative_Delta_window_low':proxy-rest,'false_negative_Delta_window_high':hi-rest,
                'interpretation':'open intervals; Delta between lower bound and proxy can allow proxy benefit with a failing composition; between proxy and upper bound can allow proxy failure with a beneficial composition. Neither Delta nor accepted composition is observed.'})
        # Check sharpness by constrained one-dimensional endpoint evaluation;
        # credit is linear in fine mass for a fixed total accepted mass.
        for x in (0,mm,mf,mt/2,mt):
            xmin=max(0,x-mm);xmax=min(x,mf)
            vals=[(x-y)*vm+y*vf for y in (xmin,xmax)]
            lo,hi=bounds(x)
            assert math.isclose(min(vals),lo,abs_tol=1e-9) and math.isclose(max(vals),hi,abs_tol=1e-9)
        assert possible<=uniform<=guaranteed
    write('mass_only_budget_bounds.csv',grid)
    write('mass_only_break_even_intervals.csv',thresholds)
    write('mass_proxy_decision_windows.csv',windows)
    report={'scope':'source-output conditional partial identification; no measured diversion distribution',
        'rows':len(grid),'scenarios':len(source),'checks':['source endpoint recovery','uniform proxy inside sharp bounds','analytic bound equals constrained endpoint extrema','break-even ordering'],
        'not_validated':['actual acceptance mass or composition','counterfactual Delta','industrial source performance','legal or environmental suitability']}
    (OUT/'calculation_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checks':report,'break_even_intervals':thresholds},indent=2))

if __name__=='__main__':main()
