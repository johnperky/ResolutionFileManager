"""Publish exact gated Windows assets through GitHub REST; never rebuild.

Uses the existing Git credential helper in memory. Credentials are not logged.
Creates a draft first, resumes it safely, and verifies uploaded asset digests.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = 'johnperky/ResolutionFileManager'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    version=(ROOT/'VERSION.txt').read_text().strip()
    gate=json.loads((ROOT/f'release-output/{version}/RELEASE_READINESS.json').read_text())
    assert gate['readyForRelease'] is True, 'Review incomplete'
    assert sha(ROOT/f'docs/RELEASE_READINESS_{version}.json')==gate['reviewEvidenceSha256'], 'Review evidence changed'
    binary=ROOT/gate['binary']
    assert sha(binary)==gate['binarySha256'], 'Reviewed binary changed'
    for name,digest in gate['sourceSha256'].items():
        assert sha(ROOT/name)==digest, f'Reviewed source changed: {name}'
    approval_path=(ROOT/gate['screenshotApproval']).resolve()
    assert sha(approval_path)==gate['screenshotApprovalSha256'], 'Screenshot approval changed'
    approval=json.loads(approval_path.read_text(encoding='utf-8'))
    assert approval['visualReviewComplete'] and approval['binarySha256']==gate['binarySha256']
    assert len(approval['captures'])==172
    for capture in approval['captures']:
        path=(approval_path.parent/capture['file']).resolve()
        assert path.is_relative_to(approval_path.parent) and sha(path)==capture['sha256'], 'Approved image changed'
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert gate['sourceCommit']==head, 'Assets were verified for a different source commit'
    tag=f'v{version}'
    tagged=subprocess.check_output(['git','rev-parse',tag+'^{commit}'],cwd=ROOT,text=True).strip()
    assert tagged==head, 'Release tag differs from current commit'
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main',f'refs/tags/{tag}'],cwd=ROOT,text=True)
    assert f'{head}\trefs/heads/main' in remote and f'{head}\trefs/tags/{tag}' in remote, 'Source/tag not pushed'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(), 'Uncommitted changes'
    folder=ROOT/f'release-output/{version}'
    checks={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (folder/'SHA256SUMS.txt').read_text().splitlines()}
    assert set(checks)=={f'ResolutionFileManager-{version}-Windows-x64.zip',f'ResolutionFileManager-{version}-Source.zip',f'ResolutionFileManager-{version}.exe'}
    for name,digest in checks.items():assert sha(folder/name)==digest, name
    assert gate['assetsSha256']=={**checks,'SHA256SUMS.txt':sha(folder/'SHA256SUMS.txt')}, 'Assets differ from verified release gate'
    assert checks[f'ResolutionFileManager-{version}.exe']==gate['binarySha256']
    credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True)
    values=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    headers={'Authorization':'Bearer '+values['password'],'Accept':'application/vnd.github+json','User-Agent':'RFM-reviewed-release','X-GitHub-Api-Version':'2022-11-28'}
    def api(path,method='GET',payload=None):
        data=json.dumps(payload).encode() if payload is not None else None
        request=urllib.request.Request('https://api.github.com'+path,data=data,headers={**headers,'Content-Type':'application/json'},method=method)
        with urllib.request.urlopen(request,timeout=120) as response:return json.load(response)
    prefix=f'/repos/{REPO}'
    try:release=api(prefix+'/releases/tags/'+tag)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        release=api(prefix+'/releases','POST',{'tag_name':tag,'target_commitish':head,'name':f'Resolution File Manager {version} — Windows','body':(ROOT/f'RELEASE_NOTES_{version}.md').read_text(encoding='utf-8'),'draft':True,'prerelease':False})
    wanted={**checks,'SHA256SUMS.txt':sha(folder/'SHA256SUMS.txt')}
    assert release['tag_name']==tag and not release['prerelease']
    existing={asset['name']:asset for asset in release['assets']}
    assert not (set(existing)-set(wanted)), 'Unexpected release assets; inspect manually'
    for name,digest in wanted.items():
        if name in existing:
            assert existing[name].get('digest')=='sha256:'+digest, 'Existing asset differs; preserved: '+name
            continue
        assert release['draft'], 'Never add missing assets to a published release automatically'
        path=folder/name
        upload=release['upload_url'].split('{',1)[0]+'?'+urllib.parse.urlencode({'name':name})
        with path.open('rb') as stream:
            request=urllib.request.Request(upload,data=stream,headers={**headers,'Content-Type':'application/octet-stream','Content-Length':str(path.stat().st_size)},method='POST')
            with urllib.request.urlopen(request,timeout=600) as response:asset=json.load(response)
        assert asset['state']=='uploaded' and asset['size']==path.stat().st_size
        assert asset.get('digest')=='sha256:'+digest, 'Uploaded asset digest mismatch: '+name
        print('Verified uploaded asset: '+name,flush=True)
    release=api(prefix+'/releases/'+str(release['id']))
    assert {a['name']:a.get('digest') for a in release['assets']}=={n:'sha256:'+h for n,h in wanted.items()}
    if release['draft']:
        release=api(prefix+'/releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'true'})
    latest=api(prefix+'/releases/latest')
    assert latest['id']==release['id'] and latest['tag_name']==tag and not latest['draft']
    # Verify anonymous public checksum download in addition to API asset hashes.
    checksum=next(a for a in latest['assets'] if a['name']=='SHA256SUMS.txt')
    request=urllib.request.Request(checksum['browser_download_url'],headers={'User-Agent':'RFM-release-download-check'})
    with urllib.request.urlopen(request,timeout=120) as response:
        assert hashlib.sha256(response.read()).hexdigest()==wanted['SHA256SUMS.txt']
    report={'version':version,'url':latest['html_url'],'tag':tag,'commit':head,'binarySha256':gate['binarySha256'],'latest':True,'assets':[{k:a[k] for k in ('name','size','digest','browser_download_url')} for a in latest['assets']],'publicChecksumDownloadVerified':True}
    (folder/'PUBLICATION_VERIFIED.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
