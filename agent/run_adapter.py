"""Run a user-configured real model adapter once. No fake outputs/API assumptions.
The adapter owns authentication and protocol; keys remain outside this package.
"""
import argparse,json,subprocess,time,hashlib
from pathlib import Path

def run(config,input_path,output_path,receipt_path,timeout=600):
 cfg=json.loads(config.read_text());argv=cfg.get('argv')
 if not isinstance(argv,list) or not argv or not all(isinstance(s,str) for s in argv):raise ValueError('argv must be an explicit command array')
 if not cfg.get('capabilities_verified'):raise ValueError('Probe real model/tool capabilities before running; not verified')
 if output_path.exists():raise ValueError('Output already exists; use a fresh run path to prevent stale-output success')
 args=[x.replace('{input}',str(input_path.resolve())).replace('{output}',str(output_path.resolve())) for x in argv]
 start=time.time();receipt={'model_id':cfg.get('id'),'argv':args,'input_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),'start_epoch':start,'status':'STARTED'}
 try:
  proc=subprocess.run(args,capture_output=True,text=True,timeout=timeout,check=False,shell=False)
  receipt.update(returncode=proc.returncode,stdout=proc.stdout,stderr=proc.stderr)
  if proc.returncode or not output_path.is_file() or output_path.stat().st_size==0:receipt['status']='FAILED'
  else:receipt.update(status='PRODUCED_NOT_REVIEWED',output_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest())
 except subprocess.TimeoutExpired:receipt['status']='TIMEOUT'
 except OSError as e:receipt.update(status='BLOCKED',error=str(e))
 receipt['elapsed_seconds']=round(time.time()-start,3);receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2));return receipt
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('model_config',type=Path);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('receipt',type=Path);ap.add_argument('--timeout',type=int,default=600);a=ap.parse_args()
 try:r=run(a.model_config,a.input,a.output,a.receipt,a.timeout);raise SystemExit(0 if r['status']=='PRODUCED_NOT_REVIEWED' else 1)
 except (OSError,ValueError) as e:raise SystemExit(str(e))
