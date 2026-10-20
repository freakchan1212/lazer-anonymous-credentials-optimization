#!/usr/bin/env python3
"""Strict reader for this release's generated C initializers (no C eval or comments as inputs)."""
import ast, hashlib, json, math, re
from decimal import Decimal, localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEFAULT_HEADER=ROOT/'lazer/python/anon_cred/anon_cred_params.h'
COMPACT={'V5','C3','DC3'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def integer(s):
 s=re.sub(r'(?<=\d)[uUlL]+\b','',s.strip())
 def walk(n):
  if isinstance(n,ast.Constant) and type(n.value)==int:return n.value
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):return (-1 if isinstance(n.op,ast.USub) else 1)*walk(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=walk(n.left),walk(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,(ast.Div,ast.FloorDiv)) and a>=0 and b>0:return a//b
   if isinstance(n.op,ast.LShift) and 0<=b<=256:return a<<b
  raise ValueError('Unsupported integer expression: '+s)
 return walk(ast.parse(s,mode='eval').body)
def strip_comments(t):return re.sub(r'/\*.*?\*/|//[^\n]*','',t,flags=re.S)
class Header:
 def __init__(self,path):
  self.path=Path(path).resolve();self.raw=self.path.read_text();self.text=strip_comments(self.raw)
  self.schema=strip_comments((ROOT/'lazer/lazer.h').read_text())
 def array(self,symbol):
  matches=list(re.finditer(r'\b'+re.escape(symbol)+r'\s*\[([^]]*)\]\s*=\s*\{([^{}]*)\}\s*;',self.text))
  if len(matches)!=1:raise ValueError(f'Expected one array {symbol}, found {len(matches)}')
  m=matches[0];xs=[x.strip() for x in m[2].split(',') if x.strip()]
  if m[1].strip() and integer(m[1])!=len(xs):raise ValueError('Array length mismatch: '+symbol)
  return xs
 def ints(self,symbol):return [integer(x) for x in self.array(symbol)]
 def value(self,symbol):
  ms=list(re.finditer(r'\b'+re.escape(symbol)+r'\s*=\s*\{\{\s*\(limb_t\s*\*\)\s*(\w+)\s*,\s*(\d+)\s*,\s*([01])\s*\}\}\s*;',self.text))
  if len(ms)!=1:raise ValueError('Missing/duplicate int_t: '+symbol)
  m=ms[0];xs=self.ints(m[1]);n=int(m[2])
  if n!=len(xs) or any(x<0 or x>=2**64 for x in xs):raise ValueError('Invalid 64-bit limbs: '+symbol)
  return (-1 if m[3]=='1' else 1)*sum(x<<(64*i) for i,x in enumerate(xs))
 def struct(self,kind,symbol):
  ms=list(re.finditer(r'\b'+re.escape(kind)+r'\s+'+re.escape(symbol)+r'\s*=\s*\{\{([^{}]*)\}\}\s*;',self.text))
  if len(ms)!=1:raise ValueError('Missing/duplicate struct: '+symbol)
  name=kind[:-2]+'_struct'
  bodies=[body for body,n in re.findall(r'typedef\s+struct\s*\{([^{}]*)\}\s*(\w+)\s*;',self.schema) if n==name]
  if len(bodies)!=1:raise ValueError('Unknown schema '+kind)
  fields=[re.search(r'(\w+)\s*$',x.strip())[1] for x in bodies[0].split(';') if x.strip()]
  values=[x.strip() for x in ms[0][1].split(',')]
  if len(fields)!=len(values):raise ValueError('Initializer/schema length mismatch: '+symbol)
  return dict(zip(fields,values))
 def proof(self,symbol):
  lin=self.struct('lin_params_t',symbol);t=self.struct('lnp_tbox_params_t',lin['tbox_params']);a=self.struct('abdlop_params_t',t['tbox']);ring=self.struct('polyring_t',a['ring']);dc=self.struct('dcompress_params_t',a['dcompress']);quad=self.struct('lnp_quad_eval_params_t',t['quad_eval'])
  # Also read every nested initializer: corrupted field counts must fail closed.
  qe=self.struct('abdlop_params_t',quad['quad_eval']);qm=self.struct('abdlop_params_t',quad['quad_many'])
  z=integer(t['Z']);ns=self.ints(t['n']);l2sym=re.fullmatch(r'&(\w+)\[0\]',t['l2Bsqr'])
  if not l2sym:raise ValueError('Unsupported l2 bound pointer')
  l2=[self.value(x) for x in self.array(l2sym[1])]
  es=[self.ints(x) for x in self.array(lin['Es'])];esn=self.ints(lin['Es_nrows'])
  p=dict(symbol=symbol,d=integer(ring['d']),q=self.value(ring['q']),p=self.value(lin['p']),relation_degree=integer(lin['dprime']),relation_rank=integer(lin['k']),m1=integer(lin['ns1_indices']),m2=integer(a['m2']),l=integer(a['l']),kmsis=integer(a['kmsis']),Z=z,nbin=integer(t['nbin']),nex=integer(t['nex']),nprime=integer(t['nprime']),nu=integer(a['nu']),omega=integer(a['omega']),eta=integer(a['eta']),D=integer(dc['D']),gamma=self.value(dc['gamma']),Bstar_sq=self.value(a['Bsqr']),lambda_repetitions=integer(quad['lambda']),norm_dimensions=ns,norm_bounds_sq=l2,Es=es,Es_nrows=esn,Ps=self.ints(lin['Ps']),s1_indices=self.ints(lin['s1_indices']),max_proof_bytes_header=integer(t['prooflen']),internal_m1=integer(a['m1']))
  p['log2stdev']=[integer(a['log2stdev1']),integer(a['log2stdev2']),integer(t['log2stdev3']),integer(t['log2stdev4'])]
  p['stdev_sq']=[self.value(a['stdev1sqr']),self.value(a['stdev2sqr']),self.value(t['stdev3sqr']),self.value(t['stdev4sqr'])]
  p['rejection_modes']=[integer(a['rej1']),integer(a['rej2']),integer(t['rej3']),integer(t['rej4'])]
  p['rejection_factors']=[self.value(s)/2**128 for s in [a['scM1'],a['scM2'],t['scM3'],t['scM4']]]
  p['structures']=dict(lin=lin,tbox=t,abdlop=a,quad=quad,quad_eval=qe,quad_many=qm,ring=ring,dcompress=dc)
  # Nominal sampler widths from encoded exponents; rounded variance integers retained separately.
  p['nominal_stdev']=[1.55*2**e for e in p['log2stdev']]
  p['response_bounds']={'Bz3sqr':self.value(t['Bz3sqr']),'Bz4':self.value(t['Bz4'])}
  p['approx_proof']=int(p['nprime']>0)
  p['kmlwe']=p['m2']-p['kmsis']-p['l']-p['lambda_repetitions']//2-256//p['d']-p['approx_proof']*256//p['d']-2
  p['mlwe_embedding_rank']=p['m2']-p['kmlwe']
  b1sq=4*p['nominal_stdev'][0]**2*2*(p['m1']+z)*p['d']
  p['msis_bound_log2']=math.log2(4*p['eta']*math.sqrt(b1sq+4*p['Bstar_sq']))
  p['MSIS_rhf']=2**(p['msis_bound_log2']**2/(4*p['d']*p['kmsis']*math.log2(p['q'])))
  return p

def inputs(header=None,variant=None,k=None):
 explicit=header is not None or variant is not None
 if header is not None and variant is None:raise ValueError('--header requires explicit --variant (no mutable active-state inference)')
 if variant is None:
  f=ROOT/'ACTIVE_VARIANT.json';variant=json.loads(f.read_text()).get('active_variant','V0') if f.exists() else 'V0'
 variant=variant.upper()
 if variant not in {'B0','B1','V0','V1','V2','V3A','V3','V4','V5','G3','C3','D3','DC3'}:raise ValueError('Unknown variant '+variant)
 compact=variant in COMPACT
 if k is None:k=3 if compact else 0
 if not 0<=k<=8 or (k and not compact):raise ValueError('k requires compact variant and 0 <= k <= 8')
 h=Header(header or DEFAULT_HEADER);p1=h.proof('p1_param');p2=h.proof('p2_param' if not k else f'p2_compact{k}_param')
 provenance={'header_path':str(h.path),'header_sha256':sha(h.path),'variant':variant,'disclosed_k':k,'parameter_k':k,'k_semantics':'compact parameter index; padded k=0 is its parameter layout, NOT actual workload disclosure count','selection_explicit':explicit,'algorithm_sources':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'lazer/lazer.h',ROOT/'lazer/scripts/codegen.sage',ROOT/'lazer/scripts/lnp-tbox-codegen.sage']},'input_authority':'compiled C integer arrays and initializers; comments are descriptive only','limb_bits':64}
 return h,variant,k,p1,p2,provenance

def compact_rows(h):
 rows=[]
 for k in range(9):
  p=h.proof('p2_param' if not k else f'p2_compact{k}_param')
  rows.append(dict(disclosed_attributes_k=k,hidden_attributes_h=8-k,param_symbol=p['symbol'],relation_shape=[8,p['m1']],m1_secret_polys=p['m1'],nbin_binary_polys=p['nbin'],nex_total_polys=p['nex'],msis_bound_log2=round(p['msis_bound_log2'],6),MSIS_rhf_recomputed=round(p['MSIS_rhf'],7),MSIS_rhf_5dec=round(p['MSIS_rhf'],5),max_proof_bytes_header=p['max_proof_bytes_header']))
 return rows
