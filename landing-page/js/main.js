/* SMCPE landing main.js — lang toggle (Arabic-first default), nav, waterfall demo, counters. No deps. */
(function(){
  const root=document.documentElement;
  const btn=document.getElementById('langToggle');
  function getLang(){
    const s=localStorage.getItem('smcpe-lang');
    if(s) return s;
    try{if((navigator.language||'').toLowerCase().startsWith('ar'))return 'ar';}catch(e){}
    return 'ar'; // actual users are Arabic-first
  }
  let current='ar';
  function applyLang(l){
    current=l;
    const dict=SMCPE_I18N[l]||SMCPE_I18N.en;
    document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.getAttribute('data-i18n');if(dict[k]!=null)el.innerHTML=dict[k];});
    document.querySelectorAll('[data-i18n-ph]').forEach(el=>{const k=el.getAttribute('data-i18n-ph');if(dict[k]!=null)el.setAttribute('placeholder',dict[k]);});
    root.lang=l; root.dir=(l==='ar')?'rtl':'ltr';
    try{localStorage.setItem('smcpe-lang',l);}catch(e){}
    if(btn)btn.textContent=(l==='ar')?'EN':'عربي';
    rerender();
  }
  if(btn)btn.addEventListener('click',()=>applyLang(current==='ar'?'en':'ar'));
  const menu=document.getElementById('menuBtn'), links=document.getElementById('navLinks');
  if(menu&&links)menu.addEventListener('click',()=>links.classList.toggle('open'));
  const FX={SDG:1,USD:2610.50,SAR:696.10};
  const fmt=n=>n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  let activeBtn=null;
  function render(cur,sal,allow){
    const host=document.getElementById('water'); if(!host)return;
    const dict=SMCPE_I18N[current]||SMCPE_I18N.en;
    const gross=(sal+allow)*FX[cur];
    const nsif=Math.round(gross*0.08*100)/100;
    const tax=Math.max(0,gross-nsif);
    const pit=tax<=50000?0:Math.round((tax-50000)*0.15*100)/100;
    const net=Math.round((gross-nsif-pit)*100)/100;
    const row=(l,v,c)=>'<div class="w-row"><span>'+l+'</span><div class="bar"><i style="width:'+Math.max(3,Math.abs(v)/gross*100)+'%;background:'+c+'"></i></div><span class="w-val">'+(v<0?'−':'')+fmt(Math.abs(v))+'</span></div>';
    host.innerHTML=row(dict.wl_gross+' · '+cur+' × '+FX[cur],gross,'#38bdf8')+row(dict.wl_nsif,-nsif,'#f59e0b')+row(dict.wl_pit,-pit,'#fb7185')+row('<b>'+dict.wl_net+'</b>',net,'#34d399');
  }
  function rerender(){if(activeBtn)render(activeBtn.dataset.cur,+activeBtn.dataset.sal,+activeBtn.dataset.allow);}
  const seg=[...document.querySelectorAll('.seg button')];
  function sel(b){activeBtn=b;seg.forEach(x=>x.setAttribute('aria-pressed',x===b?'true':'false'));render(b.dataset.cur,+b.dataset.sal,+b.dataset.allow);}
  seg.forEach(b=>b.addEventListener('click',()=>sel(b)));
  if(seg[1])activeBtn=seg[1];else if(seg[0])activeBtn=seg[0];
  applyLang(getLang());
  const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const el=e.target;io.unobserve(el);
    const t=+el.dataset.count,to=performance.now(),d=1500;
    (function tick(now){const p=Math.min(1,(now-to)/d),v=Math.round(t*(1-Math.pow(1-p,3)));el.textContent=v.toLocaleString('en-US');if(p<1)requestAnimationFrame(tick)})(to);}),{threshold:.4});
  document.querySelectorAll('[data-count]').forEach(el=>io.observe(el));
})();
