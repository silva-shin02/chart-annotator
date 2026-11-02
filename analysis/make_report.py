# os3.json → os3_rep.json (軽量化) → os_search.html (テンプレートに埋め込み)
import json,os,sys
P=os.path.dirname(os.path.abspath(__file__))+'/'
D=json.load(open(P+'os3.json'))
rows=[]
for k,v in D['agg'].items():
  x=v[2:];rows.append(json.loads(k)+[v[0],v[1]]+[round(x[i]) for i in range(16) if i%4!=3])
smp={}
for k,v in D['samples'].items():
  kk=json.loads(k);L=[]
  for s in v[:25]:
    s=dict(s);s['vp']=[[a,b] for a,b in s['vp'] if b>0];L.append(s)
  smp[kk[0]+'|'+kk[1]]=L
d=json.dumps({'rows':rows,'samples':smp,'nDays':D['nDays'],'dates':D['dates']},ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
t=open(P+'os3tpl.html',encoding='utf-8').read()
out=sys.argv[1] if len(sys.argv)>1 else P+'../os_search.html'
open(out,'w',encoding='utf-8').write(t.replace('__DATA__',d))
print('written',out,os.path.getsize(out))
