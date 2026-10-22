"""Explicit official-release checks and bounded, SHA256-verified downloads."""
import hashlib
import json
import re
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse,unquote

REPO='https://github.com/tugepaopao/Shutdown-Tool'
API='https://api.github.com/repos/tugepaopao/Shutdown-Tool/releases/latest'
MAX_INSTALLER=150*1024*1024

def version(value):
    match=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)',str(value))
    if not match:raise ValueError('版本号无效或不是正式版')
    return tuple(map(int,match.groups()))

def official_asset(url):
    parsed=urlparse(url)
    return parsed.scheme=='https' and parsed.netloc=='github.com' and parsed.path.startswith('/tugepaopao/Shutdown-Tool/releases/download/')

def _open(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Shutdown-Tool-update','Accept':'application/vnd.github+json' if url==API else 'application/octet-stream'})
    response=urllib.request.urlopen(request,timeout=20)
    final=urlparse(response.geturl())
    if final.scheme!='https' or final.hostname not in ('api.github.com','github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):
        response.close();raise ValueError('下载重定向到了非官方地址')
    return response

def _bytes(url,limit):
    with _open(url) as response:data=response.read(limit+1)
    if len(data)>limit:raise ValueError('服务器响应超过大小限制')
    return data

def check(current):
    try:data=json.loads(_bytes(API,2*1024*1024))
    except urllib.error.HTTPError as exc:
        if exc.code not in (403,429):raise
        return _page_release(current)
    if data.get('draft') or data.get('prerelease'):raise ValueError('没有可用的正式版本')
    tag=data.get('tag_name','');latest=version(tag)
    if latest<=version(current):return None
    filename=f'Shutdown-Tool-v{".".join(map(str,latest))}-Setup.exe'
    assets=data.get('assets',[])
    asset=next((a for a in assets if a.get('name')==filename),None)
    if not asset or not official_asset(asset.get('browser_download_url','')):raise ValueError('正式版缺少官方下载包')
    size=asset.get('size',0)
    if not isinstance(size,int) or not 0<size<=MAX_INSTALLER:raise ValueError('安装包大小异常')
    digest=asset.get('digest') or ''
    if digest.startswith('sha256:'):digest=digest[7:]
    if not re.fullmatch('[0-9a-fA-F]{64}',digest):
        checks=next((a for a in assets if a.get('name')=='SHA256.txt'),None)
        if not checks or not official_asset(checks.get('browser_download_url','')):raise ValueError('缺少 SHA256 校验信息，未下载')
        text=_bytes(checks['browser_download_url'],65536).decode('utf-8-sig')
        match=re.search(r'^([0-9a-fA-F]{64})\s+\*?'+re.escape(filename)+r'\s*$',text,re.M)
        if not match:raise ValueError('安装包校验信息不完整')
        digest=match[1]
    return dict(tag=tag,name=filename,url=asset['browser_download_url'],size=size,sha256=digest.lower(),notes=str(data.get('body') or '此版本未提供更新说明。')[:30000])

def _page_release(current):
    """Rate-limit fallback uses only the same official HTTPS release and hashes."""
    with _open(REPO+'/releases/latest') as response:
        final=response.geturl()
        if not final.startswith(REPO+'/releases/tag/'):raise ValueError('无法确认官方正式版本')
        tag=unquote(urlparse(final).path.rsplit('/',1)[-1]);latest=version(tag)
        if latest<=version(current):return None
        html=response.read(2*1024*1024).decode('utf-8',errors='replace')
    name=f'Shutdown-Tool-v{".".join(map(str,latest))}-Setup.exe'
    base=REPO+'/releases/download/'+tag+'/'
    checks=_bytes(base+'SHA256.txt',65536).decode('utf-8-sig')
    match=re.search(r'^([0-9a-fA-F]{64})\s+\*?'+re.escape(name)+r'\s*$',checks,re.M)
    if not match:raise ValueError('官方发布页缺少安装包校验信息')
    with _open(base+name) as response:size=int(response.headers.get('Content-Length',0))
    if not 0<size<=MAX_INSTALLER:raise ValueError('无法验证安装包大小')
    from html.parser import HTMLParser
    class Notes(HTMLParser):
        def __init__(self):super().__init__();self.depth=0;self.parts=[]
        def handle_starttag(self,t,a):
            if t=='div':
                if self.depth:self.depth+=1
                elif 'markdown-body' in dict(a).get('class',''):self.depth=1
            if self.depth and t in ('p','li','h1','h2','h3','br'):self.parts.append('\n')
        def handle_endtag(self,t):
            if t=='div' and self.depth:self.depth-=1
        def handle_data(self,data):
            if self.depth:self.parts.append(data)
    parser=Notes();parser.feed(html)
    notes=''.join(parser.parts).strip()[:30000] or '已通过官方发布页确认正式版本。'
    return dict(tag=tag,name=name,url=base+name,size=size,sha256=match[1].lower(),notes=notes)

def download(release,cancel,progress):
    if not official_asset(release['url']):raise ValueError('只允许下载本项目官方安装包')
    folder=Path(tempfile.mkdtemp(prefix='shutdown-update-'));partial=folder/'installer.part';target=folder/'Setup.exe'
    digest=hashlib.sha256();size=0
    try:
        with _open(release['url']) as response,partial.open('wb') as output:
            while True:
                if cancel.is_set():raise InterruptedError('下载已取消')
                block=response.read(128*1024)
                if not block:break
                size+=len(block)
                if size>release['size'] or size>MAX_INSTALLER:raise ValueError('下载大小与发布信息不一致')
                output.write(block);digest.update(block);progress(size,release['size'])
        if size!=release['size'] or digest.hexdigest()!=release['sha256']:raise ValueError('安装包校验失败，请重试')
        if cancel.is_set():raise InterruptedError('下载已取消')
        partial.replace(target);return target
    except Exception:
        partial.unlink(missing_ok=True);folder.rmdir();raise
