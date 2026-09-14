/* SMCPE payroll math — mirrors payroll_calc.cob (simplified 15% demo tier). Pure functions, no DOM. */
function smcpeFmt(n){return Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});}
function smcpeCompute(cur,sal,allow,fx){
  const rate=(fx||SMCPE_FX)[cur]||1;
  const gross=(sal+allow)*rate;
  const nsifE=Math.round(gross*0.08*100)/100;
  const taxable=Math.max(0,gross-nsifE);
  const pit=taxable<=50000?0:Math.round((taxable-50000)*0.15*100)/100;
  const net=Math.round((gross-nsifE-pit)*100)/100;
  return {rate,gross,nsifE,taxable,pit,net};
}
function smcpeWaterfallHTML(parts){
  // parts: [{label, value, color}]
  const max=Math.max(...parts.map(p=>Math.abs(p.value)),1);
  return parts.map(p=>'<div class="w-row"><span>'+p.label+'</span><div class="bar"><i style="width:'+Math.max(2,Math.abs(p.value)/max*100)+'%;background:'+p.color+'"></i></div><span class="w-val">'+(p.value<0?'−':'')+smcpeFmt(Math.abs(p.value))+'</span></div>').join('');
}
