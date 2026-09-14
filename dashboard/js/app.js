/* SMCPE dashboard app.js — nav + waterfall + API wiring (fallback to data.js mock if offline) */
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

  // API wiring — fallback to mock if no token or fetch fails
  const hasAPI = typeof smcpeFetch==="function";
  // helper to use mock if API fails
  async function tryAPI(path){
    if(!hasAPI) throw new Error("no api");
    const res = await smcpeFetch(path);
    if(!res.ok) throw new Error("api "+res.status);
    const ct=res.headers.get("content-type")||"";
    if(ct.includes("json")) return res.json();
    return res.text();
  }

  // index.html KPIs
  if(page==="dashboard"){
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const runs = j.runs||[];
        // find latest computed run
        let run = runs.find(r=>r.status==="computed"||r.status==="approved") || runs[0];
        if(run){
          const detail = await tryAPI("/runs/"+run.id);
          const lines = detail.lines||[];
          // compute totals from lines if not in run
          let totals = detail.run && detail.run.totals ? JSON.parse(detail.run.totals||"{}") : null;
          if(!totals || !totals.gross){
            // compute from lines
            const sums={gross:0, nsif_emp:0, pit:0, net:0};
            lines.forEach(l=>{ sums.gross+=parseFloat(l.gross); sums.nsif_emp+=parseFloat(l.nsif_emp); sums.pit+=parseFloat(l.pit); sums.net+=parseFloat(l.net); });
            totals=sums;
          }
          // update KPIs if elements exist (class kpi)
          const kpis = document.querySelectorAll(".kpi .v");
          if(kpis[1]) kpis[1].textContent = Number(totals.gross||0).toLocaleString('en-US',{minimumFractionDigits:2});
          // nsif 25% approximated as emp+co
          // net
          const netEl = document.querySelector(".kpi:nth-child(4) .v");
          if(netEl) netEl.textContent = Number(totals.net||0).toLocaleString('en-US',{minimumFractionDigits:2});
        }
        // update headcount from employees
        const empJ = await tryAPI("/employees");
        const cnt = (empJ.employees||[]).length;
        const head = document.querySelector(".kpi .v");
        if(head && cnt) head.textContent = cnt;
      }catch(e){ /* fallback to mock KPIs */ }
    })();
  }

  // employees.html
  if(page==="employees"){
    const tbody=document.querySelector("table tbody");
    if(tbody){
      (async()=>{
        try{
          const j = await tryAPI("/employees");
          const emps=j.employees||[];
          if(emps.length){
            tbody.innerHTML = emps.map(emp=>`<tr><td><b>${emp.name}</b><br><span class="mono note">${emp.id} · NID ${emp.national_id||""}</span></td><td class="mono">${emp.hire_date}</td><td><span class="badge ${emp.base_currency==="SDG"?"":"b-fx"}">${emp.base_currency}</span></td><td class="num">${Number(emp.base_salary).toLocaleString('en-US',{minimumFractionDigits:2})}</td><td class="num">${Number(emp.allowances).toLocaleString('en-US',{minimumFractionDigits:2})}</td><td><span class="badge ${emp.nsif_eligible==="Y"?"b-ok":"b-warn"}">${emp.nsif_eligible} · ${emp.nsif_eligible==="Y"?"8/17%":"contractor"}</span></td><td class="mono">${emp.bank_code||""} · ${emp.bank_account||""}</td></tr>`).join('');
          }
        }catch(e){ /* mock remains */ }
      })();
    }
  }

  // run.html
  const rr=document.getElementById('runrows');
  if(rr){
    if(window.SMCPE_RUN_ROWS) rr.innerHTML=SMCPE_RUN_ROWS.map(r=>'<tr><td class="mono">'+r[0]+'</td><td><span class="badge '+(r[1]==='SDG'?'':'b-fx')+'">'+r[1]+'</span></td>'+r.slice(2).map(smcpeFmt).map(n=>'<td class="num">'+n+'</td>').join('')+'</tr>').join('');
    // try API override
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const run = (j.runs||[])[0];
        if(!run) return;
        const detail = await tryAPI("/runs/"+run.id);
        const lines = detail.lines||[];
        if(lines.length){
          rr.innerHTML = lines.map(l=>{
            const emp = (window.SMCPE_EMPLOYEES||[]).find(e=>e.id===l.emp_id);
            const cur = emp ? emp.cur : "SDG";
            return `<tr><td class="mono">${l.emp_id}</td><td><span class="badge ${cur==="SDG"?"":"b-fx"}">${cur}</span></td><td class="num">${smcpeFmt(l.gross)}</td><td class="num">${smcpeFmt(l.nsif_emp)}</td><td class="num">${smcpeFmt(l.nsif_co)}</td><td class="num">${smcpeFmt(l.taxable)}</td><td class="num">${smcpeFmt(l.pit)}</td><td class="num">${smcpeFmt(l.net)}</td></tr>`;
          }).join('');
          // update tfoot totals if exists
          const tfoot = document.querySelector("tfoot tr");
          if(tfoot && detail.run){
            // compute totals
            let g=0,e=0,c=0,t=0,p=0,n=0;
            lines.forEach(l=>{ g+=parseFloat(l.gross); e+=parseFloat(l.nsif_emp); c+=parseFloat(l.nsif_co); t+=parseFloat(l.taxable); p+=parseFloat(l.pit); n+=parseFloat(l.net); });
            tfoot.innerHTML = `<td colspan="2">Totals · ${lines.length} lines</td><td>${smcpeFmt(g)}</td><td>${smcpeFmt(e)}</td><td>${smcpeFmt(c)}</td><td>${smcpeFmt(t)}</td><td>${smcpeFmt(p)}</td><td>${smcpeFmt(n)}</td>`;
          }
        }
      }catch(e){}
    })();
  }

  // fx.html
  if(page==="fx"){
    (async()=>{
      try{
        const j = await tryAPI("/fx/history");
        const hist=j.history||[];
        if(hist.length){
          const tbody=document.querySelector("table tbody");
          if(tbody){
            // group by date
            const byDate={};
            hist.forEach(r=>{ if(!byDate[r.date]) byDate[r.date]={}; byDate[r.date][r.currency]=r.rate; });
            const dates=Object.keys(byDate).sort().reverse().slice(0,3);
            tbody.innerHTML = dates.map(d=>`<tr><td class="mono">${d}</td><td class="num">${Number(byDate[d].USD||0).toLocaleString('en-US',{minimumFractionDigits:2})}</td><td class="num">${Number(byDate[d].SAR||0).toLocaleString('en-US',{minimumFractionDigits:2})}</td><td class="num">${Number(byDate[d].AED||0).toLocaleString('en-US',{minimumFractionDigits:2})}</td><td><span class="badge ${byDate[d].locked?"b-ok":"b-info"}">${byDate[d].locked?"Locked":"CBOS"}</span></td></tr>`).join('');
          }
        }
      }catch(e){}
    })();
  }

  // reports.html, bank.html etc fallback to mock but could fetch
  if(page==="reports"){
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const run=(j.runs||[])[0];
        if(!run) return;
        const nsif = await tryAPI("/reports/nsif?run_id="+run.id);
        const pit = await tryAPI("/reports/pit?run_id="+run.id);
        // could update tables, but keep mock for now
      }catch(e){}
    })();
  }
  if(page==="bank"){
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const run=(j.runs||[])[0];
        if(!run) return;
        const txt = await tryAPI("/bank/file?run_id="+run.id);
        const pre=document.querySelector("pre.file");
        if(pre && typeof txt==="string") pre.textContent = txt;
      }catch(e){}
    })();
  }
});
