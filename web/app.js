// Načte předpočítané JSONy a vykreslí všechny sekce webu.
const fmt = new Intl.NumberFormat("cs-CZ");
const $ = (id) => document.getElementById(id);

const DAYS = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"];

async function main() {
  const [o, r] = await Promise.all([
    fetch("data/overview.json").then((x) => x.json()),
    fetch("data/records.json").then((x) => x.json()),
  ]);

  bignums(o);
  categories(o);
  heatmap(o);
  weeks(o);
  homeAdvantage(o);
  curiosities(o, r);
  tables(o, r);
  careers();
  $("generated").textContent = "Vygenerováno " + new Date().toLocaleDateString("cs-CZ");
}

function bignums(o) {
  const items = [
    [o.bodu_celkem, "bodů padlo za sezónu"],
    [o.zapasu, "odehraných zápasů"],
    [o.hracu_se_statistikami, "hráčů a hráček ve statistikách"],
    [o.soutezi, "soutěží"],
    [o.hal, "hal a tělocvičen"],
    [o.rozhodcich_celkem, "rozhodčích"],
  ];
  $("bignums").innerHTML = items
    .map(([n, t]) => `<div class="bignum"><b>${fmt.format(n)}</b><span>${t}</span></div>`)
    .join("");
}

function barChart(rows, { max = null, fmtVal = (v) => fmt.format(v) } = {}) {
  const m = max ?? Math.max(...rows.map((r) => r[1]));
  return rows
    .map(
      ([label, val]) => `
      <div class="bar-row">
        <div class="bar-label" title="${label}">${label}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${(100 * val) / m}%"></div></div>
        <div class="bar-value">${fmtVal(val)}</div>
      </div>`
    )
    .join("");
}

function categories(o) {
  const cats = Object.entries(o.kategorie).sort((a, b) => b[1].zapasu - a[1].zapasu);
  $("cat-bars").innerHTML =
    "<h3>Zápasy podle kategorií</h3>" +
    barChart(cats.map(([k, v]) => [k, v.zapasu]));
  const youth = Object.entries(o.mladez_rocniky).sort(
    (a, b) => parseInt(b[0].slice(1)) - parseInt(a[0].slice(1))
  );
  $("youth-bars").innerHTML =
    "<h3>Mládež po ročnících</h3>" + barChart(youth);
}

function heatmap(o) {
  const byKey = {};
  let max = 0;
  for (const h of o.heatmapa) {
    byKey[`${h.den}-${h.hodina}`] = h.n;
    max = Math.max(max, h.n);
  }
  const hours = [];
  for (let h = 8; h <= 21; h++) hours.push(h);
  let html = `<div class="heat-grid" style="grid-template-columns: 34px repeat(${hours.length}, 1fr)">`;
  html += `<div></div>` + hours.map((h) => `<div class="heat-label">${h}</div>`).join("");
  for (let d = 1; d <= 7; d++) {
    html += `<div class="heat-label">${DAYS[d - 1]}</div>`;
    for (const h of hours) {
      const n = byKey[`${d}-${h}`] || 0;
      const a = n ? 0.15 + (0.85 * n) / max : 0;
      html += `<div class="heat-cell" style="background:rgba(255,140,58,${a})" title="${DAYS[d - 1]} ${h}:00 — ${fmt.format(n)} zápasů"></div>`;
    }
  }
  $("heatmap").innerHTML = html + "</div>";
}

function weeks(o) {
  const rows = o.tydny.filter((t) => t.tyden);
  const max = Math.max(...rows.map((t) => t.n));
  $("weeks").innerHTML =
    "<h3>Zápasy po týdnech sezóny</h3>" +
    `<div style="display:flex;align-items:flex-end;gap:2px;height:90px;margin-top:8px">` +
    rows
      .map(
        (t) =>
          `<div title="týden ${t.tyden}: ${fmt.format(t.n)} zápasů" style="flex:1;background:var(--accent-soft);border-top:2px solid var(--accent);height:${(100 * t.n) / max}%"></div>`
      )
      .join("") +
    "</div>";
}

function homeAdvantage(o) {
  $("homeadv").innerHTML = barChart(
    o.domaci_vyhoda_urovne.map((u) => [u.uroven, u.domaci_pct]),
    { max: 100, fmtVal: (v) => v.toFixed(1) + " %" }
  );
}

function curiosities(o, r) {
  const nv = o.nejvyssi_vyhra[0];
  const nb = o.nejvic_bodu[0];
  const cards = [
    [fmt.format(o.nejtesnejsich_o1), "zápasů rozhodl jediný bod"],
    [r.prodlouzeni.length, "zápasů došlo do prodloužení — jediné dvojité vyhrálo USK Praha B 95:94"],
    [`+${nv.rozdil}`, `nejvyšší výhra: ${nv.home} – ${nv.away} ${nv.home_score}:${nv.away_score} (${nv.soutez})`],
    [fmt.format(nb.soucet), `bodů padlo v jednom zápase: ${nb.home} – ${nb.away} ${nb.home_score}:${nb.away_score}`],
    [(100 * o.domaci_vyhry_podil).toFixed(1) + " %", "zápasů vyhráli domácí"],
    [fmt.format(o.prumer_bodu), "bodů padne v průměrném českém zápase"],
  ];
  $("curio-cards").innerHTML = cards
    .map(([n, t]) => `<div class="card curio"><b>${n}</b><p>${t}</p></div>`)
    .join("");
}

function table(headers, rows) {
  return (
    `<table><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr>` +
    rows.map((cells) => `<tr>${cells.join("")}</tr>`).join("") +
    "</table>"
  );
}
const td = (x) => `<td>${x}</td>`;
const tdn = (x) => `<td class="num">${x}</td>`;
const sub = (x) => `<span class="sub">${x}</span>`;

function tables(o, r) {
  $("tbl-obraty").innerHTML = table(
    ["Vedl o", "Zápas"],
    r.obraty.map((x) => [
      tdn(x.vedeni),
      td(`${x.domaci} – ${x.hoste} ${x.home_score}:${x.away_score}` + sub(`${x.soutez} · ${x.datum}`)),
    ])
  );

  $("tbl-snury").innerHTML = table(
    ["Výher", "Tým"],
    r.snury.slice(0, 8).map((x) => [tdn(x.vyher), td(x.tym + sub(`${x.od} → ${x.do}`))])
  );

  $("tbl-vykony").innerHTML = table(
    ["Bodů", "Hráč"],
    r.top_vykony.slice(0, 10).map((x) => [
      tdn(x.bodu),
      td(`${x.jmeno}` + sub(`${x.domaci} – ${x.hoste} · ${x.soutez} · ${x.datum}`)),
    ])
  );

  $("tbl-trojky").innerHTML = table(
    ["Trojek", "Hráč"],
    r.trojky_zapas.slice(0, 10).map((x) => [
      tdn(x.trojek),
      td(`${x.jmeno}` + sub(`${x.domaci} – ${x.hoste} · ${x.soutez}`)),
    ])
  );

  $("tbl-nejstarsi").innerHTML = table(
    ["Věk", "Hráč/ka"],
    r.nejstarsi.slice(0, 10).map((x) => [
      tdn(x.vek),
      td(`${x.jmeno}` + sub(`${x.tym} · ${x.zapasu} zápasů`)),
    ])
  );

  $("tbl-zelezni").innerHTML = table(
    ["Zápasů", "Hráč/ka"],
    r.zelezni.slice(0, 10).map((x) => [
      tdn(x.zapasu),
      td(`${x.jmeno} (${x.vek})` + sub(`${x.soutezi} soutěží`)),
    ])
  );

  $("tbl-smece").innerHTML = table(
    ["Smečí", "Hráč"],
    r.smece.map((x) => [tdn(x.smeci), td(x.jmeno)])
  );

  $("tbl-rozhodci").innerHTML = table(
    ["Zápasů", "Rozhodčí"],
    o.rozhodci_top.slice(0, 10).map((x) => [tdn(fmt.format(x.zapasu)), td(x.jmeno)])
  );

  $("tbl-haly").innerHTML = table(
    ["Zápasů", "Hala"],
    o.haly_top.slice(0, 10).map((x) => [tdn(fmt.format(x.zapasu)), td(x.hala)])
  );

  $("tbl-navstevnost").innerHTML = table(
    ["Diváků", "Zápas"],
    r.navstevnost_top.map((x) => [
      tdn(fmt.format(x.divaku)),
      td(`${x.domaci} – ${x.hoste} ${x.home_score}:${x.away_score}` + sub(`${x.soutez} · ${x.datum}`)),
    ])
  );
}

// Kariérní data jsou volitelná — sekce se ukáže, až careers.json existuje.
async function careers() {
  let c;
  try {
    c = await fetch("data/careers.json").then((x) => (x.ok ? x.json() : null));
  } catch {
    return;
  }
  if (!c) return;
  document.getElementById("kariery").hidden = false;

  $("tbl-kariery").innerHTML = table(
    ["Sezón", "Hráč/ka"],
    c.nejdelsi_kariery.slice(0, 10).map((x) => [
      tdn(x.sezon),
      td(`${x.jmeno}` + sub(`od ${x.prvni} · ${fmt.format(x.zapasu)} zápasů`)),
    ])
  );

  $("tbl-historie").innerHTML = table(
    ["Zápasů", "Hráč/ka"],
    c.nejvic_zapasu_historie.slice(0, 10).map((x) => [
      tdn(fmt.format(x.zapasu)),
      td(`${x.jmeno}${x.aktivni ? "" : " (už nehraje)"}` + sub(`${x.prvni} – ${x.posledni} · ${x.sezon} sezón`)),
    ])
  );

  $("tbl-rekordy").innerHTML = table(
    ["Bodů", "Hráč/ka", "Kdy"],
    c.rekordy_letos.map((x) => [
      tdn(x.hodnota),
      td(`${x.jmeno}` + sub(`${x.sezon} sezón v evidenci`)),
      td(x.datum ?? ""),
    ])
  );
}

main().catch((e) => {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<p style="background:#a33;color:#fff;padding:10px 16px">Nepodařilo se načíst data: ${e}</p>`
  );
});
