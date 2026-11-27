"""Download standalone upstream assets once; never read an installed Shutter copy."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets/ai'
COMMIT='a4abfb2979a7bbff3f69f58f58ae324608821e27'
URLS={
 'windows.zip':'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip',
 'linux.zip':'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip',
 'video.pth':'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
 'animation.pth':'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth',
 'realesr-general-x4v3.pth':'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth',
 'realesr-general-wdn-x4v3.pth':'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth',
 'LICENSE-RealESRGAN.txt':f'https://raw.githubusercontent.com/xinntao/Real-ESRGAN/{COMMIT}/LICENSE',
 'LICENSE-ncnn-engine.txt':'https://raw.githubusercontent.com/xinntao/Real-ESRGAN-ncnn-vulkan/master/LICENSE',
 'LICENSE-onnxruntime.txt':'https://raw.githubusercontent.com/microsoft/onnxruntime/main/LICENSE',
 'LICENSE-ncnn.txt':'https://raw.githubusercontent.com/Tencent/ncnn/master/LICENSE.txt',
 'rrdbnet_arch.py':'https://raw.githubusercontent.com/XPixelGroup/BasicSR/master/basicsr/archs/rrdbnet_arch.py',
 'srvgg_arch.py':f'https://raw.githubusercontent.com/xinntao/Real-ESRGAN/{COMMIT}/realesrgan/archs/srvgg_arch.py',
 'LICENSE-BasicSR.txt':'https://raw.githubusercontent.com/XPixelGroup/BasicSR/master/LICENSE.txt',
}
PINNED_COMPACT_HASHES={
 'realesr-general-x4v3.pth':'8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292',
 'realesr-general-wdn-x4v3.pth':'1641f8c4464b9f097c9fdda5589273713f67cf59f3d909e0bd688f0cee269dca',
}

def main():
 cache=ROOT/'.ai-downloads';cache.mkdir(exist_ok=True);ASSETS.mkdir(parents=True,exist_ok=True)
 def download(pair):
  name,url=pair;p=cache/name
  if not p.exists():
   temporary=p.with_suffix(p.suffix+'.download')
   with urllib.request.urlopen(url,timeout=120) as response,temporary.open('wb') as stream:shutil.copyfileobj(response,stream)
   temporary.rename(p)
  digest=hashlib.sha256(p.read_bytes()).hexdigest()
  if name in PINNED_COMPACT_HASHES and digest!=PINNED_COMPACT_HASHES[name]:raise ValueError(f'Unexpected upstream compact weights: {name}')
  return name,{'url':url,'sha256':digest}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:sources=dict(pool.map(download,URLS.items()))
 for platform in ('windows','linux'):
  with zipfile.ZipFile(cache/f'{platform}.zip') as archive:
   for member in archive.infolist():
    p=Path(member.filename);base=p.name
    if base.startswith('realesrgan-ncnn-vulkan') and not base.endswith(('.txt','.md')) and '.' not in base.replace('.exe',''):
     target=ASSETS/platform/('realesrgan-ncnn-vulkan.exe' if platform=='windows' else 'realesrgan-ncnn-vulkan')
    elif 'models' in p.parts and (base.startswith('realesrgan-x4plus.') or base.startswith('realesr-animevideov3')):target=ASSETS/'models'/base
    elif 'license' in base.lower() or base.lower().startswith('readme'):target=ASSETS/'LICENSES'/f'{platform}-{base}'
    else:continue
    if not member.is_dir():
     target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(member));target.chmod(0o755 if target.parent.name in ('windows','linux') else 0o644)
 for name in URLS:
  if name.startswith('LICENSE'):
   target=ASSETS/'LICENSES'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(cache/name,target)
 previous=json.loads((ASSETS/'manifest.json').read_text()) if (ASSETS/'manifest.json').exists() else {}
 manifest={'schema':1,'engine_release':'Real-ESRGAN v0.2.5.0 / ncnn 20220424','model_source_commit':COMMIT,'sources':sources,'files':{}}
 for field in ('cpu_exports','compact_photo'):
  if field in previous:manifest[field]=previous[field]
 for p in ASSETS.rglob('*'):
  if p.is_file() and p.name!='manifest.json':manifest['files'][p.relative_to(ASSETS).as_posix()]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 (ASSETS/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'downloaded_or_reused':len(sources),'asset_files':len(manifest['files'])}))

if __name__=='__main__':main()
