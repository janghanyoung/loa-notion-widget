async function loadData() {
  const res = await fetch("./daily.json");
  const data = await res.json();

  // 상단
  document.getElementById("title").textContent = data.title;
  document.getElementById("date").textContent = data.date;
  document.getElementById("headline").textContent = data.headline;
  document.getElementById("summary").textContent = data.summary;

  // 본문
  const columnsEl = document.getElementById("columns");
  columnsEl.innerHTML = "";

  data.columns.forEach(col => {
    const el = document.createElement("article");
    el.className = "news-column";

    let inner = `
      <p class="column-tag">${col.tag}</p>
      <h3 class="column-title">${col.title}</h3>
    `;

    if (col.body) {
      inner += `<p>${col.body.replace(/\n/g, "<br>")}</p>`;
    }

    if (col.highlight) {
      inner += `<div class="mini-card">${col.highlight}</div>`;
    }

    if (col.stats) {
      col.stats.forEach(s => {
        inner += `
          <div class="stat-item">
            <span>${s.name}</span>
            <span>${s.value}</span>
          </div>
        `;
      });
    }

    if (col.todos) {
      inner += `<ul class="todo-list">`;
      col.todos.forEach(t => {
        inner += `<li>${t}</li>`;
      });
      inner += `</ul>`;
    }

    if (col.quote) {
      inner += `<blockquote>${col.quote}</blockquote>`;
    }

    el.innerHTML = inner;
    columnsEl.appendChild(el);
  });

  // footer
  const footerEl = document.getElementById("footer");
  footerEl.innerHTML = "";

  data.footer.forEach(line => {
    const div = document.createElement("div");
    div.className = "bottom-box";
    div.textContent = line;
    footerEl.appendChild(div);
  });
}

loadData();
