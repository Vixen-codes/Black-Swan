/*
  Black Swan frontend
  --------------------
  GitHub Pages serves this static frontend.
  Your Render backend should expose POST /simulate.

  Expected request:
  {
    "assets": [{"ticker":"SPY","weight":0.6},{"ticker":"BND","weight":0.4}],
    "initial_value": 100000,
    "num_simulations": 10000,
    "horizon": 252,
    "seed": 42,
    "period": "5y",
    "confidence": 0.95
  }

  Expected response:
  {
    "version":"0.1.0",
    "seed":42,
    "assets":["SPY","BND"],
    "num_simulations":10000,
    "horizon":252,
    "initial_value":100000,
    "weights":{"SPY":0.6,"BND":0.4},
    "risk_metrics":{
      "var":1234.5,
      "expected_shortfall":1800.2,
      "mean_final_value":101000,
      "median_final_value":100500,
      "std_final_value":12000,
      "min_final_value":60000,
      "max_final_value":150000,
      "mean_return":0.01,
      "std_return":0.12,
      "skewness":0.1,
      "kurtosis":0.2,
      "percentiles":{"5":70000,"25":90000,"50":100500,"75":112000,"95":135000}
    },
    "final_values":[...]
  }

  If your Render URL is different, change API_BASE below.
*/

const API_BASE = "http://127.0.0.1:5000";

const $ = id => document.getElementById(id);
const money = value => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-GB",{style:"currency",currency:"GBP",maximumFractionDigits:0}).format(value)
  : "—";
const pct = value => Number.isFinite(Number(value)) ? `${(Number(value)*100).toFixed(2)}%` : "—";
const num = value => Number.isFinite(Number(value)) ? Number(value).toLocaleString("en-GB",{maximumFractionDigits:3}) : "—";

const assetRows = $("assetRows");
let assets = [
  {ticker:"SPY", weight:60},
  {ticker:"BND", weight:40}
];

function renderAssets(){
  assetRows.innerHTML = "";
  assets.forEach((asset,index)=>{
    const row = document.createElement("div");
    row.className = "asset-row";
    row.innerHTML = `
      <input aria-label="Ticker" value="${asset.ticker}" maxlength="10" data-index="${index}" data-field="ticker">
      <input aria-label="Weight percentage" type="number" min="0" max="100" step="1" value="${asset.weight}" data-index="${index}" data-field="weight">
      <button class="remove" aria-label="Remove asset" data-remove="${index}" ${assets.length<=2?"disabled":""}>×</button>
    `;
    assetRows.appendChild(row);
  });
  updateWeightStatus();
}

assetRows.addEventListener("input", e=>{
  const i = Number(e.target.dataset.index);
  if(!Number.isInteger(i)) return;
  const field = e.target.dataset.field;
  assets[i][field] = field==="weight" ? Number(e.target.value) : e.target.value.toUpperCase();
  if(field==="weight") updateWeightStatus();
});

assetRows.addEventListener("click", e=>{
  const i = e.target.dataset.remove;
  if(i !== undefined && assets.length>2){
    assets.splice(Number(i),1);
    renderAssets();
  }
});

$("addAsset").addEventListener("click",()=>{
  if(assets.length>=10) return;
  assets.push({ticker:"",weight:0});
  renderAssets();
});

function updateWeightStatus(){
  const total = assets.reduce((s,a)=>s+(Number(a.weight)||0),0);
  const box = $("validation");
  box.innerHTML = `Weights: <strong>${total.toFixed(1)}%</strong>`;
  box.classList.toggle("invalid",Math.abs(total-100)>0.001);
}

function setStatus(state,text){
  $("statusDot").className = `status-dot ${state||""}`;
  $("statusText").textContent = text;
}

function resetError(){ $("error").textContent=""; }

function setMetric(id,value){ $(id).textContent=value; }

function renderResults(data){
  const r = data.risk_metrics || data.risk || data.metrics || data;
  const initial = Number(data.initial_value ?? $("initialValue").value);

  setMetric("varValue", money(r.var));
  setMetric("esValue", money(r.expected_shortfall));
  setMetric("medianValue", money(r.median_final_value));
  setMetric("meanReturn", pct(r.mean_return));

  const p = r.percentiles || {};
  setMetric("p5",money(p["5"]));
  setMetric("p25",money(p["25"]));
  setMetric("p50",money(p["50"]));
  setMetric("p75",money(p["75"]));
  setMetric("p95",money(p["95"]));

  setMetric("stdValue",money(r.std_final_value));
  setMetric("minValue",money(r.min_final_value));
  setMetric("maxValue",money(r.max_final_value));
  setMetric("skewness",num(r.skewness));
  setMetric("kurtosis",num(r.kurtosis));

  $("runMeta").textContent =
    `${Number(data.num_simulations ?? $("simulations").value).toLocaleString()} RUNS · ` +
    `${data.horizon ?? $("horizon").value} PERIODS · SEED ${data.seed ?? $("seed").value}`;

  const values = data.final_values || data.simulation?.final_values;
  if(Array.isArray(values) && values.length) drawDistribution(values, Number(r.median_final_value), Number(initial - r.var));
}

function drawDistribution(values,median,varCutoff){
  const canvas=$("distributionChart"), wrap=canvas.parentElement;
  const rect=wrap.getBoundingClientRect();
  const dpr=window.devicePixelRatio||1;
  canvas.width=rect.width*dpr; canvas.height=rect.height*dpr;
  const ctx=canvas.getContext("2d"); ctx.scale(dpr,dpr);
  const w=rect.width,h=rect.height;
  ctx.clearRect(0,0,w,h);

  const sorted=[...values].sort((a,b)=>a-b);
  const min=sorted[0],max=sorted[sorted.length-1];
  const bins=44, counts=new Array(bins).fill(0);
  sorted.forEach(v=>{
    const i=Math.min(bins-1,Math.max(0,Math.floor((v-min)/(max-min||1)*bins)));
    counts[i]++;
  });
  const maxCount=Math.max(...counts);
  const left=48,right=18,top=15,bottom=35;
  const chartW=w-left-right, chartH=h-top-bottom;
  const barW=chartW/bins*.78;

  ctx.strokeStyle="#24272a"; ctx.lineWidth=1;
  [0,.5,1].forEach(t=>{
    const y=top+chartH*(1-t);
    ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(w-right,y);ctx.stroke();
  });

  ctx.fillStyle="#7f837c";
  counts.forEach((c,i)=>{
    const x=left+i*chartW/bins+(chartW/bins-barW)/2;
    const bh=c/maxCount*chartH;
    ctx.fillRect(x,top+chartH-bh,barW,bh);
  });

  const xFor=v=>left+(v-min)/(max-min||1)*chartW;
  [varCutoff,median].forEach((v,idx)=>{
    if(!Number.isFinite(v)) return;
    const x=Math.max(left,Math.min(w-right,xFor(v)));
    ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,top+chartH);
    ctx.strokeStyle=idx===0?"#73776f":"#d6d7d1";ctx.lineWidth=idx===0?1:2;ctx.stroke();
  });

  ctx.fillStyle="#676b65";ctx.font="9px DM Mono, monospace";
  ctx.textAlign="left";ctx.fillText(money(min),left,h-12);
  ctx.textAlign="right";ctx.fillText(money(max),w-right,h-12);
  ctx.textAlign="center";ctx.fillText("final portfolio value",w/2,h-12);
  $("chartEmpty").style.display="none";
}

async function runSimulation(){
  resetError();
  const total=assets.reduce((s,a)=>s+(Number(a.weight)||0),0);
  const clean=assets.map(a=>({ticker:a.ticker.trim().toUpperCase(),weight:Number(a.weight)/100}));
  if(clean.some(a=>!a.ticker)){ $("error").textContent="Every asset needs a ticker.";return; }
  if(Math.abs(total-100)>0.001){ $("error").textContent=`Weights must sum to 100%. Current total: ${total.toFixed(1)}%.`;return; }

  const button=$("runSimulation");
  button.disabled=true;
  button.querySelector("span").textContent="Running…";
  setStatus("busy","SIMULATION RUNNING");

  const payload={
    assets:clean,
    initial_value:Number($("initialValue").value),
    num_simulations:Number($("simulations").value),
    horizon:Number($("horizon").value),
    seed:Number($("seed").value),
    period:$("period").value,
    confidence:Number($("confidence").value)
  };

  try{
    const response=await fetch(`${API_BASE}/simulate`,{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)
    });
    const body=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(body.detail||body.error||`Backend returned HTTP ${response.status}`);
    renderResults(body);
    setStatus("","ENGINE READY");
  }catch(err){
    console.error(err);
    setStatus("error","ENGINE ERROR");
    $("error").textContent =
      `${err.message}. Check API_BASE and make sure your Render API allows CORS from GitHub Pages.`;
  }finally{
    button.disabled=false;
    button.querySelector("span").textContent="Run simulation";
  }
}

$("runSimulation").addEventListener("click",runSimulation);
window.addEventListener("resize",()=>{
  // Re-draw only if a chart is already populated.
  if($("chartEmpty").style.display==="none") $("chartEmpty").style.display="block";
});
renderAssets();
