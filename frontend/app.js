/* Jal Setu — groundwater dashboard driven by the Groundwater Forecast API.
   Levels are depth below ground in metres: a bigger number means the water is deeper (worse). */

const API = (window.API_BASE || "/api/v1").replace(/\/$/, "");
const HORIZONS = [7, 14, 30];

const st = {
  stations: [], model: null,
  cur: 0, days: 30, usage: "medium",
  status: {},   // `${id}|${days}` -> status
  detail: {},   // `${kind}|${id}|${days}` -> response
};

const byId = id => document.getElementById(id);
const S = () => st.stations[st.cur];
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = (v, d = 2) => v == null || Number.isNaN(+v) ? "—" : (+v).toFixed(d);
const signed = (v, d = 2) => v == null ? "—" : (v > 0 ? "+" : "") + (+v).toFixed(d);
const fmtDate = d => d ? new Date(d + "T00:00:00").toLocaleDateString(undefined, {day:"numeric", month:"short", year:"numeric"}) : "—";

const RISK = {
  SAFE:     {word:"Safe",     cls:"SAFE",     al:"safe",  ic:"✅", color:"#2e9e6b", bg:"var(--safe-bg)"},
  WATCH:    {word:"Watch",    cls:"WATCH",    al:"watch", ic:"⚠️", color:"#d79a16", bg:"var(--watch-bg)"},
  CRITICAL: {word:"Critical", cls:"CRITICAL", al:"crit",  ic:"🛑", color:"#d8503c", bg:"var(--crit-bg)"},
  UNKNOWN:  {word:"Unknown",  cls:"UNKNOWN",  al:"unk",   ic:"❓", color:"#7d8b92", bg:"var(--unk-bg)"},
};
const TREND = {
  declining:  {word:"Falling over the last 2 weeks", short:"declining",  ic:"↓", color:"#d8503c"},
  stable:     {word:"Steady over the last 2 weeks",           short:"steady",     ic:"→", color:"#5b7079"},
  improving:  {word:"Rising over the last 2 weeks",               short:"recovering", ic:"↑", color:"#2e9e6b"},
  unknown:    {word:"Trend unknown",            short:"unknown",    ic:"?", color:"#7d8b92"},
};
const risk = s => RISK[s?.risk] || RISK.UNKNOWN;
const trend = s => TREND[s?.trend] || TREND.unknown;

/* ---------- API ---------- */
// Static mode (GitHub Pages): export_static.py saved each API response as a JSON file under data/.
const SNAPSHOT = window.STATIC_SNAPSHOT || null;
function snapshotFile(path, opts) {
  const [p, q] = path.split("?");
  if (p === "/whatif") {
    const b = JSON.parse(opts.body);
    return `data/whatif/${b.station_id}-${b.usage}-${b.days}.json`;
  }
  const days = new URLSearchParams(q || "").get("days");
  return `data${p}${days ? "-" + days : ""}.json`;
}

async function api(path, opts) {
  const r = SNAPSHOT ? await fetch(snapshotFile(path, opts)) : await fetch(API + path, opts);
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try { const j = await r.json(); if (j.detail) msg += ` — ${typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail)}`; } catch {}
    throw new Error(msg);
  }
  return r.json();
}
async function cached(store, key, fn) {
  if (!(key in store)) store[key] = fn().catch(e => { delete store[key]; throw e; });
  return store[key];
}
const sid = s => encodeURIComponent(s.id);
const getStatus = (s, days = st.days) => cached(st.status, `${s.id}|${days}`, () => api(`/stations/${sid(s)}/status?days=${days}`));
const getForecast = s => cached(st.detail, `fc|${s.id}|${st.days}`, () => api(`/stations/${sid(s)}/forecast?days=${st.days}`));
const getRecharge = s => cached(st.detail, `rc|${s.id}`, () => api(`/stations/${sid(s)}/recharge`));
const getAnomalies = s => cached(st.detail, `an|${s.id}`, () => api(`/stations/${sid(s)}/anomalies`));
const getWhatif = s => cached(st.detail, `wi|${s.id}|${st.days}|${st.usage}`, () => api(`/whatif`, {
  method:"POST", headers:{"Content-Type":"application/json"},
  body: JSON.stringify({station_id: s.id, usage: st.usage, days: Math.min(st.days, 30)}),
}));

/* settled statuses for the current horizon (null while loading / on error) */
const statusNow = s => st.statusVal?.[`${s.id}|${st.days}`] ?? null;
st.statusVal = {};
async function loadStatuses() {
  await Promise.all(st.stations.map(async s => {
    try { st.statusVal[`${s.id}|${st.days}`] = await getStatus(s); }
    catch (e) { st.statusVal[`${s.id}|${st.days}`] = {station_id:s.id, risk:"UNKNOWN", trend:"unknown", days:st.days,
      advice:"Could not load this well's status.", alerts:[`Status request failed: ${e.message}`], _err:true}; }
  }));
}

const errBox = e => `<div class="banner warn">Could not load this section: ${esc(e.message)}</div>`;

/* ---------- region / list views (all stations) ---------- */
function regionHtml() {
  const counts = {SAFE:0, WATCH:0, CRITICAL:0, UNKNOWN:0};
  st.stations.forEach(s => counts[risk(statusNow(s)).cls]++);
  const known = counts.CRITICAL ? "CRITICAL" : counts.WATCH ? "WATCH" : counts.SAFE ? "SAFE" : "UNKNOWN";
  const o = RISK[known];
  const box = k => `<div class="count" style="background:${RISK[k].bg};color:${RISK[k].color}">
      <div class="n">${counts[k]}</div><div class="k">${RISK[k].ic} ${RISK[k].word}</div></div>`;
  const districts = [...new Set(st.stations.map(s => s.district).filter(Boolean))].join(", ");
  return `<div style="min-width:180px">
      <div class="small muted">Overall · next ${st.days} days</div>
      <span class="badge b-${o.cls}" style="margin-top:6px;font-size:16px">${o.ic} ${o.word}</span>
      <div class="small muted" style="margin-top:8px">${st.stations.length} monitored wells${districts ? " · " + esc(districts) : ""}</div>
    </div>${box("SAFE")}${box("WATCH")}${box("CRITICAL")}${counts.UNKNOWN ? box("UNKNOWN") : ""}`;
}

function sidebar() {
  return st.stations.map((s, i) => {
    const a = statusNow(s), r = risk(a), t = trend(a);
    return `<button class="item ${i === st.cur ? "sel" : ""}" onclick="pick(${i})">
      <span><div class="nm">${esc(s.name)}</div><div class="lv">${num(a?.level ?? s.level)} m · ${t.ic} ${t.short}</div></span>
      <span class="dot" style="background:${r.color}" title="${r.word}"></span></button>`;
  }).join("");
}

function wellRows() {
  return st.stations.map((s, i) => {
    const a = statusNow(s), r = risk(a);
    return `<tr class="${i === st.cur ? "sel" : ""}" onclick="pick(${i})"><td><b>${esc(s.name)}</b></td>
      <td><span class="badge b-${r.cls}" style="font-size:12px;padding:4px 10px">${r.word}</span></td>
      <td class="num">${num(a?.level ?? s.level)} m</td><td class="num">${signed(a?.change_m)} m</td></tr>`;
  }).join("");
}

function mapPins() {
  const pts = st.stations.filter(s => s.lat != null && s.lon != null);
  if (!pts.length) return `<p class="muted" style="padding:20px">No coordinates available.</p>`;
  const lats = pts.map(p => p.lat), lons = pts.map(p => p.lon);
  const [minLa, maxLa, minLo, maxLo] = [Math.min(...lats), Math.max(...lats), Math.min(...lons), Math.max(...lons)];
  return st.stations.map((s, i) => {
    if (s.lat == null) return "";
    const left = 12 + ((s.lon - minLo) / ((maxLo - minLo) || 1)) * 76;   // %
    const top  = 12 + ((maxLa - s.lat) / ((maxLa - minLa) || 1)) * 76;   // % (north up)
    return `<button class="pin ${i === st.cur ? "sel" : ""}" style="left:${left}%;top:${top}%" onclick="pick(${i})"
        title="${esc(s.name)} (${num(s.lat, 3)}, ${num(s.lon, 3)})">
       <div class="pd" style="background:${risk(statusNow(s)).color}"></div>
       <div class="lbl">${esc(s.name)}</div></button>`;
  }).join("");
}

function alertsHtml() {
  const order = {crit:0, watch:1, unk:2};
  const items = st.stations.map((s, i) => {
    const a = statusNow(s); if (!a) return null;
    const r = risk(a), extra = (a.alerts || []).map(esc).join(" ");
    if (a.risk === "CRITICAL") return {i, c:"crit", ic:r.ic, t:`${esc(s.name)}: Sharp groundwater decline expected`,
      d:`Water table ~${num(a.level)} m deep, expected to go ~${num(a.change_m)} m deeper in ${a.days} days. Reduce extraction. ${extra}`};
    if (a.risk === "WATCH") return {i, c:"watch", ic:r.ic, t:`${esc(s.name)}: Groundwater expected to fall`,
      d:`Expected ~${num(a.change_m)} m deeper in ${a.days} days. Use water carefully this season. ${extra}`};
    if (a.risk === "UNKNOWN") return {i, c:"unk", ic:r.ic, t:`${esc(s.name)}: Status unavailable`,
      d: extra || "The service could not assign a reliable risk for this well."};
    if (a.trend === "declining") return {i, c:"watch", ic:"↓", t:`${esc(s.name)}: Level declining recently`,
      d:`Readings over the last two weeks are going down, though the ${a.days}-day forecast is still safe. ${extra}`};
    return null;
  }).filter(Boolean).sort((x, y) => order[x.c] - order[y.c]);
  return items.length ? items.map(x => `
    <button class="alert ${x.c}" onclick="pick(${x.i},'overview')"><div class="ic">${x.ic}</div>
      <div><div class="t">${x.t}</div><div class="d">${x.d}</div></div></button>`).join("")
    : `<div class="alert safe"><div class="ic">✅</div><div><div class="t">No active alerts</div>
        <div class="d">Groundwater is stable across monitored wells for the next ${st.days} days.</div></div></div>`;
}

/* ---------- per-station views ---------- */
function plainCondition(a) {
  if (!a) return "";
  const lvl = `<b>${num(a.level)} m</b>`, ch = num(Math.abs(a.change_m ?? 0)), d = a.days;
  if (a.risk === "UNKNOWN")
    return `We can't give a reliable status for this well right now.
      ${(a.alerts || []).length ? esc(a.alerts.join(" ")) : ""}
      ${a.as_of ? `The last reading (${fmtDate(a.as_of)}) showed the water table at ${lvl} below ground.` : ""}
      Please don't treat this as "safe".`;
  if (a.risk === "SAFE")
    return `${a.change_m > 0 ? "No serious concern for now." : "Water levels in your area are stable."} The borewell water table is about ${lvl} below ground
      and is ${a.change_m > 0 ? `only expected to drop about <b>${ch} m</b>` : `expected to stay the same or rise slightly`}
      over the next ${d} days.`;
  if (a.risk === "WATCH")
    return `The water table (about ${lvl} deep) is expected to go down — roughly <b>${ch} m deeper over the next ${d} days</b>.
      It is not an emergency yet, but it needs care.`;
  return `The water table is at ${lvl} and is expected to drop sharply — about <b>${ch} m deeper in just ${d} days</b>.
    Action is needed to avoid the borewell running low.`;
}

function heroHtml(s, a) {
  const r = risk(a), t = trend(a);
  const age = a?.data_age_days == null ? "" : a.data_age_days === 0 ? "today" : `${a.data_age_days} day${a.data_age_days === 1 ? "" : "s"} ago`;
  return `<h3>${(a?.data_age_days ?? 0) > 7 ? "Latest reading" : "Groundwater today"} · ${esc(s.name)} <span style="text-transform:none;letter-spacing:0">(${esc(s.id)})</span></h3>
    <div class="hero">
      <div class="main">
        <div class="big">${num(a?.level)}<span class="unit"> m deep</span></div>
        <div class="trendline" style="color:${t.color}">${t.ic} ${t.word}</div>
        <span class="badge b-${r.cls}" style="margin-top:10px">${r.ic} ${r.word}</span>
      </div>
      <div class="tile"><div class="k">Forecast in ${st.days} days</div><div class="v">${num(a?.forecast_level)} m</div></div>
      <div class="tile"><div class="k">Expected change</div><div class="v" style="color:${(a?.change_m ?? 0) > 0 ? "var(--crit)" : "var(--safe)"}">${signed(a?.change_m)} m</div>
        <div class="s">+ means deeper (worse)</div></div>
      <div class="tile"><div class="k">Last reading</div><div class="v" style="font-size:18px">${fmtDate(a?.as_of)}</div>
        <div class="s">${age}</div></div>
    </div>`;
}

function chartHtml(s, fc) {
  const obs = fc.observed.map(p => ({d:p.date, v:p.level}));
  const pred = fc.forecast.map(p => ({d:p.date, v:p.level}));
  const all = obs.concat(pred);
  if (all.length < 2) return `<h3>Water depth · ${esc(s.name)}</h3><p class="muted">Not enough data to draw a chart.</p>`;
  const W = 900, H = 320, padL = 56, padR = 16, padT = 16, padB = 36;
  const vals = all.map(a => a.v);
  let min = Math.min(...vals), max = Math.max(...vals);
  const span = (max - min) || 1; min -= span * 0.12; max += span * 0.12;
  // deeper (bigger depth) = LOWER on screen -> line falls when water drops
  const x = i => padL + i * (W - padL - padR) / (all.length - 1);
  const y = v => padT + ((v - min) / (max - min)) * (H - padT - padB);
  const path = pts => pts.map((p, k) => (k ? "L" : "M") + x(p.i).toFixed(1) + " " + y(p.v).toFixed(1)).join(" ");
  const oi = obs.map((p, i) => ({...p, i}));
  const fi = pred.map((p, i) => ({...p, i: obs.length + i}));
  const bridge = oi.length ? [oi[oi.length - 1], ...fi] : fi;
  const divX = x(Math.max(obs.length - 1, 0));
  const gridY = [0, .25, .5, .75, 1].map(f => min + (max - min) * f);
  const ticks = all.map((p, i) => ({...p, i})).filter(p => p.d.endsWith("-01"));
  const monthLbl = d => new Date(d + "T00:00:00").toLocaleDateString(undefined, {month:"short", year:"numeric"});
  const hover = (pts, lbl) => pts.map(p => `<circle cx="${x(p.i).toFixed(1)}" cy="${y(p.v).toFixed(1)}" r="5" fill="transparent"><title>${p.d}: ${p.v} m (${lbl})</title></circle>`).join("");
  return `<h3>Water depth — last ${obs.length} days and next ${pred.length} · ${esc(s.name)}</h3>
  <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Groundwater level chart: observed and forecast">
    ${gridY.map(g => `<line x1="${padL}" y1="${y(g).toFixed(1)}" x2="${W - padR}" y2="${y(g).toFixed(1)}" stroke="#eef2f4"/>
      <text x="${padL - 8}" y="${(y(g) + 4).toFixed(1)}" font-size="12" fill="#8a9ca4" text-anchor="end">${g.toFixed(2)} m</text>`).join("")}
    ${pred.length ? `<rect x="${divX}" y="${padT}" width="${W - padR - divX}" height="${H - padT - padB}" fill="#fcf1e8" opacity=".6"/>
    <line x1="${divX}" y1="${padT}" x2="${divX}" y2="${H - padB}" stroke="#e8c9b4" stroke-dasharray="3 3"/>
    <text x="${divX + 6}" y="${padT + 14}" font-size="12" fill="#c07a44">forecast →</text>` : ""}
    ${ticks.map(t => `<text x="${x(t.i).toFixed(1)}" y="${H - 12}" font-size="12" fill="#8a9ca4" text-anchor="middle">${monthLbl(t.d)}</text>`).join("")}
    ${oi.length > 1 ? `<path d="${path(oi)}" fill="none" stroke="#1f6f8b" stroke-width="2.5" stroke-linejoin="round"/>` : ""}
    ${bridge.length > 1 ? `<path d="${path(bridge)}" fill="none" stroke="#e07a3f" stroke-width="2.5" stroke-dasharray="6 5"/>` : ""}
    ${fi.map(p => `<circle cx="${x(p.i).toFixed(1)}" cy="${y(p.v).toFixed(1)}" r="2.5" fill="#e07a3f"/>`).join("")}
    ${hover(oi, "observed")}${hover(fi, "forecast")}
  </svg>
  <div class="legend">
    <span><i style="border-color:#1f6f8b"></i>Observed</span>
    <span><i style="border-color:#e07a3f;border-top-style:dashed"></i>ML forecast</span>
    <span>Lower line = water deeper (worse). Hover the line for exact values.</span>
  </div>`;
}

function forecastText(a) {
  if (!a || a.forecast_level == null || a.risk === "UNKNOWN")
    return `A reliable forecast isn't available for this well right now. ${esc((a?.alerts || []).join(" "))}`;
  const c = a.change_m;
  return `Over the next <b>${a.days} days</b>, the model expects the water table to be around
    <b>${num(a.forecast_level)} m</b> deep (today: ${num(a.level)} m). ${c > 0.02
      ? `That is about <b>${num(c)} m deeper</b> — groundwater is expected to keep falling.`
      : c < -0.02 ? `That is about <b>${num(-c)} m shallower</b> — groundwater is expected to recover.`
      : "No big change is expected."}
    <br><span class="small muted">The blue line is what actually happened. The orange dashed line is the ML forecast — shown separately so the two are never confused.</span>`;
}

const STEPS = {
  SAFE:["Continue normal irrigation.","Keep simple records of your borewell water level.","Prefer drip/sprinkler where possible to save water."],
  WATCH:["Plan irrigation by the weather — avoid watering before likely rain.","Shift part of your area to less water-hungry crops.","Fix leaks in pipes and pumps.","Consider a farm pond or recharge pit for the monsoon."],
  CRITICAL:["Reduce pumping hours; irrigate in the cooler early morning/evening.","Choose low water crops (millets, pulses) this season.","Build or clean recharge structures before the monsoon.","Share a borewell with neighbours instead of drilling deeper.","Check the government groundwater advisory before any new borewell."],
  UNKNOWN:["Measure your own borewell level if you can.","Use water carefully until reliable data is back.","Contact the local groundwater office for the latest readings."],
};
function adviceHtml(a) {
  const r = risk(a);
  return `<h3>What should I do?</h3>
    <span class="badge b-${r.cls}">${r.ic} ${r.word}</span>
    <p class="plain" style="margin-top:12px">${esc(a?.advice)}</p>
    <h4 style="margin:16px 0 4px;font-size:15px">Steps you can take</h4>
    <ul class="steps">${STEPS[r.cls].map(x => `<li>${x}</li>`).join("")}</ul>`;
}

function whatifHtml(w, a, err) {
  const seg = k => `<button class="${st.usage === k ? "on" : ""}" onclick="setUsage('${k}')">${k[0].toUpperCase() + k.slice(1)}</button>`;
  let body;
  if (err) body = errBox(err);
  else if (!w) body = `<div class="skel tall"></div>`;
  else if (!w.scenario.length) body = `<p class="muted">No forecast available to simulate.</p>`;
  else {
    const sim = w.scenario.at(-1).level, base = w.baseline.at(-1).level;
    const vs = sim - base;
    let verdict, color, bg;
    if (vs < -0.01) { verdict = "Better than the baseline forecast"; color = "#2e9e6b"; bg = "var(--safe-bg)"; }
    else if (vs > 0.01) { verdict = "Worse than the baseline forecast"; color = "#d8503c"; bg = "var(--crit-bg)"; }
    else { verdict = "Same as the baseline forecast"; color = "#d79a16"; bg = "var(--watch-bg)"; }
    body = `<div class="result" style="background:${bg}">
      <div class="small muted">Simulated water depth in ${w.scenario.length} days</div>
      <div style="font-size:32px;font-weight:800;color:${color}">${num(sim)} m</div>
      <div style="font-weight:700;color:${color}">${verdict}${Math.abs(vs) > 0.01 ? ` (${signed(vs)} m)` : ""}</div>
      <div class="small muted" style="margin-top:4px">Baseline ML forecast: ${num(base)} m · today: ${num(a?.level)} m</div>
    </div>
    <p class="small muted" style="margin:12px 0 0">⚠️ ${esc(w.note)}</p>`;
  }
  return `<h3>What-if — if I change my water use?</h3>
    <p class="plain" style="margin-bottom:12px">Pick a water-use level to simulate the effect on groundwater in ${Math.min(st.days, 30)} days.</p>
    <div class="seg">${seg("low")}${seg("medium")}${seg("high")}</div>${body}`;
}

function rechargeHtml(rc) {
  const yrs = rc.years || [];
  if (!yrs.length) return `<h3>Monsoon recharge</h3><p class="muted">Not enough May and October readings to measure recharge.</p>`;
  const m = Math.max(...yrs.map(y => Math.abs(y.rise_m))) || 1;
  return `<h3>Monsoon recharge (May → October)</h3>
    <div class="bars">${yrs.map(y => `<div class="bar"><b>${y.year}</b>
      <div class="track"><div class="fill" style="width:${Math.max(3, Math.abs(y.rise_m) / m * 100)}%;background:${y.rise_m >= 0 ? "var(--safe)" : "var(--crit)"}"></div></div>
      <span class="num" style="text-align:right;font-weight:700">${signed(y.rise_m)} m</span></div>`).join("")}</div>
    <p class="small muted" style="margin:12px 0 0">How much the water table rose between the average May and average October level.
      Bigger green bars mean the monsoon refilled the aquifer well.</p>`;
}

function anomaliesHtml(an) {
  const ev = [...(an.events || [])].sort((a, b) => b.date.localeCompare(a.date));
  if (!ev.length) return `<h3>Unusual readings</h3><p class="plain">No sudden jumps detected in this well's history.</p>`;
  return `<h3>Unusual readings (${ev.length})</h3>
    <div class="tscroll"><table><thead><tr><th>Date</th><th>What happened</th><th class="num">Level</th><th class="num">Day change</th></tr></thead>
    <tbody>${ev.slice(0, 8).map(e => `<tr><td>${fmtDate(e.date)}</td>
      <td>${e.change > 0 ? "Sudden drop in water" : "Sudden rise in water"}</td>
      <td class="num">${num(e.level)} m</td><td class="num">${signed(e.change, 3)} m</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted" style="margin:12px 0 0">Day-to-day changes far outside the usual range. They can be heavy rain, heavy pumping, or a sensor fault.
      ${ev.length > 8 ? `Showing the 8 most recent.` : ""}</p>`;
}

function aboutHtml() {
  const lastDates = st.stations.map(s => statusNow(s)?.as_of).filter(Boolean).sort();
  byId("aboutData").innerHTML = `<h3>Data</h3>
    <div class="kv"><span>Groundwater</span><b>India-WRIS / CGWB</b></div>
    <div class="kv"><span>Rainfall</span><b>IMD</b></div>
    <div class="kv"><span>Monitoring wells</span><b>${st.stations.length}</b></div>
    <div class="kv"><span>Latest reading</span><b>${fmtDate(lastDates.at(-1))}</b></div>
    <div class="kv"><span>Forecast horizon</span><b>up to 30 days</b></div>
    <p class="small muted" style="margin:14px 0 0">Risk levels come from pipeline thresholds on the forecast change and are not
      independently validated. Use them as decision support, not as an official assessment.</p>`;
  const m = st.model;
  if (!m) { byId("aboutModels").innerHTML = `<h3>Model</h3><p class="muted">Model details unavailable.</p>`; return; }
  const met = m.metrics || {};
  const rows = HORIZONS.filter(h => met[`mae_${h}`] != null).map(h => {
    const a = met[`mae_${h}`], b = met[`persistence_mae_${h}`];
    const gain = b ? (1 - a / b) * 100 : null;
    return `<tr><td>${h} days</td><td class="num"><b>${num(a, 3)}</b></td><td class="num">${num(b, 3)}</td>
      <td class="num" style="color:${gain > 0 ? "var(--safe)" : "var(--crit)"}">${gain == null ? "—" : signed(gain, 1) + "%"}</td></tr>`;
  }).join("");
  byId("aboutModels").innerHTML = `<h3>Model accuracy</h3>
    <div class="kv" style="margin-bottom:8px"><span>Selected model</span><b>${esc(m.name)}</b></div>
    ${rows ? `<div class="tscroll"><table><thead><tr><th>Horizon</th><th class="num">Model MAE</th><th class="num">Persistence MAE</th><th class="num">Better by</th></tr></thead>
    <tbody>${rows}</tbody></table></div>
    <p class="small muted" style="margin:12px 0 0">MAE = average error in metres (lower is better). Persistence assumes the level stays at its
      last reading. The model with the lowest 30-day error is selected.</p>` : `<p class="muted">No evaluation metrics recorded.</p>`}`;
}

/* ---------- render ---------- */
function renderAll() {
  byId("stationSel").value = st.cur;
  byId("daysSeg").innerHTML = HORIZONS.map(d => `<button class="${st.days === d ? "on" : ""}" onclick="setDays(${d})">${d} days</button>`).join("");
  byId("thDays").textContent = st.days;
  byId("wells").innerHTML = sidebar();
  byId("region").innerHTML = regionHtml();
  byId("mapbox").innerHTML = mapPins();
  byId("wellTable").innerHTML = wellRows();
  byId("alertList").innerHTML = alertsHtml();
  aboutHtml();
  renderStation();
}

let ticket = 0;
async function renderStation() {
  const my = ++ticket, s = S(), a = statusNow(s);
  const live = () => my === ticket;
  byId("hero").innerHTML = a ? heroHtml(s, a) : `<div class="skel tall"></div>`;
  byId("meaning").innerHTML = plainCondition(a);
  byId("reco").innerHTML = esc(a?.advice);
  byId("fcLead").textContent = `What might happen at ${s.name} over the next ${st.days} days?`;
  byId("fcText").innerHTML = forecastText(a);
  byId("advLead").textContent = `Practical steps for ${s.name}, and how your water use could change the outlook.`;
  byId("trLead").textContent = `How much the monsoon refills the well at ${s.name} each year, and unusual readings.`;
  byId("advice-card").innerHTML = adviceHtml(a);
  byId("chart").innerHTML = `<div class="skel tall"></div>`;
  byId("whatif").innerHTML = whatifHtml(null, a);
  byId("recharge").innerHTML = `<div class="skel tall"></div>`;
  byId("anomalies").innerHTML = `<div class="skel tall"></div>`;

  const fill = (id, p, fn) => p.then(v => live() && (byId(id).innerHTML = fn(v)))
                               .catch(e => live() && (byId(id).innerHTML = errBox(e)));
  fill("chart", getForecast(s), fc => chartHtml(s, fc));
  fill("recharge", getRecharge(s), rechargeHtml);
  fill("anomalies", getAnomalies(s), anomaliesHtml);
  getWhatif(s).then(w => live() && (byId("whatif").innerHTML = whatifHtml(w, a)))
              .catch(e => live() && (byId("whatif").innerHTML = whatifHtml(null, a, e)));
}

function pick(i, jump) {
  st.cur = i;
  try { localStorage.setItem("jalsetu.station", st.stations[i].id); } catch {}
  renderAll();
  if (jump) location.hash = "#" + jump;
}
async function setDays(d) {
  st.days = d;
  renderAll();                 // shows loading state for anything not cached yet
  await loadStatuses();
  renderAll();
}
function setUsage(k) {
  st.usage = k;
  const s = S(), a = statusNow(s), my = ticket;
  byId("whatif").innerHTML = whatifHtml(null, a);
  getWhatif(s).then(w => my === ticket && (byId("whatif").innerHTML = whatifHtml(w, a)))
              .catch(e => my === ticket && (byId("whatif").innerHTML = whatifHtml(null, a, e)));
}

/* highlight the nav link for the section in view */
const links = [...document.querySelectorAll("#topnav a")];
const sections = [...document.querySelectorAll("main section")];
function spy() {
  const atEnd = innerHeight + scrollY >= document.body.scrollHeight - 4;
  let cur = sections[0];
  for (const s of sections) if (s.getBoundingClientRect().top <= 120) cur = s;
  if (atEnd) cur = sections[sections.length - 1];
  links.forEach(l => l.classList.toggle("on", l.getAttribute("href") === "#" + cur.id));
}
addEventListener("scroll", spy, {passive:true});

function fatal(e) {
  byId("app").hidden = true;
  const f = byId("fatal"); f.hidden = false;
  f.innerHTML = `<div class="card">
    <h3>Can't reach the groundwater service</h3>
    <p class="plain">The dashboard couldn't load data from <code>${esc(API)}</code>.</p>
    <p class="small muted">${esc(e.message)}</p>
    <p class="plain" style="margin-top:14px">If you're running this locally, prepare the data and start the API from the project root:</p>
    <pre>uvicorn app.main:app --reload</pre>
    <p class="plain">and keep the dashboard running in a second terminal:</p>
    <pre>python frontend/serve.py</pre>
    <p class="small muted">Then open <code>http://127.0.0.1:5500/</code>.</p>
    <button class="btn" onclick="location.reload()">Try again</button></div>`;
}

async function init() {
  try {
    const [stations, model] = await Promise.all([api("/stations"), api("/model").catch(() => null)]);
    if (!stations.length) throw new Error("The API returned no stations.");
    st.stations = stations; st.model = model;
  } catch (e) { return fatal(e); }

  let saved; try { saved = localStorage.getItem("jalsetu.station"); } catch {}
  const idx = st.stations.findIndex(s => s.id === saved);
  st.cur = idx >= 0 ? idx : 0;

  if (SNAPSHOT) byId("source").textContent = `Built from the Groundwater Forecast API on ${fmtDate(SNAPSHOT)}.`;

  const sel = byId("stationSel");
  sel.innerHTML = st.stations.map((s, i) => `<option value="${i}">${esc(s.name)}</option>`).join("");
  sel.onchange = e => pick(+e.target.value);

  renderAll();
  await loadStatuses();
  renderAll();
  spy();
}
init();
