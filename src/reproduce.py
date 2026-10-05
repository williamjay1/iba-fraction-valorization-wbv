"""Reproduce seven analyses offline in a fresh directory; verify 38 reference CSVs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent
MODULES = (
    'analyze_quality_conditioned_credit_v110.py',
    'analyze_mass_only_identification_v112.py',
    'analyze_sweden_qualification_order_v111.py',
    'propagate_abis_reported_variability_v111.py',
    'audit_response_magnitude_v110.py',
    'analyze_design_decisions_v113.py',
    'analyze_same_material_v114.py',
)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def validated_inputs():
    records = read_json(REPO/'validation/input_manifest.json')['files']
    for item in records:
        path = REPO/item['path']
        if not path.is_file() or sha(path) != item['sha256']:
            raise ValueError(f"Input checksum mismatch: {item['path']}")
    provenance=read_json(REPO/'validation/reference_tables_provenance.json')
    if sha(REPO/'validation/reference_tables.json') != provenance['reference_tables_sha256']:
        raise ValueError('Fixed reference table checksum mismatch.')
    return records

def check_results(work):
    manifest = read_json(REPO/'validation/reference_results_manifest.json')
    expected = {r['path']: r for r in manifest['files']}
    actual = {p.relative_to(work/'results').as_posix(): p
              for module in manifest['modules']
              for p in (work/'results'/module).glob('*.csv')}
    if set(actual) != set(expected):
        raise ValueError(f"Result inventory differs: missing={sorted(set(expected)-set(actual))}, "
                         f"extra={sorted(set(actual)-set(expected))}")
    comparisons=[]
    for rel, item in expected.items():
        reference=REPO/'validation/reference_results'/rel
        if sha(reference) != item['sha256']:
            raise ValueError(f'Reference checksum mismatch: {rel}')
        output=actual[rel]
        with output.open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream)
            columns=reader.fieldnames
            count=sum(1 for _ in reader)
        comparisons.append({'path':rel,'sha256':sha(output),
                            'byte_identical':sha(output)==item['sha256'],
                            'rows_match':count==item['rows'],
                            'columns_match':columns==item['columns']})
    return comparisons

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir',type=Path,help='A new or empty writable directory.')
    parser.add_argument('--figures',action='store_true',help='Regenerate vector/1200 dpi figures; requires graphics dependencies and Arial.')
    args=parser.parse_args()
    records=validated_inputs()
    timestamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    work=(args.workdir or REPO/'temp'/f'reproduction_{timestamp}').resolve()
    if work==REPO or REPO.is_relative_to(work):
        raise ValueError('Work directory must not be the repository root or its ancestor.')
    if work.exists() and any(work.iterdir()):
        raise FileExistsError('Work directory must be empty. Existing results are never deleted.')
    work.mkdir(parents=True,exist_ok=True)
    for item in records:
        destination=work/item['path']
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REPO/item['path'],destination)
    (work/'src').mkdir()
    (work/'validation').mkdir()
    shutil.copyfile(REPO/'validation/reference_tables.json',work/'validation/reference_tables.json')
    scripts=list(MODULES)+['verify_analysis.py']
    if args.figures:
        scripts.append('make_wbv_figures_v113.py')
        shutil.copytree(REPO/'results/wbv_v113/third_party',work/'results/wbv_v113/third_party')
    for name in scripts:
        shutil.copyfile(REPO/'src'/name,work/'src'/name)
    env=dict(os.environ,PROJECT30_WORK=str(work),PYTHONUTF8='1',PYTHONOPTIMIZE='0',
             PYTHONPYCACHEPREFIX=str(work/'temp/pycache'),
             MPLCONFIGDIR=str(work/'temp/matplotlib'))
    env['PROJECT30_GERMAN_XLSX']=str(work/'original_files_not_distributed/german.xlsx')
    env['PROJECT30_SWEDISH_DOCX']=str(work/'original_files_not_distributed/swedish.docx')
    env['PROJECT30_ABIS_XML']=str(work/'public_sources/abis2021_public_fulltext_20261001.xml')
    # Historical fallback extractors cannot read external originals in this run.
    env['PROJECT30_SAME_MATERIAL_RAW']=str(work/'original_files_not_distributed')
    logs=work/'logs';logs.mkdir()
    execution=[]
    for name in scripts:
        started=time.perf_counter()
        result=subprocess.run([sys.executable,'-X','utf8',str(work/'src'/name)],
                              cwd=work,env=env,capture_output=True,text=True,encoding='utf-8')
        (logs/(Path(name).stem+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        execution.append({'script':name,'exit_code':result.returncode,
                          'elapsed_seconds':round(time.perf_counter()-started,3)})
        print(f'{name}: exit {result.returncode}',flush=True)
        if result.returncode:
            print(result.stdout+result.stderr,flush=True)
            raise SystemExit(result.returncode)
    comparisons=check_results(work)
    unchanged=all(sha(work/r['path'])==r['sha256'] and sha(REPO/r['path'])==r['sha256'] for r in records)
    packages={name:importlib.metadata.version(name) for name in ('numpy','openpyxl')}
    if args.figures:
        packages.update({name:importlib.metadata.version(name) for name in ('matplotlib','Pillow','pypdf')})
    report={'status':'PASS' if unchanged and all(c['byte_identical'] and c['rows_match'] and c['columns_match'] for c in comparisons) else 'FAIL',
            'utc_run':timestamp,'python':platform.python_version(),'platform':platform.system(),
            'packages':packages,'offline_inputs':len(records),'inputs_unchanged':unchanged,
            'module_executions':execution,'numerical_csvs':len(comparisons),
            'byte_identical_csvs':sum(c['byte_identical'] for c in comparisons),
            'independent_numerical_verifier':execution[7]['exit_code']==0,
            'figures_regenerated':args.figures,'comparisons':comparisons}
    (work/'reproduction_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'numerical_csvs':len(comparisons),
                      'byte_identical_csvs':report['byte_identical_csvs'],
                      'report':str(work/'reproduction_report.json')},indent=2),flush=True)
    if report['status']!='PASS': raise SystemExit(1)

if __name__=='__main__':
    main()
