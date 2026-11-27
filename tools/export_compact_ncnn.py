"""Development-only SRVGG converter. No runtime torch requirement; emits isolated staging files."""
from pathlib import Path
import torch,numpy as np,struct,json,hashlib,sys
root=Path(__file__).resolve().parents[1];cache=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'.ai-downloads';out=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else cache/'compact-export';out.mkdir(parents=True,exist_ok=True)
def state(p):
 w=torch.load(p,map_location='cpu',weights_only=True);return w.get('params_ema',w.get('params',w))
def half_bytes(weight):
 values=weight.astype('<f2'); bits=values.view('<u2'); rounded_up=np.abs(values.astype('float32'))>np.abs(weight);bits[rounded_up]-=1;small=np.abs(weight)<2**-14;bits[small]=bits[small]&0x8000;return bits.tobytes()
def export(w,name,half):
 layers=['Input input 0 1 data','Split split 1 2 data base main'];blob='main';binary=bytearray()
 count=max(int(k.split('.')[1]) for k in w if k.startswith('body.'))+1
 for i in range(count):
  weight=w[f'body.{i}.weight'].numpy();dest=f'v{i}'
  if weight.ndim==4:
   layers.append(f'Convolution conv{i} 1 1 {blob} {dest} 0={weight.shape[0]} 1=3 4=1 5=1 6={weight.size}')
   binary.extend(struct.pack('<I',0x01306b47 if half else 0));binary.extend(half_bytes(weight) if half else weight.astype('<f4').tobytes());binary.extend(w[f'body.{i}.bias'].numpy().astype('<f4').tobytes())
  else:
   layers.append(f'PReLU prelu{i} 1 1 {blob} {dest} 0={weight.size}');binary.extend(weight.astype('<f4').tobytes())
  blob=dest
 layers.extend([f'PixelShuffle shuffle 1 1 {blob} shuffled 0=4','Interp nearest 1 1 base upbase 0=1 1=4.000000e+00 2=4.000000e+00','BinaryOp add 2 1 shuffled upbase output'])
 (out/(name+'.param')).write_text('7767517\n'+f'{len(layers)} {len(layers)+1}\n'+'\n'.join(layers)+'\n',encoding='utf-8',newline='\n')
 (out/(name+'.bin')).write_bytes(binary);return bytes(binary)
animation=export(state(cache/'animation.pth'),'animation-writer-validation',True)
expected=(root/'assets/ai/models/realesr-animevideov3-x4.bin').read_bytes();assert animation==expected,'Writer differs from trusted bundled animation binary'
a=state(cache/'realesr-general-x4v3.pth');b=state(cache/'realesr-general-wdn-x4v3.pth');w={k:.5*a[k]+.5*b[k] for k in a}
for name,half in [('compact-medium-fp32',False),('compact-medium-fp16',True)]:export(w,name,half)
(out/'export-evidence.json').write_text(json.dumps({'animation_binary_exact_match':True,'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.iterdir() if p.suffix in ('.bin','.param')}},indent=2))
print('Animation writer byte-identical to bundled binary; compact experimental exports saved.')



