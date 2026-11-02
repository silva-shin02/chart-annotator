import json,sys,collections,statistics as st
d=json.load(open(sys.argv[1])); R=json.load(open(sys.argv[2]))
def tm(t):h,m=t.split(':');return int(h)*60+int(m)
by=collections.defaultdict(list)
for c in d['charts']:
  if c.get('bars_1m'):by[c['ticker']].append(c)
day={}
for tk,L in by.items():
  L.sort(key=lambda c:c['date']);prevC=None;prevD=None
  for c in L:
    K=c['barCols'];B=[dict(zip(K,b)) for b in c['bars_1m']]
    B=[b for b in B if b['v'] and b['v']>0 and b['o'] and b['c']]
    for b in B:b['tm']=tm(b['t'])
    if not B: prevC=None;continue
    gap=(B[0]['o']/prevC-1)*100 if prevC and prevD<c['date'] else None
    day[(tk,c['date'])]=(B,gap,prevC)
    prevC=B[-1]['c'];prevD=c['date']
out=[];miss=0
for r in R:
  k=(r['stock'],r['date'])
  if k not in day or not r.get('time'):miss+=1;continue
  B,gap,pc=day[k];T=tm(r['time'])
  pre=[b for b in B if b['tm']<T]
  cur=[b for b in B if b['tm']==T]
  if not pre:miss+=1;continue
  o=B[0];last=pre[-1]
  ob5=[b for b in B if (b['tm']-540)//5==(o['tm']-540)//5]
  o5o,o5c=ob5[0]['o'],ob5[-1]['c']
  def bucket(t):
    return '9:00-9:10' if t<550 else '9:10-9:30' if t<570 else '9:30-10:00' if t<600 else '10:00-10:30' if t<630 else '10:30-11:30' if t<=690 else '後場'
  e9,e22,e50,e200,vw=[last.get(x) for x in ('ema9','ema22','ema50','ema200','vwap')]
  order='上昇並び' if (e9 and e200 and e9>e22>e50>e200) else '下降並び' if (e9 and e200 and e9<e22<e50<e200) else '混在'
  rng=[b['h']-b['l'] for b in pre[-10:]]; atr=sum(rng)/len(rng)
  hi=max(b['h'] for b in pre);lo=min(b['l'] for b in pre)
  vols=[b['v'] for b in pre[-20:]]
  x=dict(r)
  lv=r['level']
  x.update(
    gap=None if gap is None else round(gap,2),
    gcat=None if gap is None else ('大幅GD' if gap<=-3 else 'GD' if gap<=-1 else '大幅GU' if gap>=3 else 'GU' if gap>=1 else 'ほぼ同値'),
    yori='陽線' if o['c']>o['o'] else '陰線' if o['c']<o['o'] else '同値',
    yori5='陽線' if o5c>o5o else '陰線' if o5c<o5o else '同値',
    nOpen=len(pre), tb=bucket(T),
    vwap='VWAPの上' if (vw and last['c']>=vw) else 'VWAPの下',
    order=order, e9u200=('9EMAが200EMAの上' if (e9 and e200 and e9>e200) else '9EMAが200EMAの下'),
    gu22=bool(gap is not None and gap>=1 and all(b['c']>=b['ema22'] for b in pre if b.get('ema22'))),
    e9hold=all(b['c']>=b['ema9'] for b in pre if b.get('ema9')),
    vsOpen='寄り値より上' if last['c']>=o['o'] else '寄り値より下',
    vsPrev=None if not pc else ('前日終値より上' if last['c']>=pc else '前日終値より下'),
    atr=round(atr,1), atrp=round(atr/last['c']*100,3),
    aAtr=None if r['alpha'] is None else round(r['alpha']/atr,2) if atr>0 else None,
    rangeP=round((hi-lo)/last['c']*100,2),
    fiveEnd=(T%5==4),
    volx=round((cur[0]['v'] if cur else 0)/(sum(vols)/len(vols)),2) if vols and sum(vols)>0 else None,
    rnNear=None if lv is None else (abs(lv-round(lv/100)*100)<=10),
    dayUp=last['c']>=o['o'],
    price=last['c'])
  out.append(x)
json.dump(out,open(sys.argv[3],'w'),ensure_ascii=False)
print('ctx',len(out),'miss',miss)
