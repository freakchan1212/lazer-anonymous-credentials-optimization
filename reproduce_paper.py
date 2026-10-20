#!/usr/bin/env python3
"""One read-only-source entry: verify receipts, audit archived parameters, rebuild current paper Figs1-7/tables."""
import argparse,datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;P=R/'project';sys.path.insert(0,str(P))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def safe(base,rel):
 p=(base/rel).resolve()
 if not p.is_relative_to(base.resolve()):raise ValueError('Unsafe manifest path '+rel)
 return p
def integrity(batch):
 config=json.loads((batch/'config.json').read_text());artifacts=[];verifications=[];sources=[]
 for manifest in sorted((batch/'artifacts').glob('*/SHA256.json')):
  for rel,expected in json.loads(manifest.read_text()).items():
   f=safe(manifest.parent,rel)
   if not f.is_file() or sha(f)!=expected:raise RuntimeError('Artifact integrity failure: '+str(f))
   artifacts.append(dict(variant=manifest.parent.name,file=rel,sha256=expected))
 for f in sorted((batch/'verification').glob('*.receipt.json')):
  r=json.loads(f.read_text());data=f.with_name(f.name.replace('.receipt.json','.jsonl'))
  if sha(data)!=r['sha256']:raise RuntimeError('Verification receipt mismatch: '+str(data))
  rows=[json.loads(x) for x in data.read_text().splitlines() if x.strip()]
  if len(rows)!=r['rows'] or any(x['status'] not in ['PASSED','ACCEPTED'] for x in rows):raise RuntimeError('Verification rows failed: '+str(data))
  verifications.append(dict(file=data.name,rows=len(rows),sha256=r['sha256']))
 for rel,expected in config['script_hashes'].items():
  current=safe(R,rel);original=R/'original_audit_scripts'/Path(rel).name
  if current.exists() and sha(current)==expected:used=current;label='CURRENT_MATCHES_ORIGINAL_BATCH'
  elif original.is_file() and sha(original)==expected:used=original;label='PRESERVED_ORIGINAL_BATCH_SOURCE; CURRENT_POSTPROCESSING_PATCHED'
  else:raise RuntimeError('Original experiment source fingerprint unavailable: '+rel)
  sources.append(dict(original_path=rel,matched_path=str(used.relative_to(R)),sha256=expected,status=label))
 if config['mode']!='full':raise RuntimeError('Current-paper reproduction requires full data; smoke/pilot cannot be substituted')
 if json.loads((batch/'verification/PASSED.json').read_text())['status']!='PASSED':raise RuntimeError('Native regression record not PASSED')
 return dict(status='PASSED',archived_artifact_files=len(artifacts),verification_receipts=len(verifications),original_script_fingerprints=len(sources),artifacts=artifacts,verification=verifications,original_sources=sources,native_regressions_reexecuted=False)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--batch',type=Path,default=R/'results/full');ap.add_argument('--output',type=Path);ap.add_argument('--allow-new-data',action='store_true',help='export changed measurements instead of enforcing current manuscript display values');a=ap.parse_args();b=a.batch.resolve()
 out=a.output.resolve() if a.output else R/('paper_reproduced_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
 if out.exists() and any(out.iterdir()):raise SystemExit('Output is not empty; choose a new --output. Raw/derived historical data will not be overwritten.')
 if out==b or b in out.parents:raise SystemExit('--output must be outside original batch')
 out.mkdir(parents=True,exist_ok=True);os.environ['MPLBACKEND']='Agg';os.environ['MPLCONFIGDIR']=str(out/'matplotlib_cache');os.environ['PYTHONDONTWRITEBYTECODE']='1'
 src=dict(status='RUNNING',batch=str(b),paper=json.loads((R/'paper_reference/PROVENANCE.json').read_text()),config_sha256=sha(b/'config.json'),plan_sha256=sha(b/'plan.json'),scope='Postprocess existing recorded full batch; no new benchmark/native proof run; current paper Figures1..7',figure_sources={
 'fig1_statement_lifecycle':'draw_schematics.py / qualitative method schematic',
 'fig2_witness_compaction':'draw_schematics.py / qualitative method schematic',
 'fig3_main_strict':'raw main strict nonwarmup / derived/main_summary.csv',
 'fig4_ols_and_block_effects':'raw main strict / derived/main_summary.csv and block_effects.csv; all30 blocks, negatives preserved',
 'fig5_latency_ecdf':'all600 per strict main group / derived/samples.csv; full tail',
 'fig6_reuse_amortization':'raw reuse / derived/reuse.csv; mean and observed min-max over3 lifecycles, NOT CI',
 'fig7_same_k_size':'raw k_sweep / derived/k_sweep.csv; mean and observed min-max over30 samples'})
 src['reproduction_source_hashes']={str(p.relative_to(R)):sha(p) for p in [R/'reproduce_paper.py',R/'summarize_e4.py',R/'paper_tables.py',R/'paper_fonts.py',R/'plot_paper.py',R/'draw_schematics.py',R/'paper_reference/tables_transcribed.json',P/'security_audit.py',P/'security_models_optional.py',P/'security_metrics.py',P/'security_parameters.py',P/'check_compact_params.py']}
 dump(out/'SOURCE_MAP.json',src);print('Verifying archived artifacts, receipts and original source fingerprints...',flush=True)
 d=integrity(b);dump(out/'INPUT_INTEGRITY.json',d)
 def run(script,*args):
  print('RUN',script,*map(str,args),flush=True);subprocess.run([sys.executable,str(R/script),*map(str,args)],cwd=R,check=True)
 run('summarize_e4.py','--batch',b,'--output',out/'derived')
 from security_audit import collect
 from security_metrics import write
 from check_compact_params import write as certify
 security={}
 for v in ['B1','V0','V1','G3','C3','D3','DC3']:
  header=b/f'artifacts/{v}/lazer/python/anon_cred/anon_cred_params.h'
  if not header.exists():raise RuntimeError('Missing archived parameter header '+v)
  target=out/'security'/v;up=collect(header,v,3 if v in ['C3','DC3'] else 0);security[v]=write(target,up);dump(target/'security.json',up)
  if v in ['C3','DC3']:
   c=certify(target,header)
   if c['status']!='PASSED_SCOPED_CONDITIONS':raise RuntimeError('Compact certificate failed '+v)
 from paper_tables import make
 table=make(out,[],security['C3'])
 if table['status']!='PASSED' and not a.allow_new_data:raise RuntimeError('Paper display values disagree; see tables/TABLE_CHECK.json. No source paper changed.')
 run('draw_schematics.py','--out',out/'figures')
 run('plot_paper.py','--batch',b,'--output',out,'--lang','both')
 names=src['figure_sources'];expected=[out/'figures'/lang/ext/(name+'.'+ext) for lang in ['zh','en'] for ext in ['png','pdf','svg'] for name in names]
 if any(not p.is_file() or p.stat().st_size<1000 for p in expected):raise RuntimeError('Missing/empty figure output')
 # A source manifest for each raw record file, not only aggregate totals.
 raw_manifest={str(p.relative_to(b)):sha(p) for p in sorted((b/'raw').glob('*')) if p.is_file()};dump(out/'RAW_SOURCE_SHA256.json',raw_manifest)
 src['status']='COMPLETE';src['figures']=len(expected);src['table_check']=table;src['native_reexecuted']=False;dump(out/'SOURCE_MAP.json',src)
 (out/'README_ZH.md').write_text('原始 full 数据的只读重算已经完成。图1–7：figures/{zh,en}/{png,pdf,svg}/；表格：tables/；参数与证书：security/。\n表1/2和附录A/B为原稿转录，不是E4原始数据复算。详情见tables/TABLE_PROVENANCE.csv。\n未重跑原生证明、性能full或完整Sage估计器；不据此认证整协议安全位数。\n')
 dump(out/'OUTPUT_SHA256.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'matplotlib_cache' not in p.parts and p.name!='OUTPUT_SHA256.json'})
 print('PAPER_REPRODUCTION_COMPLETE',out,'42 figure files;',table['displayed_cells_checked'],'displayed cells checked;',len(table['rounding_notes']),'rounding notes; table status',table['status'])
if __name__=='__main__':main()
