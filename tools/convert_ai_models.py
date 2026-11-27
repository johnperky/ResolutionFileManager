"""Development-only export of upstream pretrained networks; no torch at runtime."""
import hashlib
import json
from pathlib import Path
import sys

def main():
 import torch
 import numpy as np
 import onnxruntime as ort
 root=Path(sys.argv[1]).resolve();cache=root/'.ai-downloads';assets=root/'assets/ai';target=assets/'cpu';target.mkdir(exist_ok=True)
 namespace={'torch':torch,'nn':torch.nn,'F':torch.nn.functional,
  'default_init_weights':lambda *a,**kw:None,
  'make_layer':lambda block,count,**kw:torch.nn.Sequential(*(block(**kw) for _ in range(count))),
  'pixel_unshuffle':torch.nn.functional.pixel_unshuffle}
 for source in ('rrdbnet_arch.py','srvgg_arch.py'):
  lines=(cache/source).read_text().splitlines()
  code='\n'.join(line for line in lines if not line.startswith(('from basicsr','from .arch_util','@ARCH_REGISTRY')))
  exec(compile(code,source,'exec'),namespace)
 torch.set_num_threads(2);torch.manual_seed(4)
 results={}
 for family in ('video','animation'):
  name=target/f'{family}-x4.onnx'
  model=namespace['RRDBNet'](num_in_ch=3,num_out_ch=3,num_feat=64,num_block=23,num_grow_ch=32,scale=4) if family=='video' else namespace['SRVGGNetCompact'](num_in_ch=3,num_out_ch=3,num_feat=64,num_conv=16,upscale=4,act_type='prelu')
  weights=torch.load(cache/f'{family}.pth',map_location='cpu',weights_only=True)
  model.load_state_dict(weights.get('params_ema',weights.get('params',weights)));model.eval()
  sample=torch.rand(1,3,16,16)
  if not name.exists():
   torch.onnx.export(model,sample,str(name),input_names=['input'],output_names=['output'],dynamic_axes={'input':{2:'height',3:'width'},'output':{2:'out_height',3:'out_width'}},opset_version=17,dynamo=False)
  options=ort.SessionOptions();options.intra_op_num_threads=2
  session=ort.InferenceSession(str(name),sess_options=options,providers=['CPUExecutionProvider'])
  actual=session.run(None,{'input':sample.numpy()})[0]
  with torch.no_grad():expected=model(sample).numpy()
  error=float(np.max(np.abs(actual-expected)));assert error<0.0001,(family,error)
  results[family]={'source_weights_sha256':hashlib.sha256((cache/f'{family}.pth').read_bytes()).hexdigest(),'onnx_sha256':hashlib.sha256(name.read_bytes()).hexdigest(),'max_absolute_error':error,'opset':17,'native_scale':4}
 manifest_path=assets/'manifest.json';manifest=json.loads(manifest_path.read_text());manifest['cpu_exports']=results
 for p in target.iterdir():manifest['files'][p.relative_to(assets).as_posix()]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(results),flush=True)

if __name__=='__main__':main()
