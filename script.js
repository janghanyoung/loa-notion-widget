async function loadData() {
  try {
    const res = await fetch("./daily.json", { cache: "no-store" });

    if (!res.ok) {
      throw new Error(`daily.json 로드 실패: ${res.status}`);
    }

    const data = await res.json();

    setText("title", data.title || "아크라시아 일보");
    setText("date", data.date || "");
    setText("headline", data.headline || "");
    setText("summary", data.summary || "");
    setText("subhead", data.subhead || "모험 · 일정 · 수집");

    const briefList = document.getElementById("brief-list");
    if (briefList) {
      briefList.innerHTML = "";

      (data.briefs || []).forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        briefList.appendChild(li);
      });

      if (!data.briefs || data.briefs.length === 0) {
        const li = document.createElement("li");
        li.textContent = "오늘의 짧은 요약이 없습니다.";
        briefList.appendChild(li);
      }
    }

    const columnsEl = document.getElementById("columns");
    if (columnsEl) {
      columnsEl.innerHTML = "";

      (data.columns || []).forEach((col) => {
        const article = document.createElement("article");
        article.className = "news-column";

        let html = `
          <p class="column-tag">${escapeHtml(col.tag || "")}</p>
          <h3 class="column-title">${escapeHtml(col.title || "")}</h3>
        `;

        if (col.body) {
          html += `<p>${escapeHtml(col.body).replace(/\n/g, "<br>")}</p>`;
        }

        if (col.highlight) {
          html += `
            <div class="mini-card">
              <p class="mini-card-label">CHECK</p>
              <p class="mini-card-text">${escapeHtml(col.highlight)}</p>
            </div>
          `;
        }

        if (Array.isArray(col.stats) && col.stats.length > 0) {
          html += `<div class="stat-list">`;
          col.stats.forEach((s) => {
            html += `
              <div class="stat-item">
                <span class="stat-name">${escapeHtml(s.name || "")}</span>
                <span class="stat-value">${escapeHtml(s.value || "")}</span>
              </div>
            `;
          });
          html += `</div>`;
        }

        if (col.extra_body) {
          html += `<p>${escapeHtml(col.extra_body).replace(/\n/g, "<br>")}</p>`;
        }

        if (col.quote) {
          html += `<blockquote class="quote-box">${escapeHtml(col.quote)}</blockquote>`;
        }

        if (Array.isArray(col.todos) && col.todos.length > 0) {
          html += `<ul class="todo-list">`;
          col.todos.forEach((todo) => {
            html += `<li>${escapeHtml(todo)}</li>`;
          });
          html += `</ul>`;
        }

        article.innerHTML = html;
        columnsEl.appendChild(article);
      });
    }

    const footerEl = document.getElementById("footer");
    if (footerEl) {
      footerEl.innerHTML = "";

      (data.footer || []).forEach((line) => {
        const box = document.createElement("div");
        box.className = "bottom-box";
        box.innerHTML = `<p>${escapeHtml(line)}</p>`;
        footerEl.appendChild(box);
      });
    }
  } catch (error) {
    console.error(error);

    const paper = document.querySelector(".paper");
    if (paper) {
      const errorBox = document.createElement("div");
      errorBox.className = "error-box";
      errorBox.textContent = `위젯 로딩 실패: ${error.message}`;
      paper.appendChild(errorBox);
    }
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  } else {
    console.warn(`id="${id}" 요소가 없습니다.`);
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

loadData();
