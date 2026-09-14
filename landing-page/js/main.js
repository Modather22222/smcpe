"use strict";
/* SMCPE landing main.js — lang toggle, nav a11y, waterfall, counters, API badge */
(function(){
  const root=document.documentElement;
  const btn=document.getElementById('langToggle');
  function getLang(){
    const s=localStorage.getItem('smcpe-lang');
    if(s==="ar"||s==="en") return s;
    try{ if((navigator.language||'').toLowerCase().startsWith('ar')) return 'ar'; }catch(e){}
    return 'ar';
  }
  let current='ar';
  function applyLang(l){
    current=l;
    const dict=SMCPE_I18N[l]||SMCPE_I18N.en;
    // Use textContent for plain, allow <b> via safe replace (only <b> and </b>)
    document.querySelectorAll('[data-i18n]').forEach(el=>{
      const k=el.getAttribute('data-i18n'); const v=dict[k];
      if(v==null) return;
      if(v.includes("<b>")){
        // allow only <b> tags — sanitize by escaping then re-allowing <b>
        const esc = v.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
        const safe = esc.replace(/&lt;b&gt;/g,"<b>").replace(/&lt;\/b&gt;/g,"</b>");
        el.innerHTML = safe;
      } else { el.textContent = v; }
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el=>{const k=el.getAttribute('data-i18n-ph');if(dict[k]!=null)el.setAttribute('placeholder',dict[k]);});
    root.lang=l; root.dir=(l==='ar')?'rtl':'ltr';
    try{localStorage.setItem('smcpe-lang',l);}catch(e){}
    if(btn) btn.textContent=(l==='ar')?'EN':'عربي';
    rerender();
  }
  if(btn) btn.addEventListener('click',()=>applyLang(current==='ar'?'en':'ar'));
  const menu=document.getElementById('menuBtn'), links=document.getElementById('navLinks');
  if(menu&&links){
    menu.setAttribute('aria-expanded','false');
    menu.setAttribute('aria-controls','navLinks');
    menu.addEventListener('click',()=>{
      const open=links.classList.toggle('open');
      menu.setAttribute('aria-expanded', open?'true':'false');
    });
  }
  const FX={SDG:1,USD:2610.50,SAR:696.10};
  const fmt=n=>{
    try{ return n.toLocaleString(current==="ar"?"ar-EG":"en-US",{minimumFractionDigits:2,maximumFractionDigits:2}); }catch(e){ return n.toFixed(2); }
  };
  let activeBtn=null;
  function render(cur,sal,allow){
    const host=document.getElementById('water'); if(!host) return;
    const dict=SMCPE_I18N[current]||SMCPE_I18N.en;
    const gross=(sal+allow)*FX[cur];
    const nsif=Math.round(gross*0.08*100)/100;
    const tax=Math.max(0,gross-nsif);
    const pit=tax<=50000?0:Math.round((tax-50000)*0.15*100)/100;
    const net=Math.round((gross-nsif-pit)*100)/100;
    // Use DOM, not innerHTML concat for values (XSS-safe)
    host.textContent="";
    const frag=document.createDocumentFragment();
    function addRow(label, value, color, bold){
      const row=document.createElement("div"); row.className="w-row";
      const spanL=document.createElement("span");
      if(bold){ const b=document.createElement("b"); b.textContent=label; spanL.append(b); } else { spanL.textContent=label; }
      const bar=document.createElement("div"); bar.className="bar";
      const i=document.createElement("i"); i.style.width=Math.max(3,Math.abs(value)/gross*100)+"%"; i.style.background=color;
      bar.append(i);
      const spanV=document.createElement("span"); spanV.className="w-val"; spanV.textContent=(value<0?"−":"")+fmt(Math.abs(value));
      row.append(spanL,bar,spanV);
      frag.append(row);
    }
    addRow(dict.wl_gross+" · "+cur+" × "+FX[cur],gross,"#38bdf8",false);
    addRow(dict.wl_nsif,-nsif,"#f59e0b",false);
    addRow(dict.wl_pit,-pit,"#fb7185",false);
    addRow(dict.wl_net,net,"#34d399",true);
    host.append(frag);
  }
  function rerender(){ if(activeBtn) render(activeBtn.dataset.cur,+activeBtn.dataset.sal,+activeBtn.dataset.allow); }
  const seg=[...document.querySelectorAll('.seg button')];
  function sel(b){ activeBtn=b; seg.forEach(x=>x.setAttribute('aria-pressed',x===b?"true":"false")); render(b.dataset.cur,+b.dataset.sal,+b.dataset.allow); }
  seg.forEach(b=>b.addEventListener('click',()=>sel(b)));
  if(seg[1]) activeBtn=seg[1]; else if(seg[0]) activeBtn=seg[0];
  applyLang(getLang());
  // API health badge
  fetch("/api/health").then(r=>{ if(!r.ok) throw new Error(r.status); return r.json(); }).then(j=>{
    const el=document.querySelector(".trust-row");
    if(el && j.ok){
      const b=document.createElement("span");
      b.className="mono";
      b.style.cssText="background:#ecfdf5;border:1px solid #047857;color:#047857;padding:2px 6px;border-radius:999px;font-size:11px";
      b.textContent="API "+(j.version||"v2026.09")+" ● libpayroll.so ✓";
      b.setAttribute("role","status");
      el.append(b);
    }
  }).catch(err=>{ console.debug("health", err); });
  // Respect prefers-reduced-motion for counters
  const prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const io=new IntersectionObserver(es=>es.forEach(e=>{
    if(!e.isIntersecting) return;
    const el=e.target; io.unobserve(el);
    const t=+el.dataset.count;
    if(prefersReduced){ el.textContent=t.toLocaleString(current==="ar"?"ar-EG":"en-US"); return; }
    const to=performance.now(),d=1500;
    (function tick(now){const p=Math.min(1,(now-to)/d),v=Math.round(t*(1-Math.pow(1-p,3)));el.textContent=v.toLocaleString(current==="ar"?"ar-EG":"en-US");if(p<1)requestAnimationFrame(tick)})(to);
  }),{threshold:.4});
  document.querySelectorAll('[data-count]').forEach(el=>io.observe(el));
})();
