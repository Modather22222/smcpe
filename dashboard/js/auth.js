/* SMCPE auth guard — protect dashboard pages, handle viewer role */
(function(){
  const publicPages = ["login.html"];
  const path = location.pathname.split("/").pop() || "index.html";
  if(publicPages.includes(path)) return;
  const token = (function(){ try{ return localStorage.getItem("smcpe-jwt"); }catch(e){ return null; } })();
  if(!token){
    location.href = "login.html";
    return;
  }
  // decode JWT payload without verification (for UI only)
  try{
    const payload = JSON.parse(atob(token.split(".")[1]));
    const role = payload.role || "viewer";
    document.addEventListener("DOMContentLoaded", ()=>{
      if(role==="viewer"){
        document.querySelectorAll("[data-requires='owner'],[data-requires='accountant']").forEach(el=>el.style.display="none");
        document.querySelectorAll(".btn-primary[data-requires]").forEach(el=>{ el.disabled=true; el.title="Viewer: payslips only"; });
      }
      // show role badge if exists
      const badge = document.getElementById("roleBadge");
      if(badge) badge.textContent = role;
    });
  }catch(e){}
  // verify token is still valid via /api/employees ping (silent)
  fetch("/api/employees", {headers:{Authorization:"Bearer "+token}}).then(r=>{
    if(r.status===401){
      try{ localStorage.removeItem("smcpe-jwt"); }catch(e){}
      location.href="login.html";
    }
  }).catch(()=>{});
  window.SMCPE_logout = function(){
    try{ localStorage.removeItem("smcpe-jwt"); }catch(e){}
    location.href="login.html";
  };
})();
