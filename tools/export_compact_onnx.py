"""Export compact denoising variants from cached official weights; no downloads."""
import json,hashlib,sys
from pathlib import Path
import torch,numpy as np,onnxruntime as ort
root=Path(__file__).resolve().parents[1]; cache=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'.ai-downloads';out=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else cache/'compact-export';out.mkdir(parents=True,exist_ok=True)
ns={'torch':torch,'nn':torch.nn,'F':torch.nn.functional}
code='\n'.join(x for x in (cache/'srvgg_arch.py').read_text().splitlines() if not x.startswith(('from basicsr','@ARCH_REGISTRY')))
exec(code,ns); torch.set_num_threads(2); torch.manual_seed(4)
def load(name):
 w=torch.load(cache/name,map_location='cpu',weights_only=True); return w.get('params_ema',w.get('params',w))
a=load('realesr-general-x4v3.pth');b=load('realesr-general-wdn-x4v3.pth'); report={}
for label,strength in [('weak',0),('medium',.5),('strong',1)]:
 model=ns['SRVGGNetCompact'](num_in_ch=3,num_out_ch=3,num_feat=64,num_conv=32,upscale=4,act_type='prelu')
 model.load_state_dict({k:strength*a[k]+(1-strength)*b[k] for k in a});model.eval();sample=torch.rand(1,3,16,16);p=out/(label+'.onnx')
 torch.onnx.export(model,sample,str(p),input_names=['input'],output_names=['output'],dynamic_axes={'input':{2:'height',3:'width'},'output':{2:'out_height',3:'out_width'}},opset_version=17,dynamo=False)
 opt=ort.SessionOptions();opt.intra_op_num_threads=2;sess=ort.InferenceSession(str(p),sess_options=opt,providers=['CPUExecutionProvider'])
 with torch.no_grad(): expected=model(sample).numpy()
 error=float(np.max(np.abs(expected-sess.run(None,{'input':sample.numpy()})[0])));assert error<.0001,error
 report[label]={'max_absolute_error':error,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
 print(label,error,flush=True)
report['weights']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in cache.glob('realesr-general*.pth')};(out/'exports.json').write_text(json.dumps(report,indent=2))
