const c=require('./snload.js');const fs=require('fs');
const D=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let data=D.sn;
try{ const m=c.migrateData(JSON.parse(JSON.stringify(data))); if(m&&m.charts)data=m; }catch(e){console.error('migrate',e.message);}
const recs=c._elCollectAllSignals(data);
console.error('recs',recs.length, Object.keys(recs[0]).join(','));
const out=[];
recs.forEach(r=>{
  const s=r.signal; if(!s)return;
  let ai=null; try{ai=c._elAlphaInfo(r,data);}catch(e){}
  const alpha=ai?ai.alpha:null, cut=ai?ai.cutLine:null;
  let res=null,xs=null,fp=null; try{res=c._epResolve(s,alpha);}catch(e){} try{xs=c._epIsXSkip(s,alpha);}catch(e){}
  try{fp=c._elHoldFinalParts(s,alpha,cut);}catch(e){}
  out.push({key:r.chartKey||r.key||null,stock:r.stock||r.stockName||null,date:r.date,id:s.id,tag:s.tag,time:s.time,level:s.levelPrice!=null&&s.levelPrice!==''?Number(s.levelPrice):null,
    alpha,cut,v2:c._epIsV2(s),incl:c._elInclData(s),thru:s.passThrough===true,prov:!!c._elIsProvisional(s),
    judge:res?res.judge:null,epIdx:res?res.epIdx:null,xskip:!!xs,pnl:(fp&&fp.main!=null&&res&&res.judge==='ok'&&!xs)?fp.main:null,
    skip:s.skipReasons||null,thruR:s.thruReasons||null,review:s.review===true,revR:s.reviewReasons||null,
    det:s.sigDetail||null,osVal:s.osVal,minBar:s.minBar,specialUsed:!!s.specialUsed,spR:s.specialReasons||null,rnUsed:!!s.rnUsed,ceOn:s.ceOn===true,
    lineCoexist:!!s.lineCoexist,entered:s.entered===true,vap:c._vapOf(s),vapAdj:c._vapAdjOf(s)});
});
fs.writeFileSync(process.argv[3],JSON.stringify(out));
const C={};out.forEach(o=>{const k=[o.v2,o.incl,o.judge].join('/');C[k]=(C[k]||0)+1;});console.error(C);
const ok=out.filter(o=>o.v2&&o.incl&&o.pnl!=null);console.error('pnl n',ok.length,'sum',ok.reduce((a,o)=>a+o.pnl,0),'win',ok.filter(o=>o.pnl>0).length);
