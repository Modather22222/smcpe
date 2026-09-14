/* SMCPE dashboard app.js — active nav, translated waterfall, run table. Depends on data.js + payroll.js + i18n.js */
document.addEventListener('DOMContentLoaded',()=>{
  const page=document.body.dataset.page;
  document.querySelectorAll('.nav a').forEach(a=>{if(a.dataset.nav===page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  const seg=[...document.querySelectorAll('[data-cur]')];
  const host=document.getElementById('water');
  let active=seg[1]||seg[0]||null;
  function paint(){
    if(!host||!active)return;
    const lang=document.documentElement.lang==='ar'?'ar':'en';
    const d=(window.SMCPE_DASH_I18N||{})[lang]||{};
    const r=smcpeCompute(active.dataset.cur,+active.dataset.sal,+active.dataset.allow);
    host.innerHTML=smcpeWaterfallHTML([
      {label:(d.wl_gross||'Gross')+' · '+active.dataset.cur+' × '+r.rate,value:r.gross,color:'#1d4ed8'},
      {label:d.wl_nsif||'NSIF employee −8%',value:-r.nsifE,color:'#b45309'},
      {label:d.wl_tax||'Taxable base',value:r.taxable,color:'#0ea5e9'},
      {label:d.wl_pit||'PIT over 50k exempt',value:-r.pit,color:'#be123c'},
      {label:'<b>'+(d.wl_net||'Net pay SDG')+'</b>',value:r.net,color:'#047857'}
    ]);
  }
  window.SMCPE_rerenderWater=paint;
  function sel(b){active=b;seg.forEach(x=>x.setAttribute('aria-pressed',x===b?'true':'false'));paint();}
  seg.forEach(b=>b.addEventListener('click',()=>sel(b)));
  if(active){seg.forEach(x=>x.setAttribute('aria-pressed',x===active?'true':'false'));paint();}
  const rr=document.getElementById('runrows');
  if(rr&&window.SMCPE_RUN_ROWS)rr.innerHTML=SMCPE_RUN_ROWS.map(r=>'<tr><td class="mono">'+r[0]+'</td><td><span class="badge '+(r[1]==='SDG'?'':'b-fx')+'">'+r[1]+'</span></td>'+r.slice(2).map(smcpeFmt).map(n=>'<td class="num">'+n+'</td>').join('')+'</tr>').join('');
});
