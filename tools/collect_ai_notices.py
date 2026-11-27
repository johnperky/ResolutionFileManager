"""Retain actual runtime licences and upstream notice texts in AI resources."""
import ctypes
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'assets/ai'
URLS={
 'LICENSE-libwebp.txt':'https://raw.githubusercontent.com/webmproject/libwebp/main/COPYING',
 'LICENSE-stb.txt':'https://raw.githubusercontent.com/nothings/stb/master/LICENSE',
 'LICENSE-dirent.txt':'https://raw.githubusercontent.com/tronkko/dirent/master/LICENSE',
 'COPYING-LGPL-2.1.txt':'https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.LGPLv2.1',
 'COPYING-LGPL-3.txt':'https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.LGPLv3',
 'COPYING-GPL-2.txt':'https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.GPLv2',
 'COPYING-GPL-3.txt':'https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.GPLv3',
}

def main():
    destination=ASSETS/'LICENSES';destination.mkdir(exist_ok=True)
    record={}
    for name,url in URLS.items():
        target=destination/name
        if not target.exists():target.write_bytes(urllib.request.urlopen(url,timeout=60).read())
        record[name]={'url':url,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    for package in ('onnxruntime','numpy','av'):
        distribution=importlib.metadata.distribution(package)
        record[package]={'version':distribution.version,'source':'https://pypi.org/project/'+package+'/'+distribution.version+'/'}
        for file in distribution.files or ():
            if file.suffix=='.pyc':continue
            if any(word in str(file).lower() for word in ('license','copying','notice','authors.rst')):
                source=Path(distribution.locate_file(file))
                if source.is_file():
                    target=destination/(sys.platform+'-'+package)/Path(str(file)).name;target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
    import av
    record['av_libraries']=av.library_versions
    distribution=importlib.metadata.distribution('av')
    for file in distribution.files or ():
        if 'avcodec' not in file.name or file.suffix not in ('.dll','.so') and '.so.' not in file.name:continue
        library=ctypes.CDLL(str(distribution.locate_file(file)))
        for symbol in ('avcodec_license','avcodec_configuration'):
            function=getattr(library,symbol);function.restype=ctypes.c_char_p;record[symbol]=function().decode()
        break
    record['sources']={'PyAV':'https://github.com/PyAV-Org/PyAV/tree/v'+av.__version__,'PyAV_wheel_builds':'https://github.com/PyAV-Org/pyav-wheels','FFmpeg':'https://ffmpeg.org/download.html#get-sources','RealESRGAN':'https://github.com/xinntao/Real-ESRGAN','ncnn':'https://github.com/Tencent/ncnn','ONNXRuntime':'https://github.com/microsoft/onnxruntime'}
    (destination/('RUNTIME-'+sys.platform+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    path=ASSETS/'manifest.json';manifest=json.loads(path.read_text())
    for file in ASSETS.rglob('*'):
        if file.is_file() and file.name!='manifest.json':manifest['files'][file.relative_to(ASSETS).as_posix()]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'platform':sys.platform,'files':len(manifest['files']),'FFmpeg_wheel_license':record.get('avcodec_license','see retained source notices')}))

if __name__=='__main__':main()
