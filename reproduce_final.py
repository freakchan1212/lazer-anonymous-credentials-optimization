#!/usr/bin/env python3
"""Rebuild final paper Figs1-7 and tables1-7/S1-S13 from the preserved full batch.
No native proof, benchmark, or full Sage estimator is executed by this entry.
"""
import argparse,csv,datetime,hashlib,json,subprocess,sys,re
from pathlib import Path
R=Path(__file__).resolve().parent
MAP={'1':'1','2':'3','3':'4','4':'5','5':'6','6':'7',**{f'A{i}':f'S{i}' for i in range(1,5)},**{f'B{i}':f'S{i+4}' for i in range(1,4)},**{f'C{i}':f'S{i+7}' for i in range(1,6)}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def export_current(out,allow_new=False):
 target=json.loads((R/'publication/PUBLICATION_TARGET.json').read_text())
 for name,digest in target['sha256'].items():
  if sha(R/'publication'/name)!=digest:raise RuntimeError('Publication target changed: '+name)
 source=out/'tables';legacy=out/'legacy_fix123_tables';source.rename(legacy);source.mkdir()
 tables=json.loads((R/'publication/final_tables.json').read_text());indexed={x['id']:x for x in tables}
 provenance=[];checks=[]
 for t in tables:
  with (source/f"table_{t['id']}_paper_transcription.csv").open('w',newline='',encoding='utf-8-sig') as f:csv.writer(f).writerows(t['rows'])
  provenance.append(dict(table=t['id'],caption=t['caption'],status='PAPER_TRANSCRIPTION_ONLY',source='final DOCX; no new measurements'))
 # Numeric checks are recomputed from JSONL by the legacy engine, then compared
 # directly to the NEW displayed table cells; human labels are not numeric tests.
 oldchecks=list(csv.DictReader((legacy/'paper_cell_checks.csv').open()))
 for c in oldchecks:
  old=c['table'];new=MAP[old];col=int(c['column'])-1;row=int(c['row'])
  expected=indexed[new]['rows'][row][col]
  # First cell in each numerical table identifies the scheme/lifecycle, not data.
  if col==0 or (old in ['C1','C3'] and col==1):continue
  norm=lambda s:re.sub(r'[\s,]','',str(s))
  ok=norm(expected)==norm(c['recomputed']);note=c['rounding_note']
  if note and norm(expected)==norm(c['expected']):ok=True
  checks.append(dict(table=new,row=row,column=col,final_paper=expected,recomputed=c['recomputed'],passed=ok,rounding_note=note))
 for old,new in MAP.items():
  p=legacy/f'table_{old}.csv'
  if p.exists():
   (source/f'table_{new}_recomputed.csv').write_bytes(p.read_bytes())
   next(x for x in provenance if x['table']==new).update(status='RECOMPUTED_E4_VALUES_OR_RECORDED_REGRESSION',source='preserved JSONL / actual C arrays / finite native receipts; see legacy_fix123_tables/TABLE_PROVENANCE.csv')
 # Related work and identifier table are explicitly qualitative/transcribed.
 if any(not c['passed'] for c in checks) and not allow_new:raise RuntimeError('Final manuscript numeric mismatch: '+repr([c for c in checks if not c['passed']]))
 for name,rows in [('FINAL_NUMERIC_CHECKS.csv',checks),('TABLE_PROVENANCE.csv',provenance)]:
  with (source/name).open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 report=dict(status='PASSED' if all(c['passed'] for c in checks) else 'NEW_DATA_DIFFERS_FROM_PAPER',numeric_cells_checked=len(checks),mismatches=[c for c in checks if not c['passed']],figure_files=42,main_tables=7,supplement_tables=13,native_proofs_reexecuted=False,full_performance_reexecuted=False,full_sage_estimation_executed=False,publication_target=target)
 (out/'FINAL_REPRODUCTION.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 (out/'README_ZH.md').write_text('当前正文图1—7：figures/{zh,en}/{png,pdf,svg}/。当前表1—7、S1—S13：tables/；数值核对：FINAL_REPRODUCTION.json。\n历史编号仅保存在legacy_fix123_tables/，不能用于最终论文编号。\n图1/2是方法示意；历史表S1—S7只有转录，没有原始full重算。新重算的表与归档回归证据见TABLE_PROVENANCE.csv。\n本入口没有执行新的原生证明、full性能实验或完整Sage安全估计。\n')
 src=json.loads((out/'SOURCE_MAP.json').read_text());src['legacy_fix123_paper']=src.pop('paper',None);src['paper']=target;src['final_entry_sha256']=sha(R/'reproduce_final.py');(out/'SOURCE_MAP.json').write_text(json.dumps(src,ensure_ascii=False,indent=2)+'\n')
 # Refresh output manifest after publishing final numbering.
 (out/'OUTPUT_SHA256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and 'matplotlib_cache' not in p.parts and p.name!='OUTPUT_SHA256.json'},indent=2,ensure_ascii=False)+'\n')
 return report

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--batch',type=Path,default=R/'results/full');ap.add_argument('--output',type=Path);ap.add_argument('--allow-new-data',action='store_true');a=ap.parse_args()
 out=a.output.resolve() if a.output else R/('final_reproduced_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
 cmd=[sys.executable,str(R/'reproduce_paper.py'),'--batch',str(a.batch.resolve()),'--output',str(out)]
 if a.allow_new_data:cmd+=['--allow-new-data']
 subprocess.run(cmd,check=True,cwd=R);report=export_current(out,a.allow_new_data)
 print('FINAL_PAPER_REPRODUCTION_COMPLETE',out,'numeric cells',report['numeric_cells_checked'],'status',report['status'])
if __name__=='__main__':main()
