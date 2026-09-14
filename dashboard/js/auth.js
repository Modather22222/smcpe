"use strict";
/* SMCPE auth guard — protect dashboard pages, handle viewer role, no silent catch */
(function(){
  const publicPages = ["login.html"];
  const path = location.pathname.split("/").pop() || "index.html";
  if(publicPages.includes(path)) return;
  let token = null;
  try{ token = localStorage.getItem("smcpe-jwt"); }catch(e){ token = null; }
  if(!token){
    location.href = "login.html";
    return;
  }
  // UI-only decode, check exp
  let role = "viewer";
  try{
    const payload = JSON.parse(atob(token.split(".")[1]));
    if(payload.exp && payload.exp * 1000 < Date.now()){
      try{ localStorage.removeItem("smcpe-jwt"); }catch(e){}
      location.href = "login.html";
      return;
    }
    role = payload.role || "viewer";
    document.addEventListener("DOMContentLoaded", ()=>{
      if(role==="viewer"){
        document.querySelectorAll("[data-requires='owner'],[data-requires='accountant']").forEach(el=>{ el.style.display="none"; });
        document.querySelectorAll(".btn-primary[data-requires]").forEach(el=>{ el.disabled=true; el.title="Viewer: payslips only"; el.setAttribute("aria-disabled","true"); });
      }
      const badge = document.getElementById("roleBadge");
      if(badge) badge.textContent = role;
    });
  }catch(e){ console.warn("auth decode failed", e); }
  // verify token is still valid via /api/employees ping
  fetch("/api/employees", {headers:{Authorization:"Bearer "+token}}).then(r=>{
    if(r.status===401){
      try{ localStorage.removeItem("smcpe-jwt"); }catch(e){}
      location.href="login.html";
    }
  }).catch(err=>{ console.error("auth verify failed", err); });
  window.SMCPE_logout = function(){
    try{ localStorage.removeItem("smcpe-jwt"); }catch(e){}
    location.href="login.html";
  };
})();
