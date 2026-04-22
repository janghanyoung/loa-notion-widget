async function loadData() {
  try {
    const res = await fetch("./daily.json", { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`daily.json 로드 실패: ${res.status}`);
    }

    const data = await res.json();

    setText("paperTitle", data.paperTitle || "노이호이테 일보");
    setText("metaLeft", data.metaLeft || "");
    setText("metaCenter", data.metaCenter || "");
    setText("metaRight", data.metaRight || "");
    setText("mainHeadline", data.mainHeadline || "");
    setText("sideHeadline", data.sideHeadline || "");
    setText("characterNameplate", data.character?.nameplate || "");
    setText("characterSubplate", data.character?.subplate || "");

    setImage("characterImage", data.character?.image);
    setImage("islandImage", data.islandArticle?.image);

    renderDl("profileStats", data.profileStats || []);
    renderDl("equipmentStats", data.equipmentStats || []);
    renderLookbook("lookbookTableBody", data.lookbook || []);
    renderBulletColumns("todayIslands", data.islandArticle?.todayIslands || []);
    renderList("raidList", data.islandArticle?.remainingRaids || []);
    renderMarket("marketIslandNews", data.market?.island || []);
    renderMarket("marketEventNews", data.market?.events || []);
    renderMarket("guildAdNews", data.market?.guild || []);
    setText("quoteText", data.islandArticle?.quote || "");
  } catch (error) {
    console.error(error);
    const paper = document.querySelector(".paper");
    if (paper) {
      const box = document.createElement("div");
      box.className = "error-box";
      box.textContent = `위젯 로딩 실패: ${error.message}`;
      paper.appendChild(box);
    }
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? "";
}

function setImage(id, src) {
  const el = document.getElementById(id);
  if (el && src) el.src = src;
}

function renderDl(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = "";

  items.forEach((item) => {
    const dt = document.createElement("dt");
    dt.textContent = item.label || "";
    const dd = document.createElement("dd");
    dd.textContent = item.value || "";
    el.appendChild(dt);
    el.appendChild(dd);
  });
}

function renderLookbook(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = "";

  items.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(item.name || "")}</td>
      <td>${escapeHtml(item.part || "")}</td>
      <td>${escapeHtml(item.color || "")}</td>
      <td>${escapeHtml(item.avgPrice || "")}</td>
      <td>${escapeHtml(item.lowestPrice || "")}</td>
    `;
    el.appendChild(tr);
  });
}

function renderBulletColumns(id, items) {
  const wrap = document.getElementById(id);
  if (!wrap) return;
  wrap.innerHTML = "";
  const ul = document.createElement("ul");

  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  });

  wrap.appendChild(ul);
}

function renderList(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = "";

  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

function renderMarket(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = "";

  if (Array.isArray(items)) {
    const ul = document.createElement("ul");
    items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      ul.appendChild(li);
    });
    el.appendChild(ul);
  } else if (typeof items === "string") {
    const p = document.createElement("p");
    p.textContent = items;
    el.appendChild(p);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", loadData);
} else {
  loadData();
}
