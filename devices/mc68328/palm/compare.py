#!/usr/bin/env python3
"""Compare real Palm firmware runs with pre/post-fix MAME binaries; no vision/model calls."""
import concurrent.futures,hashlib,json,os,pathlib,subprocess
from PIL import Image
root=pathlib.Path(__file__).resolve().parent
cases=[('palmiii','3.3e'),('palmiiic','4.0e'),('palmm100','3.51e')]
def run(item):
 version,system,bios=item
 out=root/'runs'/system/version;out.mkdir(parents=True,exist_ok=False)
 cmd=[str(root/('mame-'+version)),system,'-bios',bios,'-rompath',str(root/'roms'),'-noreadconfig','-skip_gameinfo','-video','none','-sound','none','-nothrottle','-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg'),'-snapshot_directory',str(out/'snap'),'-autoboot_delay','0','-autoboot_script',str(root/'compare.lua'),'-seconds_to_run','25']
 (out/'command.json').write_text(json.dumps(cmd,indent=2))
 with (out/'mame.log').open('w') as f:
  p=subprocess.run(cmd,cwd=out,env={**os.environ,'SDL_VIDEODRIVER':'dummy','MAME_VALIDATION_OUTPUT':str(out)},stdout=f,stderr=subprocess.STDOUT,timeout=90)
 trace=out/'trace.tsv'
 return dict(version=version,system=system,exit=p.returncode,captures=len(list(out.glob('*.pixels'))),trace=trace.exists())
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  results=list(pool.map(run,[(v,s,b) for s,b in cases for v in ['before','after']]))
 comparisons=[]
 for system,bios in cases:
  before=root/'runs'/system/'before';after=root/'runs'/system/'after'
  frames=[]
  for p in sorted(before.glob('*.pixels')):
   q=after/p.name;raw=p.read_bytes();other=q.read_bytes() if q.exists() else b''
   img=Image.open(p.with_suffix('.png')).convert('RGB')
   frames.append(dict(frame=p.stem,equal=raw==other,sha256=hashlib.sha256(raw).hexdigest(),after_sha256=hashlib.sha256(other).hexdigest(),distinct_colors=len(img.getcolors(img.width*img.height) or []),size=img.size))
  comparisons.append(dict(system=system,frames=frames,identical=bool(frames) and len(frames)==9 and all(v['equal'] for v in frames),trace_identical=(before/'trace.tsv').exists() and (after/'trace.tsv').exists() and (before/'trace.tsv').read_bytes()==(after/'trace.tsv').read_bytes()))
 result=dict(runs=results,comparisons=comparisons)
 (root/'comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 success = all(x['exit']==0 and x['captures']==9 for x in results) and all(x['identical'] and x['trace_identical'] for x in comparisons)
 raise SystemExit(0 if success else 1)
