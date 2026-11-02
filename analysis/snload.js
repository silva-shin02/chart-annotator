// SN 本体 (app-01..07,09) を vm に読み込み、計算関数を使えるようにする
const vm=require('vm'),fs=require('fs');
const dir=process.env.SN_DIR||'/home/user/silva-shin02/scalping-notebook/';
function stub(){ const f=function(){return f;}; return new Proxy(f,{get:(t,k)=>k===Symbol.toPrimitive?(()=>''):(k==='prototype'?{}:stub()),apply:()=>stub(),construct:()=>stub()}); }
const store={};
const ctx={console,Math,JSON,Date,Object,Array,Number,String,Boolean,RegExp,Error,Map,Set,WeakMap,Promise,parseInt,parseFloat,isNaN,isFinite,Symbol,Proxy,Reflect,Intl,
  setTimeout:()=>0,clearTimeout:()=>0,setInterval:()=>0,clearInterval:()=>0,requestAnimationFrame:()=>0,
  localStorage:{getItem:k=>store[k]??null,setItem:(k,v)=>{store[k]=String(v)},removeItem:k=>{delete store[k]},key:()=>null,length:0},
  navigator:{userAgent:'node',onLine:true},location:{href:'file:///x',search:'',hash:'',protocol:'file:'},
  fetch:()=>new Promise(()=>{}),indexedDB:stub(),firebase:stub(),
  document:stub(),React:stub(),ReactDOM:stub(),Blob:function(){},URL:stub(),FileReader:function(){},Image:function(){},
  addEventListener:()=>{},removeEventListener:()=>{},matchMedia:()=>({matches:false,addListener(){}})};
ctx.window=ctx; ctx.self=ctx; ctx.globalThis=ctx;
vm.createContext(ctx);
for(const f of ['app-01.js','app-02.js','app-03.js','app-04.js','app-05.js','app-06.js','app-09.js','app-07.js']){
  try{ vm.runInContext(fs.readFileSync(dir+f,'utf8'),ctx,{filename:f}); }catch(e){ console.error('load',f,e.message); }
}
module.exports=ctx;
