/*
  Black Swan frontend
  --------------------
  Talks to a Flask backend exposing POST /simulate.
  See README / backend source for the exact request and response shape.
*/

const API_BASE = "http://127.0.0.1:5000";

const $ = id => document.getElementById(id);
const money = value => Number.isFinite(Number(value))
  ? new Intl.NumberFormat("en-GB",{style:"currency",currency:"GBP",maximumFractionDigits:0}).format(value)
  : "—";
const pct = value => Number.isFinite(Number(value)) ? `${(Number(value)*100).toFixed(2)}%` : "—";
const num = value => Number.isFinite(Number(value)) ? Number(value).toLocaleString("en-GB",{maximumFractionDigits:3}) : "—";

/* ------------------------------------------------------------------ */
/* Ticker directory — used for the search dropdown only. The backend  */
/* will accept any ticker Yahoo Finance recognises, listed or not.    */
/* ------------------------------------------------------------------ */
const TICKERS = [
  {t:"AAPL",n:"Apple"},{t:"MSFT",n:"Microsoft"},{t:"GOOGL",n:"Alphabet (Class A)"},
  {t:"AMZN",n:"Amazon"},{t:"NVDA",n:"NVIDIA"},{t:"META",n:"Meta Platforms"},
  {t:"TSLA",n:"Tesla"},{t:"BRK-B",n:"Berkshire Hathaway"},{t:"JPM",n:"JPMorgan Chase"},
  {t:"V",n:"Visa"},{t:"MA",n:"Mastercard"},{t:"UNH",n:"UnitedHealth Group"},
  {t:"HD",n:"Home Depot"},{t:"PG",n:"Procter & Gamble"},{t:"XOM",n:"ExxonMobil"},
  {t:"CVX",n:"Chevron"},{t:"KO",n:"Coca-Cola"},{t:"PEP",n:"PepsiCo"},
  {t:"COST",n:"Costco"},{t:"WMT",n:"Walmart"},{t:"MCD",n:"McDonald's"},
  {t:"DIS",n:"Walt Disney"},{t:"NFLX",n:"Netflix"},{t:"ADBE",n:"Adobe"},
  {t:"CRM",n:"Salesforce"},{t:"ORCL",n:"Oracle"},{t:"INTC",n:"Intel"},
  {t:"AMD",n:"Advanced Micro Devices"},{t:"IBM",n:"IBM"},{t:"CSCO",n:"Cisco Systems"},
  {t:"QCOM",n:"Qualcomm"},{t:"TXN",n:"Texas Instruments"},{t:"AVGO",n:"Broadcom"},
  {t:"PYPL",n:"PayPal"},{t:"UBER",n:"Uber Technologies"},{t:"ABNB",n:"Airbnb"},
  {t:"SBUX",n:"Starbucks"},{t:"NKE",n:"Nike"},{t:"BA",n:"Boeing"},
  {t:"LMT",n:"Lockheed Martin"},{t:"RTX",n:"RTX Corporation (Raytheon)"},{t:"NOC",n:"Northrop Grumman"},
  {t:"GD",n:"General Dynamics"},{t:"GE",n:"General Electric"},{t:"CAT",n:"Caterpillar"},
  {t:"DE",n:"Deere & Company"},{t:"HON",n:"Honeywell"},{t:"MMM",n:"3M"},
  {t:"UPS",n:"United Parcel Service"},{t:"FDX",n:"FedEx"},{t:"F",n:"Ford Motor"},
  {t:"GM",n:"General Motors"},{t:"T",n:"AT&T"},{t:"VZ",n:"Verizon"},
  {t:"PFE",n:"Pfizer"},{t:"JNJ",n:"Johnson & Johnson"},{t:"MRK",n:"Merck"},
  {t:"ABBV",n:"AbbVie"},{t:"LLY",n:"Eli Lilly"},{t:"BMY",n:"Bristol Myers Squibb"},
  {t:"GS",n:"Goldman Sachs"},{t:"MS",n:"Morgan Stanley"},{t:"BAC",n:"Bank of America"},
  {t:"WFC",n:"Wells Fargo"},{t:"C",n:"Citigroup"},{t:"BLK",n:"BlackRock"},
  {t:"SCHW",n:"Charles Schwab"},{t:"AXP",n:"American Express"},{t:"SPGI",n:"S&P Global"},
  {t:"COIN",n:"Coinbase Global"},{t:"SQ",n:"Block (Square)"},{t:"SHOP",n:"Shopify"},
  {t:"PLTR",n:"Palantir Technologies"},{t:"SNOW",n:"Snowflake"},{t:"NOW",n:"ServiceNow"},
  {t:"INTU",n:"Intuit"},{t:"ADP",n:"Automatic Data Processing"},{t:"BKNG",n:"Booking Holdings"},
  {t:"MAR",n:"Marriott International"},{t:"LOW",n:"Lowe's"},{t:"TGT",n:"Target"},
  {t:"TJX",n:"TJX Companies"},{t:"CMCSA",n:"Comcast"},{t:"TMUS",n:"T-Mobile US"},
  {t:"NEE",n:"NextEra Energy"},{t:"DUK",n:"Duke Energy"},{t:"SO",n:"Southern Company"},
  {t:"LIN",n:"Linde"},{t:"APD",n:"Air Products & Chemicals"},{t:"NEM",n:"Newmont"},
  {t:"FCX",n:"Freeport-McMoRan"},{t:"BA.L",n:"BAE Systems (London)"},{t:"SHEL",n:"Shell"},
  {t:"BP",n:"BP"},{t:"AZN",n:"AstraZeneca"},{t:"GSK",n:"GSK"},
  {t:"HSBC",n:"HSBC Holdings"},{t:"ULVR.L",n:"Unilever (London)"},{t:"DGE.L",n:"Diageo (London)"},
  {t:"RIO",n:"Rio Tinto"},{t:"BHP",n:"BHP Group"},{t:"TSM",n:"Taiwan Semiconductor"},
  {t:"BABA",n:"Alibaba Group"},{t:"SONY",n:"Sony Group"},{t:"TM",n:"Toyota Motor"},
  {t:"NVO",n:"Novo Nordisk"},{t:"SAP",n:"SAP"},{t:"ASML",n:"ASML Holding"},
  {t:"SPY",n:"SPDR S&P 500 ETF"},{t:"VOO",n:"Vanguard S&P 500 ETF"},{t:"IVV",n:"iShares Core S&P 500 ETF"},
  {t:"VTI",n:"Vanguard Total Stock Market ETF"},{t:"QQQ",n:"Invesco QQQ (Nasdaq 100)"},{t:"DIA",n:"SPDR Dow Jones Industrial Average ETF"},
  {t:"IWM",n:"iShares Russell 2000 ETF"},{t:"VEA",n:"Vanguard FTSE Developed Markets ETF"},{t:"VWO",n:"Vanguard FTSE Emerging Markets ETF"},
  {t:"EFA",n:"iShares MSCI EAFE ETF"},{t:"BND",n:"Vanguard Total Bond Market ETF"},{t:"AGG",n:"iShares Core US Aggregate Bond ETF"},
  {t:"TLT",n:"iShares 20+ Year Treasury Bond ETF"},{t:"SHY",n:"iShares 1-3 Year Treasury Bond ETF"},{t:"LQD",n:"iShares Investment Grade Corporate Bond ETF"},
  {t:"HYG",n:"iShares High Yield Corporate Bond ETF"},{t:"GLD",n:"SPDR Gold Shares"},{t:"SLV",n:"iShares Silver Trust"},
  {t:"USO",n:"United States Oil Fund"},{t:"VNQ",n:"Vanguard Real Estate ETF"},{t:"XLE",n:"Energy Select Sector SPDR"},
  {t:"XLF",n:"Financial Select Sector SPDR"},{t:"XLK",n:"Technology Select Sector SPDR"},{t:"XLV",n:"Health Care Select Sector SPDR"},
  {t:"XLY",n:"Consumer Discretionary Select Sector SPDR"},{t:"XLI",n:"Industrial Select Sector SPDR"},{t:"ARKK",n:"ARK Innovation ETF"},
  {t:"VIG",n:"Vanguard Dividend Appreciation ETF"},{t:"SCHD",n:"Schwab US Dividend Equity ETF"},{t:"VYM",n:"Vanguard High Dividend Yield ETF"},
  {t:"^GSPC",n:"S&P 500 Index"},{t:"^DJI",n:"Dow Jones Industrial Average"},{t:"^IXIC",n:"Nasdaq Composite"},
  {t:"^FTSE",n:"FTSE 100 Index"},{t:"BTC-USD",n:"Bitcoin"},{t:"ETH-USD",n:"Ethereum"}
];

/* ------------------------------------------------------------------ */
/* Portfolio state                                                    */
/* ------------------------------------------------------------------ */
const assetRows = $("assetRows");
let assets = [
  {ticker:"SPY", weight:60},
  {ticker:"BND", weight:40}
];
let openMenuIndex = null;

function matchTickers(query){
  const q = query.trim().toUpperCase();
  if(!q) return TICKERS.slice(0,8);
  const starts = TICKERS.filter(x=>x.t.toUpperCase().startsWith(q));
  const contains = TICKERS.filter(x=>!x.t.toUpperCase().startsWith(q) &&
    (x.t.toUpperCase().includes(q) || x.n.toUpperCase().includes(q)));
  return [...starts, ...contains].slice(0,8);
}

function renderAssets(){
  assetRows.innerHTML = "";
  assets.forEach((asset,index)=>{
    const row = document.createElement("div");
    row.className = "asset-row";
    row.innerHTML = `
      <div class="ticker-field">
        <input aria-label="Ticker" autocomplete="off" value="${asset.ticker}" maxlength="12" data-index="${index}" data-field="ticker" placeholder="Search ticker or name">
        <div class="ticker-menu" data-menu="${index}"></div>
      </div>
      <input aria-label="Weight percentage" type="number" min="0" max="100" step="1" value="${asset.weight}" data-index="${index}" data-field="weight">
      <button class="remove" aria-label="Remove holding" data-remove="${index}" ${assets.length<=2?"disabled":""}>×</button>
    `;
    assetRows.appendChild(row);
  });
  updateWeightStatus();
}

function renderMenu(index){
  const menu = assetRows.querySelector(`.ticker-menu[data-menu="${index}"]`);
  if(!menu) return;
  const input = assetRows.querySelector(`input[data-index="${index}"][data-field="ticker"]`);
  const results = matchTickers(input.value);
  if(!results.length){
    menu.innerHTML = `<div class="ticker-empty">No match — you can still type any ticker directly.</div>`;
  } else {
    menu.innerHTML = results.map(r=>
      `<div class="ticker-option" data-pick="${r.t}" data-index="${index}"><span>${r.t}</span><span>${r.n}</span></div>`
    ).join("");
  }
  menu.classList.add("open");
  openMenuIndex = index;
}

function closeMenus(){
  assetRows.querySelectorAll(".ticker-menu").forEach(m=>m.classList.remove("open"));
  openMenuIndex = null;
}

assetRows.addEventListener("focusin", e=>{
  if(e.target.dataset.field === "ticker"){
    renderMenu(Number(e.target.dataset.index));
  }
});

assetRows.addEventListener("input", e=>{
  const i = Number(e.target.dataset.index);
  if(!Number.isInteger(i)) return;
  const field = e.target.dataset.field;
  assets[i][field] = field==="weight" ? Number(e.target.value) : e.target.value.toUpperCase();
  if(field==="weight") updateWeightStatus();
  if(field==="ticker") renderMenu(i);
});

assetRows.addEventListener("click", e=>{
  const pick = e.target.closest("[data-pick]");
  if(pick){
    const i = Number(pick.dataset.index);
    assets[i].ticker = pick.dataset.pick;
    renderAssets();
    return;
  }
  const removeIdx = e.target.dataset.remove;
  if(removeIdx !== undefined && assets.length>2){
    assets.splice(Number(removeIdx),1);
    renderAssets();
    return;
  }
});

document.addEventListener("click", e=>{
  if(openMenuIndex !== null && !e.target.closest(".ticker-field")){
    closeMenus();
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
  box.innerHTML = `weights total <strong>${total.toFixed(1)}%</strong>`;
  box.classList.toggle("invalid",Math.abs(total-100)>0.001);
}

function setStatus(state,text){
  $("statusDot").className = `status-dot ${state||""}`;
  $("statusLine").lastChild.textContent = text;
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
    `${Number(data.num_simulations ?? $("simulations").value).toLocaleString()} paths · ` +
    `${data.horizon ?? $("horizon").value} days · seed ${data.seed ?? $("seed").value}`;

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
  const bins=48, counts=new Array(bins).fill(0);
  sorted.forEach(v=>{
    const i=Math.min(bins-1,Math.max(0,Math.floor((v-min)/(max-min||1)*bins)));
    counts[i]++;
  });
  const maxCount=Math.max(...counts);
  const left=52,right=16,top=16,bottom=32;
  const chartW=w-left-right, chartH=h-top-bottom;
  const barW=chartW/bins*.76;

  ctx.strokeStyle="#D6D3C2"; ctx.lineWidth=1;
  [0,.5,1].forEach(t=>{
    const y=top+chartH*(1-t);
    ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(w-right,y);ctx.stroke();
  });

  ctx.fillStyle="#585B4E";
  counts.forEach((c,i)=>{
    const x=left+i*chartW/bins+(chartW/bins-barW)/2;
    const bh=c/maxCount*chartH;
    ctx.fillRect(x,top+chartH-bh,barW,bh);
  });

  const xFor=v=>left+(v-min)/(max-min||1)*chartW;
  if(Number.isFinite(varCutoff)){
    const x=Math.max(left,Math.min(w-right,xFor(varCutoff)));
    ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,top+chartH);
    ctx.strokeStyle="#9C3A2C";ctx.lineWidth=1.4;ctx.stroke();
  }
  if(Number.isFinite(median)){
    const x=Math.max(left,Math.min(w-right,xFor(median)));
    ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,top+chartH);
    ctx.strokeStyle="#181A15";ctx.lineWidth=1.8;ctx.stroke();
  }

  ctx.fillStyle="#8A8C7C";ctx.font="10px IBM Plex Mono, monospace";
  ctx.textAlign="left";ctx.fillText(money(min),left,h-10);
  ctx.textAlign="right";ctx.fillText(money(max),w-right,h-10);
  $("chartEmpty").style.display="none";
}

async function runSimulation(){
  resetError();
  closeMenus();
  const total=assets.reduce((s,a)=>s+(Number(a.weight)||0),0);
  const clean=assets.map(a=>({ticker:a.ticker.trim().toUpperCase(),weight:Number(a.weight)/100}));
  if(clean.some(a=>!a.ticker)){ $("error").textContent="Every holding needs a ticker.";return; }
  if(Math.abs(total-100)>0.001){ $("error").textContent=`Weights must total 100%. Current total: ${total.toFixed(1)}%.`;return; }

  const button=$("runSimulation");
  button.disabled=true;
  button.textContent="Running…";
  setStatus("busy","simulation running");

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
    setStatus("","engine ready");
  }catch(err){
    console.error(err);
    setStatus("error","engine error");
    $("error").textContent =
      `${err.message}. Check API_BASE and make sure your backend allows requests from this page.`;
  }finally{
    button.disabled=false;
    button.textContent="Run simulation";
  }
}

$("runSimulation").addEventListener("click",runSimulation);
window.addEventListener("resize",()=>{
  if($("chartEmpty").style.display==="none") $("chartEmpty").style.display="block";
});

renderAssets();