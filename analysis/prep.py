# 全チャートを日ごとの足にまとめる。EMA は前日から連続で計算し直す (前日チャートがあるとき)
import json,sys,collections,pickle
d=json.load(open(sys.argv[1]))
def tm(t):h,m=t.split(':');return int(h)*60+int(m)
A={9:2/10,22:2/23,50:2/51,200:2/201}
by=collections.defaultdict(list)
for c in d['charts']:
  if c.get('bars_1m'):by[c['ticker']].append(c)
days=[]
for tk,L in by.items():
  L.sort(key=lambda c:c['date']);prev=None
  for c in L:
    K=c['barCols'];B=[dict(zip(K,b)) for b in c['bars_1m']]
    B=[b for b in B if b['o'] and b['c'] and b['h'] and b['l']]
    if not B:prev=None;continue
    for b in B:b['tm']=tm(b['t'])
    # 出来高0の足は直前終値で埋まっている想定。約定の無い足は落とす(場中の判定に使わない)
    T=[b for b in B if b['v'] and b['v']>0]
    if len(T)<30:prev=None;continue
    seed=prev['ema'] if prev and prev['date']<c['date'] else None
    e={n:(seed[n] if seed else T[0]['c']) for n in A}
    for b in T:
      for n,a in A.items(): e[n]=e[n]+a*(b['c']-e[n]); b['e%d'%n]=e[n]
      if not seed: pass
    # VWAP は取り込み値 (当日リセット)
    for b in T:
      if not b.get('vwap'):b['vwap']=b['c']
    day=dict(tk=tk,date=c['date'],B=T,seeded=bool(seed),
      prevC=prev['c'] if prev and prev['date']<c['date'] else None,
      prevH=prev['h'] if prev and prev['date']<c['date'] else None,
      prevL=prev['l'] if prev and prev['date']<c['date'] else None,
      vp=c.get('vp_1m'))
    days.append(day)
    prev=dict(date=c['date'],ema={n:e[n] for n in A},c=T[-1]['c'],h=max(b['h'] for b in T),l=min(b['l'] for b in T))
pickle.dump(days,open(sys.argv[2],'wb'))
print(len(days),'days, seeded',sum(x['seeded'] for x in days))
