#!/usr/bin/env python3
"""Executable, scoped certificate of structural and generator-inequality checks. No parameter writes."""
import argparse,csv,json,math,re
from decimal import Decimal as D,localcontext,ROUND_HALF_EVEN
from pathlib import Path
from security_parameters import Header,DEFAULT_HEADER,ROOT,integer,sha

def prime64(n):
 if n<2 or n>=2**64:return False
 for p in [2,3,5,7,11,13,17,19,23,29,31,37]:
  if n%p==0:return n==p
 t=n-1;s=0
 while t%2==0:s+=1;t//=2
 for a in [2,325,9375,28178,450775,9780504,1795265022]:
  if a%n==0:continue
  x=pow(a,t,n)
  if x in [1,n-1]:continue
  for _ in range(s-1):
   x=x*x%n
   if x==n-1:break
  else:return False
 return True

def certificate(header=DEFAULT_HEADER):
 h=Header(header);gen=ROOT/'lazer/scripts/lnp-tbox-codegen.sage';g=gen.read_text()
 constants={key:float(re.search(r'^'+key+r'\s*=\s*([\d.]+)',g,re.M)[1]) for key in ['KAPPA','DELTA128','L','T']}
 K=int(constants['KAPPA']);L=int(constants['L']);checks=[];params=[]
 def check(p,name,passed,actual,requirement,source):
  checks.append(dict(parameter=p['symbol'],check=name,passed=bool(passed),actual=str(actual),requirement=requirement,source=source))
 base=h.proof('p2_param')
 for sym in ['p1_param','p2_param']+[f'p2_compact{k}_param' for k in range(1,9)]:
  p=h.proof(sym);k=0 if sym in ['p1_param','p2_param'] else int(re.search(r'compact(\d+)',sym)[1]);is_p2=sym!='p1_param';a=p['structures']['abdlop'];lin=p['structures']['lin'];tbox=p['structures']['tbox'];q=p['q'];d=p['d'];z=p['Z'];m=p['m1'];nb=p['nbin']
  check(p,'prime_modulus_and_two_factors',prime64(q) and d==64 and L==2 and q%8==5,(q,d,L,q%8),'q prime <2^64, d=64,L=2,q=5 mod8','generator lines 105-154; deterministic 64-bit Miller-Rabin')
  check(p,'linear_ring_interface',p['relation_degree']==d and p['relation_rank']==1 and p['p']==h.value(lin['p']) and (p['p']*h.value(lin['pinv']))%q==1,(p['relation_degree'],p['relation_rank'],p['p']),'same degree, ring extension rank1, relation modulus inverse modulo proof q','lin_params_t')
  check(p,'norm_groups',z==len(p['norm_dimensions'])==len(p['norm_bounds_sq'])==len(p['Es'])==len(p['Es_nrows']) and p['norm_dimensions']==[len(x) for x in p['Es']]==p['Es_nrows'],p['norm_dimensions'],'Z and group dimensions agree with actual Es and squared bounds','lin-codegen.sage partition; lnp-tbox-codegen.sage Z,nex')
  flat=sum(p['Es'],[])+p['Ps']
  check(p,'complete_disjoint_partition',sorted(flat)==list(range(m)) and len(flat)==len(set(flat)),flat,'exact Euclidean groups + binary coordinates partition 0..m1-1','lin-codegen.sage partition assertions')
  check(p,'binary_count',nb==len(p['Ps'])==integer(lin['Ps_nrows']),p['Ps'],'nbin = Ps length = lin.Ps_nrows','lin_params_t and lnp_tbox_params_t')
  check(p,'witness_indices',p['s1_indices']==list(range(m)) and integer(lin['nm_indices'])==p['l']==0,p['s1_indices'],'all witness coordinates short, no large-message coordinates','this retained Ajtai layout')
  check(p,'internal_dimensions',p['internal_m1']==m+z and p['nex']==sum(p['norm_dimensions'])+nb+z,(p['internal_m1'],p['nex']),'internal m1=m1+Z; nex=sum(n)+nbin+Z','lnp-tbox-codegen.sage lines126-129,532-536')
  check(p,'base_challenge',p['omega']==8 and p['eta']==140 and p['nu']==1 and integer(a['log2omega'])==5,(p['omega'],p['eta'],p['nu']),'d64,L2 challenge table and ternary randomness unchanged','lnp-tbox-codegen.sage lines145-157,189')
  check(p,'lambda',p['lambda_repetitions']==2*math.ceil(K/(2*math.log2(q))),p['lambda_repetitions'],'lambda=2 ceil(KAPPA/(2 log2 q))','generator line140')
  check(p,'completeness_short',(m+z)*d>=5*K,(m+z)*d,'(m1+Z)*d >=5*KAPPA','generator lines329-332; cited theorem6.4.1')
  check(p,'completeness_randomness',p['m2']*d>=5*K,p['m2']*d,'m2*d >=5*KAPPA','generator lines329-332')
  check(p,'simulation_dimension',p['kmlwe']>=0 and p['mlwe_embedding_rank']==p['kmsis']+p['l']+p['lambda_repetitions']//2+256//d+p['approx_proof']*256//d+2,(p['kmlwe'],p['mlwe_embedding_rank']),'nonnegative kmlwe and extension dimension identity','generator lines335-340')
  check(p,'rejection_modes',p['rejection_modes'][0]==1 and p['rejection_modes'][1] in [1,2] and p['rejection_modes'][2:]==[2,2],p['rejection_modes'],'standard/bimodal modes permitted by generator','generator lines98-101')
  with localcontext() as ctx:
   ctx.prec=90
   # Sage preparses the decimal literal 1.55; reproduce it at high precision.
   sig=[D("1.55")*D(2)**e for e in p['log2stdev']]
   check(p,'rounded_variances',[int((s*s).to_integral_value(rounding=ROUND_HALF_EVEN)) for s in sig]==p['stdev_sq'],p['stdev_sq'],'stored integer variances = nint((mpf(1.55)*2^e)^2)','generator lines446-449,490-493')
   bst=sig[1]*(D(2*p['m2']*d).sqrt())+D(p['eta'])*D(2)**(p['D']-1)*D(p['kmsis']*d).sqrt()+D(p['gamma'])*D(p['kmsis']*d).sqrt()/2
   tconst=D(str(constants['T']))
   bz3=int((tconst*sig[2])**2*256);bz4=int(D(2*K).sqrt()*sig[3])
   check(p,'response_bounds',p['response_bounds']==dict(Bz3sqr=bz3,Bz4=bz4),p['response_bounds'],'Bz3sqr=floor((T*sigma3*sqrt256)^2); Bz4=floor(sqrt(2*KAPPA)*sigma4)','generator lines470-471')
   check(p,'compression_integer_bound',int(bst*bst)==p['Bstar_sq'],str(bst*bst),'stored Bstar_sq=floor(Bound_star^2)','generator Bound_(), line485')
   B=D(4*p['eta'])*(D(8*(m+z)*d)*sig[0]**2+D(4)*bst**2).sqrt()
   delta=2**(float(B.ln()/D(2).ln())**2/(4*d*p['kmsis']*math.log2(q)))
   check(p,'extraction_bound_vs_modulus',B<q,str(B),'Bound < q (also stronger than Bound <2^logq)','generator lines232,297; Bound functions')
   check(p,'declared_msis_threshold',delta<constants['DELTA128'],delta,'analytic RHF < generator DELTA128; heuristic target, not certified bits','generator line297')
   check(p,'compression_challenge',2**(p['D']-1)*p['omega']*d<p['gamma'],2**(p['D']-1)*p['omega']*d,'2^(D-1)*omega*d < gamma','generator line297')
   dc=p['structures']['dcompress'];gam=p['gamma']
   check(p,'decomposition_constants',h.value(dc['q'])==q and h.value(dc['qminus1'])==q-1 and h.value(dc['pow2D'])==2**p['D'] and h.value(dc['pow2Dby2'])==2**(p['D']-1) and h.value(dc['m'])*gam==q-1 and h.value(dc['gammaby2'])*2==gam,(q,gam,p['D']),'q, q-1, powers of two and gamma factorization consistent','dcompress_params_t')
   arp=2*(D(256)/26).sqrt()*(1+(D(2).ln()*K)/128).sqrt()*sig[2]
   for name,rhs,op,src in [('range_linear',D(41*p['nex']*d)*arp,'>=','346'),('binary_nbin',arp**2+arp*D(nb*d).sqrt(),'>','348'),('binary_slack',arp**2+arp*D(d).sqrt(),'>','350')]+[(f'exact_norm_{i}',D(3*b)+arp**2,'>','354') for i,b in enumerate(p['norm_bounds_sq'])]:
    check(p,name,D(q)>=rhs if op=='>=' else D(q)>rhs,str(D(q)-rhs),f'q {op} RHS; actual records q-RHS','generator line'+src)
   epsilon=D(2)**-130+D(q)**(-d//L)+D(q)**(-p['lambda_repetitions'])+D(2)**-K+D(2)**(-2*K)
   check(p,'interactive_knowledge_error',epsilon<=D(2)**-127,str(epsilon),'epsilon <=2^-127 for d64 challenge cardinality2^129','generator lines145-154,357-360; interactive expression only')
  # Verify every nested backend sees the same inherited numerical parameters.
  for kind,lext,lval in [('quad_eval',p['lambda_repetitions']//2+1,p['l']+512//d+1),('quad_many',1,p['l']+512//d+1+p['lambda_repetitions']//2)]:
   b=p['structures'][kind];want=dict(a);want.update(l=str(lval),lext=str(lext))
   check(p,'nested_'+kind,b==want,b,'all fields inherited except specified extension lengths','generator lines533-535')
  check(p,'tbox_extension',integer(a['lext'])==512//d+2+p['lambda_repetitions']//2,a['lext'],'lext=512/d+2+lambda/2','generator line532')
  if is_p2:
   check(p,'compact_layout',m==48-k and nb==16-k and p['Ps']==list(range(16,24))+list(range(40,48-k)) and p['Es']==[list(range(16)),list(range(24,40))],(m,nb,p['Ps']),'m1=48-k,nbin=16-k; exact groups unchanged; only last attribute coordinates removed','switch_variant.py compact construction; explicit release relation')
   unchanged=['d','q','p','m2','kmsis','D','gamma','Bstar_sq','log2stdev','stdev_sq','rejection_modes','rejection_factors','norm_bounds_sq','norm_dimensions','nprime','lambda_repetitions']
   check(p,'retained_base_parameters',all(p[x]==base[x] for x in unchanged),{x:p[x] for x in unchanged},'sampling, norm bounds, compression and randomness retained from k0','conservative reuse check, not fresh parameter optimization')
   alpha_sq=sum(p['norm_bounds_sq'])+nb*d
   check(p,'sampling_dominance',alpha_sq<=sum(base['norm_bounds_sq'])+base['nbin']*d and p['nex']<=base['nex'] and p['nprime']==base['nprime'],alpha_sq,'binary deletion cannot increase alpha, alpha3 or ARP dimensions; retained Bprime dominates smaller column count','lin-codegen.sage alpha/Bprime formulas and projection layout')
   check(p,'proof_capacity_layout',p['max_proof_bytes_header']==base['max_proof_bytes_header']-192*k,p['max_proof_bytes_header'],'declared buffer estimate follows release -192*k convention; not proof of worst-case length','implementation invariant only; runtime length regressions separate')
  params.append({k:v for k,v in p.items() if k!='structures'})
 return dict(schema=1,status='PASSED_SCOPED_CONDITIONS' if all(c['passed'] for c in checks) else 'FAILED',header_path=str(h.path),header_sha256=sha(h.path),generator_constants=constants,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [gen,ROOT/'lazer/scripts/codegen.sage',ROOT/'lazer/scripts/lin-codegen.sage',ROOT/'lazer/lazer.h',Path(__file__),ROOT/'security_parameters.py']},checks=checks,parameters=params,scope='Executable arithmetic and layout checks for P1 and k0..8 retained P2. Not a new reduction, whole-protocol security certification, full Sage regeneration, or compiled-object/header identity proof.',not_checked=['full ROM/QROM security and auxiliary-preimage assumptions','constant-time behavior, sampler distribution proof and rejection-probability derivation','CRT auxiliary modulus generation/min_P and all serialized-proof worst-case lengths','native code execution and compiled-object identity (use archived hash evidence and native regressions separately)'])

def write(out,header=DEFAULT_HEADER):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);d=certificate(header)
 (out/'compact_conditions.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 with (out/'compact_conditions.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(d['checks'][0]));w.writeheader();w.writerows(d['checks'])
 txt=['# 紧致参数条件核查证书','',d['status'],f"\n头文件 SHA256：{d['header_sha256']}",f"\n逐项检查：{len(d['checks'])}；失败：{sum(not x['passed'] for x in d['checks'])}。",'','覆盖 P1、P2 k=0…8 的实际整数数组、结构初始化及所列生成器条件。不是整协议安全认证；不声称已重新运行完整 Sage 生成器。','', '|参数|条件|通过|实测值或余量|要求|来源|','|---|---|---|---|---|---|']
 txt += ['|'+'|'.join(str(x[k]).replace('|','/') for k in ['parameter','check','passed','actual','requirement','source'])+'|' for x in d['checks']]
 txt+=['','未覆盖：']+['- '+x for x in d['not_checked']]
 (out/'COMPACT_CONDITIONS_ZH.md').write_text('\n'.join(txt)+'\n');return d
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--header',type=Path,default=DEFAULT_HEADER);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args();d=write(a.output,a.header);print(d['status'],len(d['checks']));raise SystemExit(0 if d['status']=='PASSED_SCOPED_CONDITIONS' else 1)
