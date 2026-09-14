/* SMCPE config — single origin API via Nginx /api/ proxy */
const SMCPE_API = "/api";
const SMCPE_TOKEN_KEY = "smcpe-jwt";

function smcpeGetToken(){ try{ return localStorage.getItem(SMCPE_TOKEN_KEY); }catch(e){ return null; } }
function smcpeSetToken(t){ try{ localStorage.setItem(SMCPE_TOKEN_KEY, t); }catch(e){} }
function smcpeClearToken(){ try{ localStorage.removeItem(SMCPE_TOKEN_KEY);}catch(e){} }

async function smcpeFetch(path, opts={}){
  const token = smcpeGetToken();
  const headers = Object.assign({}, opts.headers||{});
  if(token) headers["Authorization"] = "Bearer " + token;
  if(!headers["Content-Type"] && !(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(SMCPE_API + path, Object.assign({}, opts, {headers}));
  if(res.status===401){
    // redirect to login unless already there
    if(!location.pathname.endsWith("login.html")){
      smcpeClearToken();
      location.href = "login.html";
    }
    throw new Error("Unauthorized");
  }
  return res;
}
async function smcpeFetchJSON(path, opts={}){
  const res = await smcpeFetch(path, opts);
  if(!res.ok) throw new Error(await res.text());
  const ct = res.headers.get("content-type")||"";
  if(ct.includes("application/json")) return res.json();
  return res.text();
}
