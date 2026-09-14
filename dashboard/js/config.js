"use strict";
/* SMCPE config — single origin API via Nginx /api/ proxy, strict, no globals leak beyond SMCPE_* */
const SMCPE_API = "/api";
const SMCPE_TOKEN_KEY = "smcpe-jwt";

/** @returns {string|null} JWT or null */
function smcpeGetToken(){ try{ return localStorage.getItem(SMCPE_TOKEN_KEY); }catch(e){ return null; } }
function smcpeSetToken(t){ try{ localStorage.setItem(SMCPE_TOKEN_KEY, t); }catch(e){ /* quota */ } }
function smcpeClearToken(){ try{ localStorage.removeItem(SMCPE_TOKEN_KEY);}catch(e){} }

/** Check exp without verify (UI only); true if expired */
function smcpeIsExpired(token){
  try{
    const payload = JSON.parse(atob(token.split(".")[1]));
    if(!payload.exp) return false;
    return payload.exp * 1000 < Date.now();
  }catch(e){ return true; }
}

/**
 * Fetch with auth, 401 → login, preserves status in error.
 * @param {string} path - /api path e.g. "/employees"
 * @param {RequestInit} opts
 * @returns {Promise<Response>}
 */
async function smcpeFetch(path, opts={}){
  const token = smcpeGetToken();
  if(token && smcpeIsExpired(token)){
    smcpeClearToken();
    if(!location.pathname.endsWith("login.html")) location.href = "login.html";
    throw new Error("Token expired");
  }
  const headers = Object.assign({}, opts.headers||{});
  if(token) headers["Authorization"] = "Bearer " + token;
  if(!headers["Content-Type"] && !(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  let res;
  try{ res = await fetch(SMCPE_API + path, Object.assign({}, opts, {headers})); }
  catch(e){ console.error("smcpeFetch network", path, e); throw new Error("Network error: "+e.message); }
  if(res.status===401){
    smcpeClearToken();
    if(!location.pathname.endsWith("login.html")) location.href = "login.html";
    const body = await res.text().catch(()=> "");
    const err = new Error(body || "Unauthorized");
    err.status = 401;
    throw err;
  }
  return res;
}
async function smcpeFetchJSON(path, opts={}){
  const res = await smcpeFetch(path, opts);
  if(!res.ok){
    const body = await res.text().catch(()=> res.statusText);
    const err = new Error(body);
    err.status = res.status;
    throw err;
  }
  const ct = res.headers.get("content-type")||"";
  if(ct.includes("application/json")) return res.json();
  return res.text();
}
