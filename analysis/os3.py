# 逆張り空売りの検証エンジン (8/20以降・前場・ティックVAP)
# ライン L → (割れて下にいる状態から) OS: 高値が L を超える足 = OS1。
# EP = L から上の高VAP帯 (平均×r_hi 以上で始まり、平均×r_cont 以上が続く所まで) の上端 −1円 (大RN ちょうど＆VAP値0 は補正なし)。
# OS1〜OS3 で高値が EP を1円でも上回れば約定(EP)。決済 = EP足の終値 / H1 / H2。損切り = 高値−EP≥15円 に触れた足の終値。手数料0。
import pickle,sys,collections,json
days=[d for d in pickle.load(open(sys.argv[1],'rb')) if d['date']>='2026-08-20' and d.get('vp')]
AM=690; CUT=15
RCOMBO=[(1.5,1.0),(1.5,1.2),(1.5,1.5),(2.0,1.0),(2.0,1.5),(2.0,2.0),(3.0,1.0),(3.0,1.5),(3.0,2.0)]
MAXVAP=10.0
def tick(p): return 1.0 if p>3000 else 0.5
def k10(p): return round(p*10)
def tb(t): return '9:00-9:30' if t<570 else '9:30-10:00' if t<600 else '10:00-10:30' if t<630 else '10:30-11:30'
AGG=collections.defaultdict(lambda:[0,0]+[0,0,0.0,0.0]*4)   # n_sig, n_fill, (win, loss, sum, sumsq) x3
SAMPLES=collections.defaultdict(list)
def ep_of(prof,mean,L,rh,rc,tk):
  p=round(L/tk)*tk
  if p<L-1e-9: p+=tk
  start=None;q=p
  while q-L<=MAXVAP+1e-9:
    if prof.get(k10(q),0)>=rh*mean: start=q;break
    q+=tk
  if start is None: return None
  top=start;q=start+tk
  while prof.get(k10(q),0)>=rc*mean and q-L<=MAXVAP+1e-9: top=q;q+=tk
  vapval=top-L
  if abs(L-round(L/100)*100)<1e-9 and vapval<=1e-9: return top
  return top-1.0
for day in days:
  S=[b for b in day['B'] if 540<=b['tm']<=AM]
  if len(S)<30: continue
  tk=tick(S[0]['c']); vp=day['vp']
  # 各足の直前までの累計VAP
  pre=[];cur=collections.defaultdict(float)
  for b in S:
    pre.append(dict(cur))
    a=vp.get(b['t']) or []
    for j in range(0,len(a)-1,2): cur[k10(a[j])]+=a[j+1]
  pre.append(dict(cur))
  def meanof(pr):
    v=[x for x in pr.values() if x>0]; return sum(v)/len(v) if v else 0
  means=[meanof(p) for p in pre]
  lines=[]   # (type, L, creation index, flags)
  n=len(S)
  # 1 底抜けライン (2026-11-02 ユーザー定義の「底支え」)
  #   底支え = ①ヒゲで指標線を下に貫いたが実体は上で確定 / ②実体で下に確定→次の足の終値で上に復帰
  #            ③実体で下に確定→次の足が底つきサイン→その次の足の終値で上に復帰
  #   底抜け = 実体で下に確定→次の足が続落(終値がその足より下)。次の足が底つきサインなら、その次の足が続落(サインの足より下)
  #   底支えが N 回以上(1/2/3)あったあとに底抜け → ライン = 割った足の指標線の値段
  def bottom_sign(i):
    b=S[i];rng=b['h']-b['l']
    if rng<=0: return False
    body=abs(b['c']-b['o']);up=b['h']-max(b['o'],b['c']);lo=min(b['o'],b['c'])-b['l']
    if body<=rng*0.2: return True                                  # 十字線・トンボ・トウバ
    if lo>=body*2 and up<=body: return True                         # カラカサ・たくり線・ハンマー
    if up>=body*2 and lo<=body: return True                         # 逆カラカサ
    if i>0 and b['h']<=S[i-1]['h'] and b['l']>=S[i-1]['l']: return True   # はらみ線
    return False
  for X in ('e9','e22','e50','e200','vwap'):
    sup=0;i=1
    while i<n-1:
      b=S[i];x=b[X]
      if b['c']>=x:
        if min(b['o'],b['c'])>=x and b['l']<x: sup+=1             # ①
        i+=1;continue
      # 実体で下に確定
      nb=S[i+1]
      if nb['c']>=nb[X]: sup+=1;i+=2;continue                      # ②
      if bottom_sign(i+1) and i+2<n:
        n2=S[i+2]
        if n2['c']>=n2[X]: sup+=1;i+=3;continue                    # ③
        if n2['c']<nb['c']:
          for N in (1,2,3):
            if sup>=N: lines.append(('底抜け %s 底支え%d回'%(X,N),x,i+2,{}))
          sup=0;i+=3;continue
        sup=0;i+=3;continue                                        # どちらでもない＝数え直し
      if nb['c']<b['c']:
        for N in (1,2,3):
          if sup>=N: lines.append(('底抜け %s 底支え%d回'%(X,N),x,i+1,{}))
        sup=0;i+=2;continue
      sup=0;i+=2
  # 2 寄り足ライン (1分・5分)
  o=S[0]; g5=[b for b in S if (b['tm']-540)//5==(S[0]['tm']-540)//5]
  for tf,ob,st in (('1分',dict(o=o['o'],h=o['h'],l=o['l'],c=o['c']),1),('5分',dict(o=g5[0]['o'],h=max(x['h'] for x in g5),l=min(x['l'] for x in g5),c=g5[-1]['c']),len(g5))):
    col='陽線' if ob['c']>ob['o'] else '陰線' if ob['c']<ob['o'] else None
    if not col: continue
    for nm,L in ((('実体高値(=終値)' if col=='陽線' else '実体高値(=始値)'),max(ob['o'],ob['c'])),(('実体安値(=始値)' if col=='陽線' else '実体安値(=終値)'),min(ob['o'],ob['c'])),('上ヒゲ先',ob['h']),('下ヒゲ先',ob['l'])):
      for i in range(st,n):
        if S[i]['c']<L: lines.append(('寄り足%s %s %s'%(tf,col,nm),L,i,{}));break
  # 3 前日終値/高値/安値
  for nm,key in (('前日終値','prevC'),('前日高値','prevH'),('前日安値','prevL')):
    L=day.get(key)
    if not L: continue
    if S[0]['o']<L: lines.append((nm,L,0,{}))
    else:
      for i in range(1,n):
        if S[i]['c']<L: lines.append((nm,L,i,{}));break
  # 4 RN と 底つき(新)
  lo=min(b['l'] for b in S);hi=max(b['h'] for b in S)
  for R in range(int(lo//50)*50,int(hi)+51,50):
    big=(R%100==0)
    for i in range(1,n):
      if S[i-1]['c']>=R and S[i]['c']<R:
        lines.append(('大RN' if big else '中RN',R,i,{}))
        if big:
          pr=pre[i+1];m=means[i+1]
          bounce=any(abs(S[j]['l']-R)<=10 and S[j]['c']>R for j in range(0,i))
          for r in (1.5,2.0,3.0):
            q=R-10;ok=False
            while q<=R+10:
              if pr.get(k10(q),0)>=r*m: ok=True;break
              q+=tk
            if ok: lines.append(('底つき(新) 大RN±10に高VAP×%.1f %s'%(r,'反発あり' if bounce else '反発なし'),R,i,{}))
        break
  # 5 底つき(旧)・山頂
  for j in range(5,n-5):
    b=S[j]
    if b['l']==min(x['l'] for x in S[j-5:j+6]):
      body=abs(b['c']-b['o']);wick=min(b['o'],b['c'])-b['l']
      sign=wick>=max(body,tk) or (j>0 and b['l']<S[j-1]['l'] and b['c']>S[j-1]['l'])
      if sign:
        k=j+1;cnt=0
        while k<n and k<j+15:
          cnt=cnt+1 if S[k]['c']>S[k]['e9'] else 0
          if cnt>=3: break
          k+=1
        if cnt>=3:
          for i in range(k+1,n):
            if S[i]['c']<b['l']: lines.append(('底つき(旧) 反発→定着した底',b['l'],i,{}));break
    if b['h']==max(x['h'] for x in S[max(0,j-5):j+6]):
      lines.append(('山頂（実体の頂点）',max(b['o'],b['c']),j+5,{}))
  # 6 POC・高VAP帯 を割った
  for r,nm in ((None,'POC'),(2.0,'高VAP×2'),(3.0,'高VAP×3')):
    seen=set()
    for i in range(3,n):
      pr=pre[i];m=means[i]
      if not pr: continue
      if r is None: cands=[max(pr.items(),key=lambda kv:kv[1])[0]/10]
      else: cands=[k/10 for k,v in pr.items() if v>=r*m]
      for L in cands:
        if L in seen: continue
        if S[i-1]['c']>=L and S[i]['c']<L: seen.add(L);lines.append((nm,L,i,{}))
  # --- OS の評価 (各ライン: 1回目 / 2回目以降)
  def evaluate(typ,L,i_os,age,osno,c=None):
    pr=pre[i_os];m=means[i_os]
    if m<=0: return
    t=S[i_os]['tm']
    for rh,rc in RCOMBO:
      if rc>rh: continue
      ep=ep_of(pr,m,L,rh,rc,tk)
      if ep is None: continue          # 高VAP帯なし＝シグナルにしない
      e=None
      for j in range(i_os,min(n,i_os+3)):
        if S[j]['h']>ep: e=j;break
      pls=None
      if e is not None:
        pls=[];exs=[]
        for dd in (0,1,2):
          last=min(n-1,e+dd);ex=S[last]['c'];xb=last;stp=False
          for k in range(e,last+1):
            if S[k]['h']-ep>=CUT: ex=S[k]['c'];xb=k;stp=True;break
          pls.append((ep-ex)*100);exs.append((xb,stp))
        # 4つ目: H1までは必ず持ち、H1の終値がEPより下(含み益)ならH2まで、そうでなければH1の終値で決済 (損切りは同じ)
        h1=min(n-1,e+1)
        if exs[1][1] or not (S[h1]['c']<ep): pls.append(pls[1]);exs.append(exs[1])
        else: pls.append(pls[2]);exs.append(exs[2])
      for win in ('30本','60本','前場中'):
        if win=='30本' and age>30: continue
        if win=='60本' and age>60: continue
        key=(typ,osno,win,rh,rc,tb(t),'前半' if day['date']<='2026-09-25' else '後半')
        A=AGG[key];A[0]+=1
        if e is None: continue
        A[1]+=1
        for xi,p in enumerate(pls):
          A[2+xi*4]+= p>0; A[3+xi*4]+= p<0; A[4+xi*4]+=p; A[5+xi*4]+=p*p
      if rh==2.0 and rc==1.0 and e is not None:
        a0=max(0,min(c if c is not None else i_os,i_os)-12); a0=max(a0,i_os-30); a1=min(n,e+5)
        bars=[[S[q]['t'],round(S[q]['o'],1),round(S[q]['h'],1),round(S[q]['l'],1),round(S[q]['c'],1)] for q in range(a0,a1)]
        lv=[[k/10,round(v)] for k,v in pr.items() if L-15<=k/10<=L+20]
        SAMPLES[(typ,osno)].append(dict(d=day['date'],tk=day['tk'],t=S[i_os]['t'],L=round(L,1),ep=ep,et=S[e]['t'],p=[round(x) for x in pls],
          age=age,bars=bars,c=(c-a0) if c is not None and c>=a0 else None,os=i_os-a0,e=e-a0,x=[[xb-a0,stp] for xb,stp in exs],vp=lv,mean=round(m)))
  for typ,L,c,fl in lines:
    if c>=n: continue
    osno=0;i=c
    below=S[c]['c']<L or (c>0 and S[c-1]['c']<L) or c==0
    while i<n:
      if S[i]['h']>L and i>c-0:
        if i==c and not (c==0 and S[0]['o']<L): i+=1;continue
        osno+=1
        evaluate(typ,L,i,i-c,'1回目' if osno==1 else '2回目以降',c)
        # 次のOSは、終値で L の下へ戻ってから
        k=i+1
        while k<n and S[k]['c']>=L: k+=1
        i=k+1
        continue
      i+=1
  # 7 浮き足連続OS
  used=set()
  for i in range(5,n):
    b=S[i];pr=pre[i];m=means[i]
    if m<=0: continue
    win=S[max(0,i-15):i+1];lj=min(range(len(win)),key=lambda j:win[j]['l']);base=win[lj]['l']
    if lj>=len(win)-1: continue
    cand={'9EMA':b['e9'],'22EMA':b['e22'],'50EMA':b['e50'],'200EMA':b['e200'],'VWAP':b['vwap'],
          '寄り足実体高値':max(o['o'],o['c']),'寄り足実体安値':min(o['o'],o['c'])}
    if day.get('prevC'): cand['前日終値']=day['prevC']
    poc=max(pr.items(),key=lambda kv:kv[1])[0]/10 if pr else None
    if poc: cand['POC']=poc
    for k,v in pr.items():
      if v>=2*m: cand['高VAP%.1f'%(k/10)]=k/10
    R=round(b['c']/50)*50; cand['RN%d'%R]=R
    crossed={k:v for k,v in cand.items() if base<v<b['h']}
    if len(crossed)<2: continue
    topn=max(crossed,key=crossed.get);L=crossed[topn]
    if not(b['h']>L and S[i-1]['h']<=L): continue      # この足で最上部ラインを初めて超えた = OS1
    if (topn,round(L)) in used: continue
    used.add((topn,round(L)))
    below=[v for v in crossed.values() if v<L]
    pv=S[i-1]
    float_prev= all(pv['l']>v for v in below if v<pv['c'])
    seg=win[lj+1:i-max(0,i-15)]
    notouch=True
    for v in below:
      crossed_at=None
      for q,x in enumerate(seg):
        if crossed_at is None and x['c']>v: crossed_at=q;continue
        if crossed_at is not None and x['l']<=v: notouch=False;break
      if not notouch: break
    nl=len(crossed)
    for cond,okc in (('条件なし',True),('前足浮き',float_prev),('途中で足をつけない',notouch),('前足浮き＋途中で足をつけない',float_prev and notouch)):
      if okc: evaluate('浮き足連続OS %s 線%s本'%(cond,'2' if nl==2 else '3+'),L,i,0,'1回目',i-lj-0 if False else max(0,i-15)+lj)
json.dump({'agg':{json.dumps(k,ensure_ascii=False):v for k,v in AGG.items()},'samples':{json.dumps(k,ensure_ascii=False):sorted(v,key=lambda x:(x['d'],x['t']),reverse=True)[:40] for k,v in SAMPLES.items()},
  'nDays':len(days),'dates':[min(d['date'] for d in days),max(d['date'] for d in days)]},open(sys.argv[2],'w'),ensure_ascii=False)
print('keys',len(AGG),'days',len(days))
