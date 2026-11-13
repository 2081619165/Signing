import urllib.request,json,pathlib
root=pathlib.Path('.local-tests')
for repo in ['show7/signature-extractor','leopens/seal-extractor']:
 try:
  meta=json.load(urllib.request.urlopen('https://api.github.com/repos/'+repo+'/commits/'+{'show7/signature-extractor':'f7da5df17bda46a56bf588baa78843baa5b8779a','leopens/seal-extractor':'4e571b3f25cc8431756476e96976c392abda398e'}[repo],timeout=25)); sha=meta['sha']; dest=root/repo.split('/')[1];dest.mkdir(exist_ok=True)
  (dest/'VERSION.json').write_text(json.dumps({'repo':repo,'commit':sha}),encoding='utf-8')
  tree=json.load(urllib.request.urlopen('https://api.github.com/repos/'+repo+'/git/trees/'+sha+'?recursive=1',timeout=25))
  for f in tree['tree']:
   p=f['path']
   if f['type']=='blob' and (p.endswith(('.py','.md','.txt','.toml','.json')) or p=='LICENSE'):
    out=dest/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(urllib.request.urlopen('https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+p,timeout=25).read())
  print(repo,sha)
 except Exception as e: print(repo,repr(e))
