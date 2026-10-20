#!/usr/bin/env python3
"""Negative regressions: parameter corruption and mislabeled raw records must be detected."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'project'))
from security_parameters import inputs,Header,sha
from check_compact_params import certificate
from security_audit import collect
from reproduce_paper import integrity
B=R/'results/full'
def run(out):
 header=B/'artifacts/C3/lazer/python/anon_cred/anon_cred_params.h';raw=header.read_text();tests=[]
 def record(name,passed,detail=''):
  tests.append(dict(test=name,passed=bool(passed),detail=detail))
  if not passed:raise AssertionError(name+' '+detail)
 good=certificate(header);record('actual_C3_all_scoped_conditions',good['status']=='PASSED_SCOPED_CONDITIONS',str(len(good['checks'])))
 record('B1_vs_C3_explicit_selection',collect(B/'artifacts/B1/lazer/python/anon_cred/anon_cred_params.h','B1')['P2_relation_shape']==[8,48] and collect(header,'C3')['P2_relation_shape']==[8,45])
 try:inputs(header);raised=False
 except ValueError:raised=True
 record('archived_header_without_variant_rejected',raised)
 with tempfile.TemporaryDirectory() as td:
  td=Path(td)
  edits=[('wrong_variance','169060907886838UL','169060907886839UL'),('wrong_q','{1125899906843221UL}','{1125899906843222UL}'),('missing_exact_index','p2_compact3_param_Ps[13] = {16,','p2_compact3_param_Ps[13] = {99,'),('wrong_nex',', 8, 2, 47, 2, 18,',', 8, 2, 48, 2, 18,'),('wrong_nested_randomness','_p2_compact3_param_quad_many_ = {{ _p2_param_ring, _p2_param_dcomp, 47, 64,','_p2_compact3_param_quad_many_ = {{ _p2_param_ring, _p2_param_dcomp, 47, 63,')]
  for name,before,after in edits:
   if before not in raw:raise AssertionError('Mutation did not match: '+name)
   target=td/(name+'.h');target.write_text(raw.replace(before,after,1))
   try:d=certificate(target);detected=d['status']=='FAILED';detail=','.join(sorted({x['check'] for x in d['checks'] if not x['passed']}))
   except ValueError as e:detected=True;detail=str(e)
   record('detect_'+name,detected,detail)
  target=td/'misleading_comments.h';target.write_text(raw.replace('// modulus q = 1125899906843221','// modulus q = 9').replace('// stdev1 = 13002342.4','// stdev1 = 1'))
  p=Header(target).proof('p2_compact3_param');record('comment_constants_not_parameter_authority',p['q']==1125899906843221 and abs(p['msis_bound_log2']-40.133840634948335)<1e-12)
  # Re-sign an intentionally mislabeled record: receipt hash alone must not make it trusted.
  job=json.loads((B/'plan.json').read_text())[0];work=td/'bad_batch';(work/'raw').mkdir(parents=True);(work/'plan.json').write_text(json.dumps([job]))
  rr=[json.loads(s) for s in (B/'raw'/(job['id']+'.jsonl')).read_text().splitlines()];rr[0]['variant']='B1' if job['variant']!='B1' else 'C3'
  f=work/'raw'/(job['id']+'.jsonl');f.write_text('\n'.join(json.dumps(x) for x in rr)+'\n');f.with_suffix('.receipt.json').write_text(json.dumps(dict(sha256=sha(f),rows=len(rr))))
  proc=subprocess.run([sys.executable,str(R/'summarize_e4.py'),'--batch',str(work),'--output',str(td/'bad_output')],capture_output=True,text=True)
  record('resigned_mislabeled_raw_record_rejected',proc.returncode!=0 and 'Job metadata mismatch' in proc.stderr)
 data=integrity(B);record('original_archives_and_fingerprints',data['status']=='PASSED',f"{data['archived_artifact_files']} artifact files, {data['original_script_fingerprints']} source hashes")
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(status='PASSED',tests=tests,scope='new audit and postprocessing regressions; no native proof/performance rerun'),ensure_ascii=False,indent=2)+'\n');print('FIX123_REGRESSIONS_PASSED',len(tests))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=R/'FIX123_REGRESSION.json');a=ap.parse_args();run(a.output)
