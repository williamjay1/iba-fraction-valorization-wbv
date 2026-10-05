"""Conditional uncertainty analysis of published Abis means and SDs.

Technical column variability is NOT facility variability. Distribution and
within-endpoint pre/post dependence are sensitivity assumptions. Unknown
cross-analyte dependence is bounded rather than silently set independent.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

ROOT=Path(os.environ.get("PROJECT30_WORK",Path(__file__).resolve().parent.parent))
RAW=Path(os.environ.get("PROJECT30_ABIS_XML",ROOT/"public_sources"/"abis2021_public_fulltext_20261001.xml"))
SOURCE="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8201139/fullTextXML"
EC=ROOT/"datasets"/"treatment_synthesis"/"abis2021_ec_leachate_pairs_v106.csv"
LEG=ROOT/"results"/"paired_response_dataset_v98_2026-09-28.csv"
OUT=ROOT/"results"/"abis_reported_variability_v111"
N=200_000

def read(p):
    with p.open(encoding="utf-8-sig",newline="") as s:return list(csv.DictReader(s))

def save(path, rows):
    with path.open("w",encoding="utf-8",newline="") as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    if not RAW.is_file():
        raise FileNotFoundError(f"Required distributed source XML missing: {RAW}; this analysis runs offline.")
    tree=ET.fromstring(RAW.read_bytes())
    source_tables=[]
    for table in tree.findall(".//table-wrap"):
        label=" ".join(table.findtext("label",default="").split())
        if label in ("Table 3","Table 4"):
            source_tables.append({"label":label,"rows":[["".join(cell.itertext()).strip() for cell in row] for row in table.findall(".//tr")]})
    assert len(source_tables)==2
    # Numerical cross-check against table rows, including the displayed SD.
    t4=next(x for x in source_tables if x["label"]=="Table 4")
    selected=[]
    endpoint_map={"Cl-":"Cl","SO4(2-)":"SO4","Co":"Co","Ni":"Ni","Cr":"Cr","Cu":"Cu"}
    source_rows={r[0].replace('−','-'):r for r in t4["rows"] if r}
    source_rows['SO4(2-)']=source_rows['SO42-']
    for r in read(LEG):
        if r["study_id"]!="ABIS2021" or r["endpoint"] not in endpoint_map:continue
        native=source_rows[r["endpoint"]]
        plant=0 if r["source_lineage_id"].endswith("Plant-A") else 1
        arm=1 if r["treatment_id"].endswith("60min") else 2
        b=1 if plant==0 else 6; t=b+arm
        # Cells use 'mean ± sd'; decimal punctuation and typography normalized.
        for cell,mean,sd in ((native[b],r["baseline_mean"],r["baseline_sd"]),(native[t],r["treated_mean"],r["treated_sd"])):
            values=[x.strip() for x in cell.replace("−","-").split("±")]
            assert len(values)==2,(cell,native)
            assert math.isclose(float(values[0]),float(mean)) and math.isclose(float(values[1]),float(sd)),(cell,mean,sd)
        selected.append({**r,"endpoint":endpoint_map[r["endpoint"]]})
    ec_rows=read(EC)
    # Correct a derived metadata typo only; numerical EC observations unchanged.
    corrections=[]
    for r in ec_rows:
        expected="Germany" if r["source_lineage_id"].endswith("Plant-A") else "Sweden"
        if r["country"]!=expected:corrections.append({"condition":r["treatment_id"],"old_country":r["country"],"new_country":expected})
        r["country"]=expected
        t3=next(x for x in source_tables if x['label']=='Table 3')
        native=[x for x in t3['rows'] if x and x[0]=='4.0'][0 if expected=='Germany' else 1]
        arm=1 if r['treatment_id'].endswith('60min') else 2
        t=arm+1 if expected=='Germany' else arm+2
        for cell,mean,sd in ((native[1],r['baseline_mean'],r['baseline_sd']),(native[t],r['treated_mean'],r['treated_sd'])):
            values=[x.strip() for x in cell.split('±')]
            assert float(values[0])==float(mean) and float(values[1])==float(sd),(cell,mean,sd)
        selected.append({**r,"endpoint":"EC"})
    OUT.mkdir(parents=True,exist_ok=True)
    fixed=ROOT/"datasets"/"treatment_synthesis"/"abis2021_ec_leachate_pairs_v111_metadata_corrected.csv"
    # The distributed corrected cache is immutable; independently derive and
    # compare its metadata instead of rewriting an input during reproduction.
    if not fixed.is_file():
        raise FileNotFoundError(f"Required corrected EC cache missing: {fixed}")
    assert read(fixed)==ec_rows, "Corrected EC cache differs from the source-table metadata correction"
    (OUT/"source_table_audit.json").write_text(json.dumps(source_tables,indent=2)+"\n",encoding="utf-8")
    rng=np.random.default_rng(20261001)
    records=[]
    for mode in ("reported_SD","SD_divided_by_sqrt_3_sensitivity"):
        for rho in (0.0,0.5,0.9):
            for r in selected:
                mb,mt=float(r["baseline_mean"]),float(r["treated_mean"])
                scale=1 if mode=="reported_SD" else math.sqrt(3)
                sb,st=float(r["baseline_sd"])/scale,float(r["treated_sd"])/scale
                vb,vt=math.log1p((sb/mb)**2),math.log1p((st/mt)**2)
                z1=rng.standard_normal(N);z2=rng.standard_normal(N)
                before=np.exp(math.log(mb)-vb/2+math.sqrt(vb)*z1)
                after=np.exp(math.log(mt)-vt/2+math.sqrt(vt)*(rho*z1+math.sqrt(1-rho*rho)*z2))
                ratio=after/before
                records.append({"condition":r["treatment_id"],"endpoint":r["endpoint"],"country":r["country"],
                    "mode":mode,"within_endpoint_log_correlation":rho,
                    "probability_ratio_at_most_0_9":float(np.mean(ratio<=.9)),
                    "probability_ratio_at_least_1_2":float(np.mean(ratio>=1.2)),
                    "native_mean_ratio":mt/mb,"baseline_SD":float(r["baseline_sd"]),"treated_SD":float(r["treated_sd"]),
                    "interpretation":"conditional propagation under stated assumptions; not legal failure, EU prevalence or independent-material inference"})
    bounds=[]
    conditions=sorted({r["condition"] for r in records})
    for condition in conditions:
        for mode in ("reported_SD","SD_divided_by_sqrt_3_sensitivity"):
            for rho in (0.0,0.5,0.9):
                ep={r["endpoint"]:r for r in records if r["condition"]==condition and r["mode"]==mode and r["within_endpoint_log_correlation"]==rho}
                salts=[ep[k]["probability_ratio_at_most_0_9"] for k in ("EC","Cl","SO4")]
                for panel in (("Co","Ni"),("Cr","Cu")):
                    ups=[ep[k]["probability_ratio_at_least_1_2"] for k in panel]
                    # Frechet bounds allow any unknown cross-analyte dependence.
                    low=max(0,sum(salts)+max(ups)-3)
                    high=min(min(salts),min(1,sum(ups)))
                    assert low<=high+1e-10
                    low=min(low,high)  # remove machine-epsilon inversions only
                    bounds.append({"condition":condition,"mode":mode,"rho":rho,"panel":";".join(panel),
                        "joint_probability_lower_bound":low,"joint_probability_upper_bound":high,
                        "interpretation":"bounds for all salts down >=10% and any named element up >=20%, conditional on marginal lognormal model"})
    save(OUT/"endpoint_marginal_probabilities.csv",records);save(OUT/"unknown_cross_analyte_dependence_bounds.csv",bounds)
    manifest={"source":SOURCE,"raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"draws_per_endpoint_setting":N,"seed":20261001,
        "metadata_corrections":corrections,"validated_Table4_means_and_SDs":len(selected)-4,
        "assumptions":"moment-matched lognormal; within-endpoint log correlations 0, 0.5, 0.9; technical SD and SD/sqrt3 sensitivity; cross-analyte joint dependence bounded",
        "inference_limit":"No independent feedstocks simulated. SEM option not asserted to be an empirical standard error because paired covariance and raw technical replicates are unavailable.",
        "maximum_binomial_MC_SE":math.sqrt(.25/N)}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2));print(json.dumps([r for r in bounds if r['condition']=='Plant-B-abrasion-120min'],indent=2))

if __name__=="__main__":main()
