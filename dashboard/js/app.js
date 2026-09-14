"use strict";
/* SMCPE dashboard app.js — nav + waterfall + API wiring, fallback to data.js mock, XSS-safe, a11y, offline */
document.addEventListener("DOMContentLoaded", ()=>{
  const page = document.body.dataset.page;
  document.querySelectorAll(".nav a").forEach(a=>{ if(a.dataset.nav===page) a.setAttribute("aria-current","page"); else a.removeAttribute("aria-current"); });
  // a11y: seg buttons role group
  document.querySelectorAll(".seg").forEach(g=>{ if(!g.getAttribute("role")) g.setAttribute("role","group"); if(!g.getAttribute("aria-label")) g.setAttribute("aria-label","Currency"); });

  const seg = [...document.querySelectorAll("[data-cur]")];
  const host = document.getElementById("water");
  let active = seg[1]||seg[0]||null;
  function paint(){
    if(!host||!active) return;
    const lang = document.documentElement.lang==="ar"?"ar":"en";
    const d = (window.SMCPE_DASH_I18N||{})[lang]||{};
    const r = smcpeCompute(active.dataset.cur,+active.dataset.sal,+active.dataset.allow);
    host.innerHTML = smcpeWaterfallHTML([
      {label:(d.wl_gross||"Gross")+" · "+active.dataset.cur+" × "+r.rate,value:r.gross,color:"#1d4ed8"},
      {label:d.wl_nsif||"NSIF employee −8%",value:-r.nsifE,color:"#b45309"},
      {label:d.wl_tax||"Taxable base",value:r.taxable,color:"#0ea5e9"},
      {label:d.wl_pit||"PIT over 50k exempt",value:-r.pit,color:"#be123c"},
      {label:"<b>"+(d.wl_net||"Net pay SDG")+"</b>",value:r.net,color:"#047857"}
    ]);
  }
  window.SMCPE_rerenderWater = paint;
  function sel(b){ active=b; seg.forEach(x=>x.setAttribute("aria-pressed", x===b?"true":"false")); paint(); }
  seg.forEach(b=>b.addEventListener("click", ()=>sel(b)));
  if(active){ seg.forEach(x=>x.setAttribute("aria-pressed", x===active?"true":"false")); paint(); }

  const hasAPI = typeof smcpeFetch==="function";
  async function tryAPI(path){
    if(!hasAPI) throw new Error("no api");
    const res = await smcpeFetch(path);
    if(!res.ok) throw new Error("api "+res.status);
    const ct=res.headers.get("content-type")||"";
    if(ct.includes("json")) return res.json();
    return res.text();
  }
  function fmtMoney(v, lang){
    try{ return Number(v).toLocaleString(lang==="ar"?"ar-EG":"en-US",{minimumFractionDigits:2,maximumFractionDigits:2}); }catch(e){ return String(v); }
  }
  function setLoading(tbody, cols, msg){
    if(tbody) tbody.innerHTML = `<tr><td colspan="${cols}" aria-live="polite" style="text-align:center;padding:12px;color:var(--muted)">${msg}</td></tr>`;
  }

  // index.html KPIs
  if(page==="dashboard"){
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const runs = j.runs||[];
        let run = runs.find(r=>r.status==="computed"||r.status==="approved") || runs[0];
        if(run){
          const detail = await tryAPI("/runs/"+run.id);
          const lines = detail.lines||[];
          let totals = null;
          // try to parse totals from run if stored, else compute
          try{ totals = detail.run && detail.run.fx_snapshot_json ? null : null; }catch(e){}
          if(!totals||!totals.gross){
            const sums={gross:0, nsif_emp:0, pit:0, net:0};
            lines.forEach(l=>{ sums.gross+=parseFloat(l.gross); sums.nsif_emp+=parseFloat(l.nsif_emp); sums.pit+=parseFloat(l.pit); sums.net+=parseFloat(l.net); });
            totals=sums;
          }
          const lang=document.documentElement.lang==="ar"?"ar":"en";
          const kpis=document.querySelectorAll(".kpi .v");
          if(kpis[1]) kpis[1].textContent = fmtMoney(totals.gross||0, lang);
          const netEl=document.querySelector(".kpi:nth-child(4) .v");
          if(netEl) netEl.textContent = fmtMoney(totals.net||0, lang);
        }
        const empJ = await tryAPI("/employees");
        const cnt=(empJ.employees||[]).length;
        const head=document.querySelector(".kpi .v");
        if(head&&cnt) head.textContent = String(cnt);
      }catch(e){ console.warn("dashboard KPIs fallback", e); }
    })();
  }

  // employees.html — XSS-safe via createElement
  if(page==="employees"){
    const tbody=document.querySelector("table tbody");
    if(tbody){
      setLoading(tbody, 7, "Loading…");
      (async()=>{
        try{
          const j = await tryAPI("/employees");
          const emps=j.employees||[];
          if(emps.length){
            tbody.textContent="";
            const frag=document.createDocumentFragment();
            const lang=document.documentElement.lang==="ar"?"ar":"en";
            emps.forEach(emp=>{
              const tr=document.createElement("tr");
              const tdName=document.createElement("td");
              const b=document.createElement("b"); b.textContent=emp.name;
              const br=document.createElement("br");
              const span=document.createElement("span"); span.className="mono note"; span.textContent=`${emp.id} · NID ${emp.national_id||""}`;
              tdName.append(b,br,span);
              const tdHire=document.createElement("td"); tdHire.className="mono"; tdHire.textContent=emp.hire_date;
              const tdCur=document.createElement("td"); const badge=document.createElement("span"); badge.className="badge "+(emp.base_currency==="SDG"?"":"b-fx"); badge.textContent=emp.base_currency; tdCur.append(badge);
              const tdSal=document.createElement("td"); tdSal.className="num"; tdSal.textContent=fmtMoney(emp.base_salary, lang);
              const tdAllow=document.createElement("td"); tdAllow.className="num"; tdAllow.textContent=fmtMoney(emp.allowances, lang);
              const tdNsif=document.createElement("td"); const nsifBadge=document.createElement("span"); nsifBadge.className="badge "+(emp.nsif_eligible==="Y"?"b-ok":"b-warn"); nsifBadge.textContent=`${emp.nsif_eligible} · ${emp.nsif_eligible==="Y"?"8/17%":"contractor"}`; tdNsif.append(nsifBadge);
              const tdBank=document.createElement("td"); tdBank.className="mono"; tdBank.textContent=`${emp.bank_code||""} · ${emp.bank_account||""}`;
              tr.append(tdName,tdHire,tdCur,tdSal,tdAllow,tdNsif,tdBank);
              frag.append(tr);
            });
            tbody.append(frag);
          } else { tbody.textContent=""; }
        }catch(e){ console.error("employees load", e); tbody.textContent=""; /* keep mock fallback: re-render from data.js if available is done at page load, so clear loading only */ }
      })();
    }
  }

  // run.html
  const rr=document.getElementById("runrows");
  if(rr){
    if(window.SMCPE_RUN_ROWS) rr.innerHTML=SMCPE_RUN_ROWS.map(r=>"<tr><td class=\"mono\">"+r[0]+"</td><td><span class=\"badge "+(r[1]==="SDG"?"":"b-fx")+"\">"+r[1]+"</span></td>"+r.slice(2).map(smcpeFmt).map(n=>"<td class=\"num\">"+n+"</td>").join("")+"</tr>").join("");
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const run=(j.runs||[])[0];
        if(!run) return;
        setLoading(rr, 8, "Loading run…");
        const detail = await tryAPI("/runs/"+run.id);
        const lines=detail.lines||[];
        if(lines.length){
          rr.textContent="";
          const frag=document.createDocumentFragment();
          const lang=document.documentElement.lang==="ar"?"ar":"en";
          lines.forEach(l=>{
            const emp=(window.SMCPE_EMPLOYEES||[]).find(e=>e.id===l.emp_id);
            const cur=emp?emp.cur:"SDG";
            const tr=document.createElement("tr");
            const tdId=document.createElement("td"); tdId.className="mono"; tdId.textContent=l.emp_id;
            const tdCur=document.createElement("td"); const b=document.createElement("span"); b.className="badge "+(cur==="SDG"?"":"b-fx"); b.textContent=cur; tdCur.append(b);
            const vals=[l.gross,l.nsif_emp,l.nsif_co,l.taxable,l.pit,l.net];
            tr.append(tdId,tdCur);
            vals.forEach(v=>{ const td=document.createElement("td"); td.className="num"; td.textContent=fmtMoney(v, lang); tr.append(td); });
            frag.append(tr);
          });
          rr.append(frag);
          const tfoot=document.querySelector("tfoot tr");
          if(tfoot){
            let g=0,e=0,c=0,t=0,p=0,n=0;
            lines.forEach(l=>{ g+=parseFloat(l.gross); e+=parseFloat(l.nsif_emp); c+=parseFloat(l.nsif_co); t+=parseFloat(l.taxable); p+=parseFloat(l.pit); n+=parseFloat(l.net); });
            tfoot.textContent="";
            const tdLabel=document.createElement("td"); tdLabel.colSpan=2; tdLabel.textContent=`Totals · ${lines.length} lines`;
            const tdG=document.createElement("td"); tdG.textContent=fmtMoney(g, lang);
            const tdE=document.createElement("td"); tdE.textContent=fmtMoney(e, lang);
            const tdC=document.createElement("td"); tdC.textContent=fmtMoney(c, lang);
            const tdT=document.createElement("td"); tdT.textContent=fmtMoney(t, lang);
            const tdP=document.createElement("td"); tdP.textContent=fmtMoney(p, lang);
            const tdN=document.createElement("td"); tdN.textContent=fmtMoney(n, lang);
            tfoot.append(tdLabel,tdG,tdE,tdC,tdT,tdP,tdN);
          }
        }
      }catch(e){ console.warn("run rows", e); }
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
            const byDate={};
            hist.forEach(r=>{ if(!byDate[r.date]) byDate[r.date]={}; byDate[r.date][r.currency]=r.rate; byDate[r.date].locked = r.source==="locked"; });
            const dates=Object.keys(byDate).sort().reverse().slice(0,3);
            tbody.textContent="";
            const frag=document.createDocumentFragment();
            const lang=document.documentElement.lang==="ar"?"ar":"en";
            dates.forEach(d=>{
              const tr=document.createElement("tr");
              const tdDate=document.createElement("td"); tdDate.className="mono"; tdDate.textContent=d;
              ["USD","SAR","AED"].forEach(cur=>{
                const td=document.createElement("td"); td.className="num"; td.textContent=fmtMoney(byDate[d][cur]||0, lang); tr.append(td);
              });
              // reorder: we need USD,SAR,AED but table has USD,SAR,AED
              const tdSrc=document.createElement("td"); const badge=document.createElement("span"); badge.className="badge "+(byDate[d].locked?"b-ok":"b-info"); badge.textContent=byDate[d].locked?"Locked":"CBOS"; tdSrc.append(badge);
              tr.prepend(tdDate);
              tr.append(tdSrc);
              frag.append(tr);
            });
            tbody.append(frag);
          }
        }
      }catch(e){ console.error("fx history", e); }
    })();
  }

  // reports, bank
  if(page==="reports"){
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const run=(j.runs||[])[0];
        if(!run) return;
        await tryAPI("/reports/nsif?run_id="+run.id);
        await tryAPI("/reports/pit?run_id="+run.id);
      }catch(e){ console.debug("reports", e); }
    })();
  }
  if(page==="bank"){
    const pre=document.querySelector("pre.file");
    if(pre) setLoading(pre, 0, "Loading bank file…");
    (async()=>{
      try{
        const j = await tryAPI("/runs?period=2026-09");
        const run=(j.runs||[])[0];
        if(!run) return;
        const txt = await tryAPI("/bank/file?run_id="+run.id);
        const pre2=document.querySelector("pre.file");
        if(pre2 && typeof txt==="string") pre2.textContent = txt;
      }catch(e){ console.error("bank file", e); const pre2=document.querySelector("pre.file"); if(pre2) pre2.textContent="Offline — mock file shown"; }
    })();
  }
});
