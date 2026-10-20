"""Recompute current E4 paper tables, compare displayed cells, mark historical transcriptions."""
import csv,json,statistics as st
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from summarize_e4 import dumpcsv
R=Path(__file__).resolve().parent
IDS=['1','2','3','4','5','6','A1','A2','A3','A4','B1','B2','B3','C1','C2','C3','C4','C5']
def read(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def make(out,rows,security):
 out=Path(out);D=out/'derived';T=out/'tables';T.mkdir(exist_ok=True)
 original=json.loads((R/'paper_reference/tables_transcribed.json').read_text());summary=json.loads((D/'summary.json').read_text())['main']
 tables={};tests=[];provenance=[]
 def cell(table,row,col,actual,raw_numeric=None):
  expected=original[IDS.index(table)][row][col]
  norm=lambda t: str(t).replace(',','').replace(' ','').replace('\n','')
  exact=norm(expected)==norm(actual);rounding_note=''
  if not exact and raw_numeric is not None:
   try:
    number=Decimal(str(raw_numeric));shown=Decimal(norm(actual));old=Decimal(norm(expected));unit=Decimal(10)**shown.as_tuple().exponent
    if abs(shown-old)==unit and abs(number-old)==unit/2 and abs(number-shown)==unit/2:
     rounding_note='Exact decimal half tie; manuscript binary-float formatting versus canonical decimal ROUND_HALF_UP. Original paper unchanged.'
   except Exception:pass
  tests.append(dict(table=table,row=row,column=col,expected=expected,recomputed=str(actual),passed=exact or bool(rounding_note),rounding_note=rounding_note))
 def emit(table,data,desc):
  tables[table]=data;dumpcsv(T/f'table_{table}.csv',data);provenance.append(dict(table=table,status='RECOMPUTED_FROM_E4_RAW_OR_ACTUAL_HEADER',source=desc))
 def m(v,life,mode='strict'):return next(x for x in summary if x['variant']==v and x['lifecycle']==life and x['verification_mode']==mode)
 def f(x,n=2):return format(Decimal(str(x)).quantize(Decimal(10)**-n,rounding=ROUND_HALF_UP),f'.{n}f')
 def main_table(table,mode):
  data=[];r=0
  for life in ['steady','fresh']:
   for v in ['B1','G3','C3']:
    r+=1;x=m(v,life,mode);data.append(x)
    if table=='3':
     values=[life+v,f(x['prove_mean_ms']),f(x['verify_mean_ms']),f(x['show_mean_ms']),f(x['show_median_ms'])+f(x['show_p95_ms']),f(x['K_mean']),f(x['ols_at_5_5']),f(x['proof_mean_bytes'])]
    else:values=[life,v,f(x['prove_mean_ms']),f(x['verify_mean_ms']),f(x['show_mean_ms']),f(x['ols_at_5_5'])]
    for c,value in enumerate(values,1):cell(table,r,c,value,raw_numeric=x['proof_mean_bytes'] if table=='3' and c==8 else None)
  emit(table,data,'raw main; nonwarmup; '+mode)
 main_table('3','strict');main_table('C1','raw')
 reuse=read(D/'reuse.csv');data=[]
 for r,v in enumerate(['B1','V0','V1','G3','C3'],1):
  one=[x for x in reuse if x['variant']==v and int(x['N'])==1];last=[x for x in reuse if x['variant']==v and int(x['N'])==256]
  init=st.mean(float(x['user_verifier_init_ms']) for x in one);first=st.mean(float(x['prove_verify_ms']) for x in one);n1=st.mean(float(x['amortized_local_service_ms']) for x in one);ns=[float(x['amortized_local_service_ms']) for x in last]
  row=dict(variant=v,independent_lifecycles=len(one),init_mean_ms=init,first_show_mean_ms=first,N1_mean_ms=n1,N256_mean_ms=st.mean(ns),N256_min_ms=min(ns),N256_max_ms=max(ns));data.append(row)
  for c,value in enumerate([v,f(init),f(first),f(n1),f(st.mean(ns)),f(min(ns))+'～'+f(max(ns))],1):cell('4',r,c,value)
 emit('4',data,'raw reuse; initialization + prefix sums; 3 lifecycle min/max, not CI')
 data=[]
 for r,(life,v) in enumerate(((life,v) for life in ['steady','fresh'] for v in ['B1','G3','C3']),1):
  x=m(v,life);data.append(x)
  values=[life+v,f(x['ols_a'],3)+' / '+f(x['ols_b'],3),f(x['ols_r2'],5),f(x['prove_cpu_mean_ms']),f(x['verify_cpu_mean_ms']),f(x['rss_max_MiB'])]
  for c,value in enumerate(values,1):cell('C2',r,c,value)
 emit('C2',data,'raw strict main; OLS descriptive regression and process high-water RSS')
 policy=read(D/'policy.csv');data=[];r=0
 for v in ['V1','G3','C3']:
  for pattern in ['fixed','alternating','random']:
   r+=1;x=next(x for x in policy if x['variant']==v and x['pattern']==pattern);data.append(x)
   values=[v,pattern,f(x['show_mean_ms']),f(x['K_mean']),x['cache_hits'],x['cache_populates']]
   for c,value in enumerate(values,1):cell('C3',r,c,value)
 emit('C3',data,'raw policy strict; all100 per cell including cold policy changes')
 ks=read(D/'k_sweep.csv');data=[]
 for k in range(9):
  a=next(x for x in ks if x['variant']=='G3' and int(x['k'])==k);b=next(x for x in ks if x['variant']=='C3' and int(x['k'])==k)
  diff=float(a['proof_mean_bytes'])-float(b['proof_mean_bytes']);data.append(dict(k=k,G3_mean_B=a['proof_mean_bytes'],C3_mean_B=b['proof_mean_bytes'],reduction_B=diff,G3_show_ms=a['show_mean_ms'],C3_show_ms=b['show_mean_ms']))
  for c,value in enumerate([k,f(a['proof_mean_bytes']),f(b['proof_mean_bytes']),f(diff),f(a['show_mean_ms']),f(b['show_mean_ms'])],1):cell('C4',k+1,c,value)
 emit('C4',data,'raw same-k sweep30 per variant,k; unpaired timings')
 model=security['model_details'];p1,p2=model['proofs'];data=[]
 models=p2['MSIS']['all_k_0_to_8_models']
 from project.security_parameters import Header,compact_rows
 compact=compact_rows(Header(security['parameter_source']['header_path']))
 for row in compact:
  k=row['disclosed_attributes_k'];x=models[f'k_{k}_m1_{48-k}'];beta=x['bkz_blocksize'];data.append(dict(**row,beta=beta,classical_log2=.292*beta,quantum_log2=.265*beta))
  for c,value in enumerate([k,f(row['msis_bound_log2'],6),f(row['MSIS_rhf_recomputed'],7),beta,f(.292*beta,3)+' / '+f(.265*beta,3)],1):cell('C5',k+1,c,value)
 emit('C5',data,'archived C3 actual C arrays + fixed SIS generic subdimension/GSA model; analytic RHF shown separately')
 data=[]
 for label,x,kind in [('P1 MSIS',p1['MSIS'],'sis'),('P1 MLWE',p1['MLWE'],'lwe'),('P2 MSIS 填充',p2['MSIS']['full_m1_48_reference'],'sis'),('P2 MSIS 紧致',p2['MSIS'],'sis'),('P2 MLWE',p2['MLWE'],'lwe'),('Falcon 原像代理',model['Falcon_NTRU_512_preimage_generic_model'],'sis')]:
  beta=x['fresh_primal_usvp_gsa']['bkz_blocksize'] if kind=='lwe' else x['bkz_blocksize'];rhf=x['header_root_hermite_factor'] if kind=='lwe' else x['root_hermite_factor']
  data.append(dict(component=label,rhf_display=rhf,rhf_source='attributed upstream multi-attack declaration; NOT rerun' if kind=='lwe' else 'fresh generic SIS subdimension model',beta=beta,classical_log2=.292*beta,quantum_log2=.265*beta,beta_source='fresh primal uSVP GSA' if kind=='lwe' else 'generic SIS GSA'))
  for c,value in [(1,label),(2,f(rhf,7)),(3,beta),(4,f(.292*beta,3)+' / '+f(.265*beta,3))]:cell('5',len(data),c,value)
 emit('5',data,'actual archived parameters; separate attributed MLWE RHF versus fresh beta model')
 # Table6 has prose; export machine-checkable recorded evidence, do not treat prose as new native execution.
 batch=Path(json.loads((out/'SOURCE_MAP.json').read_text())['batch'])
 v=batch/'verification';passed=json.loads((v/'PASSED.json').read_text());cache=json.loads((v/'cache_residency.json').read_text());poly=json.loads((v/'poly_scale.json').read_text());shadow=json.loads((D/'summary.json').read_text())['float_shadow'];subset=read(D/'subsets.csv')
 data=[dict(item='cross strict',recorded=json.dumps(passed,ensure_ascii=False),source='verification/PASSED.json'),dict(item='cache lifecycle',recorded=json.dumps(cache,ensure_ascii=False),source='verification/cache_residency.json'),dict(item='integer multiplication',recorded=json.dumps(poly),source='verification/poly_scale.json'),dict(item='float shadow',recorded=json.dumps(shadow),source='raw diagnostic'),dict(item='all subsets',recorded=json.dumps(dict(records=len(subset),all_checks_pass=all(x['passed']=='True' for x in subset))),source='raw subsets')]
 emit('6',data,'recorded finite native regressions only; receipts checked, native runs not repeated')
 # Retain all manuscript table transcriptions; make the missing historical E3 evidence explicit.
 for table,orig in zip(IDS,original):
  with (T/f'table_{table}_paper_transcription.csv').open('w',newline='') as f0:csv.writer(f0).writerows(orig)
  if table not in tables:provenance.append(dict(table=table,status='PAPER_TRANSCRIPTION_ONLY_NOT_RAW_RECOMPUTED',source='current unchanged Word; E3 raw archive / external work absent from this supplement' if table!='2' else 'current unchanged Word variant definitions'))
 dumpcsv(T/'paper_cell_checks.csv',tests);dumpcsv(T/'TABLE_PROVENANCE.csv',sorted(provenance,key=lambda x:IDS.index(x['table'])))
 report=dict(status='PASSED' if all(x['passed'] for x in tests) else 'MISMATCH',displayed_cells_checked=len(tests),rounding_notes=[x for x in tests if x['rounding_note']],mismatches=[x for x in tests if not x['passed']],raw_recomputed_tables=list(tables),transcription_only_tables=[x['table'] for x in provenance if x['status'].startswith('PAPER_TRANSCRIPTION')],scope='numeric display comparison; table6 prose not counted as numeric cell verification; no independent E3 reproduction')
 (T/'TABLE_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 text=['# 当前论文图表与表格重建核对','',f"核对 {len(tests)} 个数字/标签单元格；实质数值不一致 {len(report['mismatches'])} 个；末位舍入注记 {len(report['rounding_notes'])} 个。",'','原始 E3 数据未随本包提供。表1的外部/E3数值、表2和附录A/B保留原稿转录与明确来源标记，不宣称由E4重算。','', '表3–5、C1–C5由本包原始记录或归档参数重算；表6导出原生回归记录证据，未把本次静态重读称为重新执行原生密码证明。','', 'MLWE RHF是原生成器多攻击估计的归属数值；beta与成本来自本次单攻击primal GSA。表5分别标明来源；二者不是同一估计器重新运行的输出。','']
 text += ['展示值统一采用十进制ROUND_HALF_UP。原稿在精确半分位使用二进制浮点格式化时末位可能相差1；单列注记，不改原稿、不改变原始数值。']
 text += [json.dumps(x,ensure_ascii=False) for x in report['mismatches']+report['rounding_notes']]
 (T/'TABLE_CHECK_ZH.md').write_text('\n'.join(text)+'\n');return report
