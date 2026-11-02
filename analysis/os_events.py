import json,sys,collections
src,dst=sys.argv[1],sys.argv[2]
d=json.load(open(src))
sn={s['id']:s['text'] for s in (d.get('snippets') or [])}
def tm(t):h,m=t.split(':');return int(h)*60+int(m)
AM=690
by=collections.defaultdict(list)
for c in d['charts']:
  if c.get('bars_1m'): by[c['ticker']].append(c)
def stamps_yori(c):
  out=[]
  for tf,arr in (c.get('strokes') or {}).items():
    for s in arr or []:
      if s.get('type')!='text':continue
      t=sn.get(s.get('snipId'),'') if s.get('_snippet') else ''
      t=t or (s.get('text') or '')
      p=s.get('pointer') or {}
      if '寄り' in t and p.get('tipTm') is not None: out.append(p['tipTm'])
  return out
events=[]; days=[]
PAT={'P1':('bl','bh'),'P2':('bl','bl'),'P3':('c','c'),'P4':('bh','bh')}
for tk,L in by.items():
  L.sort(key=lambda c:c['date']); prevC=None; prevD=None
  for c in L:
    K=c['barCols']; B=[dict(zip(K,b)) for b in c['bars_1m']]
    B=[b for b in B if b['v'] and b['v']>0 and b['o'] and b['c']]
    for b in B: b['tm']=tm(b['t'])
    if not B: prevC=None; continue
    gap=(B[0]['o']/prevC-1)*100 if (prevC and prevD and prevD<c['date']) else None
    prevC=B[-1]['c']; prevD=c['date']
    if B[0]['tm']>600: continue
    st=stamps_yori(c)
    for tf in ('1m','5m'):
      if tf=='1m':
        ob=dict(o=B[0]['o'],h=B[0]['h'],l=B[0]['l'],c=B[0]['c']); i0=1
      else:
        b0=(B[0]['tm']-540)//5; grp=[b for b in B if (b['tm']-540)//5==b0]
        ob=dict(o=grp[0]['o'],h=max(b['h'] for b in grp),l=min(b['l'] for b in grp),c=grp[-1]['c']); i0=len(grp)
      bull=ob['c']>ob['o']; bear=ob['c']<ob['o']
      lines={'bh':max(ob['o'],ob['c']),'bl':min(ob['o'],ob['c']),'c':ob['c']}
      # 5m engulf: 2nd 5m bucket after open bucket
      b0=(B[0]['tm']-540)//5
      g1=[b for b in B if (b['tm']-540)//5==b0]; g2=[b for b in B if (b['tm']-540)//5==b0+1]
      eng=None; engEnd=None
      if g1 and g2:
        f=dict(o=g1[0]['o'],c=g1[-1]['c']); s2=dict(o=g2[0]['o'],c=g2[-1]['c'])
        eng=(f['c']<f['o'] and s2['c']>s2['o'] and s2['c']>=f['o'] and s2['o']<=f['c'])
        engEnd=540+(b0+2)*5
      days.append(dict(tk=tk,d=c['date'],tf=tf,gap=gap,bull=bull,bear=bear))
      for pk,(lb,lc) in PAT.items():
        Lb=lines[lb]; Lc=lines[lc]
        i=i0
        while i<len(B) and B[i]['tm']<=AM and not(B[i]['c']<Lb): i+=1
        if i>=len(B) or B[i]['tm']>AM: continue
        j=i+1
        while j<len(B) and B[j]['tm']<=AM and not(B[j]['h']>Lc): j+=1
        if j>=len(B) or B[j]['tm']>AM: continue
        X=B[j]
        seg=B[i:j]; bot=min(seg,key=lambda b:b['l']); ib=B.index(bot)
        pre=B[0:j]
        def near(a,b,pct=0.1): return a and b and abs(a-b)/b*100<=pct
        R=round(bot['l']/100)*100
        ema_sup=any(bot.get(k) and bot['l']<=bot[k]*1.0005 and bot['c']>=bot[k] for k in ('ema9','ema22','ema50','ema200'))
        # outcomes
        push=None; mx=0
        for k in range(j,min(len(B),j+30)):
          mx=max(mx,B[k]['h']-Lc)
          if B[k]['c']<Lc: push=k-j; break
        osmax=mx if push is not None else max(B[k]['h'] for k in range(j,min(len(B),j+15)))-Lc
        drop=None
        if push is not None:
          lo=min(b['l'] for b in B[j+push:j+push+6]); drop=Lc-lo
        nx=B[j+1] if j+1<len(B) else None
        def fut(n):
          return (B[j+n]['c']-Lc)/Lc*100 if j+n<len(B) else None
        w=B[j:j+31]
        e=dict(tk=tk,d=c['date'],tf=tf,p=pk,t=X['t'],line=round(Lc,1),px=Lc,
          gap=None if gap is None else round(gap,2),bull=bull,bear=bear,
          brk=B[i]['t'],bot=bot['t'],
          # conditions
          c15=(j<15), c910=(X['tm']<550),
          cGU22=(gap is not None and gap>=1 and all(b['c']>=b['ema22'] for b in pre if b.get('ema22'))),
          cE9=all(b['c']>=b['ema9'] for b in pre if b.get('ema9')),
          cVW=bool(bot.get('vwap') and (near(bot['l'],bot['vwap']) or bot['l']<bot['vwap']<bot['c'])),
          cRN=(abs(bot['l']-R)<=10),
          cEMA=ema_sup,
          cFast=((j-ib)<=3),
          cEng=bool(eng and engEnd is not None and X['tm']>=engEnd),
          c3up=(j>=3 and all(B[k]['c']>B[k]['o'] for k in range(j-2,j+1))),
          # outcomes
          os=round(osmax,1), osp=round(osmax/Lc*100,3),
          xc=(X['c']>Lc), nb=(nx is not None and nx['c']<nx['o']), nh=(nx is not None and nx['h']>X['h']),
          push=push, drop=None if drop is None else round(drop,1), dropp=None if drop is None else round(drop/Lc*100,3),
          r5=fut(5), r10=fut(10),
          up30=round((max(b['h'] for b in w)-Lc)/Lc*100,3), dn30=round((min(b['l'] for b in w)-Lc)/Lc*100,3),
          stamp=any(abs(s-X['tm'])<=5 for s in st))
        for k in ('r5','r10'):
          if e[k] is not None: e[k]=round(e[k],3)
        del e['px']
        events.append(e)
json.dump(dict(events=events,days=days,exportedAt=d.get('exportedAt'),nCharts=len(d['charts'])),open(dst,'w'),ensure_ascii=False)
print(len(events),len(days))
import collections as C
print(C.Counter((e['tf'],e['p']) for e in events))
print('stamped',sum(e['stamp'] for e in events))
