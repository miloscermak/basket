// Načte předpočítané JSONy a vykreslí všechny sekce webu.
const fmt = new Intl.NumberFormat("cs-CZ");
const $ = (id) => document.getElementById(id);

const DAYS = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"];

async function main() {
  // data jsou přibalená v data.js (fetch nefunguje při otevření přes file://)
  const o = window.BASKET_DATA.overview;
  const r = window.BASKET_DATA.records;

  bignums(o);
  categories(o);
  heatmap(o);
  weeks(o);
  homeAdvantage(o);
  curiosities(o, r);
  tables(o, r);
  careers();
  search();
  shotmap();
  threes();
  anatomy();
  clutch();
  names();
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

// Kariérní data jsou volitelná — sekce se ukáže, jen když jsou v balíčku.
async function careers() {
  const c = window.BASKET_DATA.careers;
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

// ---------- vyhledávání hráčů ----------
const deacc = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function search() {
  const idx = window.BASKET_DATA.search;
  if (!idx) return;
  const input = $("search-input");
  const out = $("search-results");
  const norm = idx.map((p) => deacc(p[0]));

  function render(q) {
    if (q.length < 2) {
      out.innerHTML = `<p class="hint">Napiš aspoň dvě písmena.</p>`;
      return;
    }
    const nq = deacc(q);
    const hits = [];
    for (let i = 0; i < norm.length && hits.length < 15; i++) {
      if (norm[i].includes(nq)) hits.push(idx[i]);
    }
    if (!hits.length) {
      out.innerHTML = `<p class="hint">Nikdo takový letos nenastoupil.</p>`;
      return;
    }
    out.innerHTML = table(
      ["Hráč/ka", "Věk", "Letos", "Kariéra"],
      hits.map(([name, age, teams, games, ppg, comps, first, seasons, rec]) => [
        td(`<b>${name}</b>` + sub(teams || "")),
        td(age ?? "?"),
        td(`${games ?? "?"} zápasů, ${ppg ?? "?"} b/z` + sub(`${comps} ${comps === 1 ? "soutěž" : comps < 5 ? "soutěže" : "soutěží"}`)),
        td(first ? `od ${first}, ${seasons} sezón` + (rec ? sub(`max ${rec} bodů v zápase`) : "") : "první sezóna"),
      ])
    );
  }
  input.addEventListener("input", () => render(input.value.trim()));
  render("");
}

// ---------- střelecká mapa ----------
// souřadnice: fx 0–50 (délka půlky, koš u 0), fy 0–100 (šířka hřiště)
function shotmap() {
  const data = window.BASKET_DATA.shots;
  if (!data) return;
  const S = 30; // px na metr
  const W = 14 * S, H = 15 * S;
  const px = (fx) => (fx * 28 / 100) * S;
  const py = (fy) => (fy * 15 / 100) * S;
  const cell = data.cell;

  function courtLines() {
    const bx = px(5.625), by = H / 2; // koš 1,575 m od čáry
    return `
      <g fill="none" stroke="#5a4c3d" stroke-width="1.5">
        <rect x="0" y="0" width="${W}" height="${H}"/>
        <rect x="0" y="${by - 2.45 * S}" width="${5.8 * S}" height="${4.9 * S}"/>
        <circle cx="${5.8 * S}" cy="${by}" r="${1.8 * S}"/>
        <circle cx="${bx}" cy="${by}" r="${0.23 * S}" stroke="#8a7a68"/>
        <path d="M ${0} ${by - 6.6 * S} L ${bx} ${by - 6.6 * S}
                 A ${6.75 * S} ${6.75 * S} 0 0 1 ${bx} ${by + 6.6 * S}
                 L ${0} ${by + 6.6 * S}"/>
      </g>`;
  }

  function render(label) {
    const m = data.mapy[label];
    const max = Math.max(...m.cells.map((c) => c[2]));
    let rects = "";
    for (const [cx, cy, att, made] of m.cells) {
      if (px(cx * cell) > W) continue;
      const a = Math.sqrt(att / max); // odmocnina, ať jsou vidět i řidší místa
      rects += `<rect x="${px(cx * cell)}" y="${py(cy * cell)}"
        width="${px(cell) + 0.5}" height="${py(cell) + 0.5}"
        fill="rgba(255,140,58,${(0.9 * a).toFixed(3)})">
        <title>${att} střel, úspěšnost ${Math.round((100 * made) / att)} %</title></rect>`;
    }
    $("shotmap").innerHTML =
      `<svg viewBox="-8 -8 ${W + 16} ${H + 16}" role="img" aria-label="Střelecká mapa – ${label}">
         <g>${rects}</g>${courtLines()}</svg>`;
    $("shotmap-note").textContent =
      `${label}: ${fmt.format(m.strel)} střel z pole, úspěšnost ${m.usp} %.`;
    document.querySelectorAll("#shotmap-buttons button").forEach((b) =>
      b.classList.toggle("active", b.textContent === label));
  }

  $("shotmap-buttons").innerHTML = Object.keys(data.mapy)
    .map((l) => `<button>${l}</button>`)
    .join("");
  document.querySelectorAll("#shotmap-buttons button").forEach((b) =>
    b.addEventListener("click", () => render(b.textContent)));
  render(Object.keys(data.mapy)[0]);
}

function threes() {
  const data = window.BASKET_DATA.shots;
  if (!data) return;
  $("threes-bars").innerHTML = barChart(
    data.trojky_urovne.map((u) => [u.uroven, u.podil_trojek]),
    { max: 100, fmtVal: (v) => v.toFixed(1) + " %" }
  );
}

// ---------- anatomie zápasu ----------
function anatomy() {
  const d = window.BASKET_DATA.pbp;
  if (!d) return;
  $("anatomy-note").textContent =
    `Kolik bodů v průměru padne v každé minutě zápasu (${fmt.format(d.anatomie_zapasu)} ` +
    `zápasů s podrobným zápisem, obě družstva dohromady). Hrací čas 4 × 10 minut.`;
  const max = Math.max(...d.anatomie.map((m) => m.bodu_prumer));
  $("anatomy").innerHTML =
    `<div style="display:flex;align-items:flex-end;gap:2px;height:130px">` +
    d.anatomie
      .map(
        (m) =>
          `<div title="minuta ${m.minuta}: ${m.bodu_prumer} bodu" style="flex:1;background:${m.minuta % 20 > 10 || m.minuta % 20 === 0 ? "var(--accent)" : "var(--accent-soft)"};border-top:2px solid var(--accent);height:${(100 * m.bodu_prumer) / max}%"></div>`
      )
      .join("") +
    `</div><div style="display:flex;color:var(--ink-dim);font-size:.75rem;margin-top:6px">` +
    ["1. čtvrtina", "2. čtvrtina", "3. čtvrtina", "4. čtvrtina"]
      .map((q) => `<div style="flex:1;text-align:center">${q}</div>`)
      .join("") +
    "</div>";
}

// ---------- clutch ----------
function clutch() {
  const d = window.BASKET_DATA.pbp;
  if (!d) return;
  $("clutch-note").textContent =
    `Body v posledních dvou minutách vyrovnaných zápasů (rozdíl do 5 bodů) a v prodloužení. ` +
    `Takových koncovek se letos hrálo ${fmt.format(d.clutch_zapasu)} — v soutěžích s podrobným zápisem.`;
  $("tbl-clutch").innerHTML = table(
    ["Bodů", "Hráč/ka", "Koncovek"],
    d.clutch.slice(0, 12).map((x) => [
      tdn(x.bodu),
      td(`${x.jmeno}` + sub(`${x.tym} · ${x.soutez}`)),
      td(x.zapasu),
    ])
  );
}

// ---------- jména ----------
function names() {
  const d = window.BASKET_DATA.names;
  if (!d) return;
  $("tbl-prijmeni").innerHTML = table(
    ["Hráčů", "Příjmení"],
    d.prijmeni.slice(0, 10).map((x) => [tdn(x.hracu), td(`${x.prijmeni}` + sub(x.tvary))])
  );
  $("tbl-klany").innerHTML = table(
    ["Lidí", "Rodina"],
    d.klany.slice(0, 8).map((x) => [
      tdn(x.hracu),
      td(`${x.prijmeni} — ${x.tym}` + sub(x.jmena)),
    ])
  );
  $("tbl-rozpeti").innerHTML = table(
    ["Rozpětí", "Soutěž", "Nejmladší", "Nejstarší"],
    d.vekova_rozpeti.slice(0, 8).map((x) => [
      tdn(`${x.rozpeti} let`),
      td(x.soutez),
      td(`${x.jmeno_nejmladsi} (${x.nejmladsi})`),
      td(`${x.jmeno_nejstarsi} (${x.nejstarsi})`),
    ])
  );
}

main().catch((e) => {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<p style="background:#a33;color:#fff;padding:10px 16px">Nepodařilo se načíst data: ${e}</p>`
  );
});
