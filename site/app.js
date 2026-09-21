const OWNER = "paytbidd";
const SELF = "omarchy-design-factory";

const grid = document.querySelector("[data-plugin-grid]");
const countEl = document.querySelector("[data-count]");
const schemeBtn = document.querySelector("[data-scheme-toggle]");

function systemScheme() {
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyScheme(scheme, persist) {
  const next = scheme === "dark" ? "dark" : "light";
  document.documentElement.dataset.scheme = next;
  if (persist) localStorage.setItem("factory-scheme", next);
  if (schemeBtn) {
    schemeBtn.textContent = next === "dark" ? "Orange" : "Blue";
    schemeBtn.setAttribute(
      "aria-label",
      next === "dark" ? "Use light blue scheme" : "Use dark orange scheme"
    );
  }
}

function initScheme() {
  const stored = localStorage.getItem("factory-scheme");
  applyScheme(stored || systemScheme(), false);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (event) => {
    if (!localStorage.getItem("factory-scheme")) {
      applyScheme(event.matches ? "dark" : "light", false);
    }
  });
  schemeBtn?.addEventListener("click", () => {
    const current = document.documentElement.dataset.scheme || systemScheme();
    applyScheme(current === "dark" ? "light" : "dark", true);
  });
}

function titleFromName(name) {
  return name
    .replace(/^omarchy-/, "")
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function installCommand(name) {
  return `omarchy plugin add https://github.com/${OWNER}/${name}.git --enable`;
}

function mergePlugins(listed, overrides) {
  const excluded = new Set([SELF, ...((overrides && overrides.exclude) || [])]);
  const extra = (overrides && overrides.plugins) || {};
  return (listed || [])
    .filter((plugin) => plugin.name && !excluded.has(plugin.name))
    .map((plugin) => {
      const hand = extra[plugin.name] || {};
      if (hand.hidden) return null;
      return {
        name: plugin.name,
        title: hand.title || plugin.title || titleFromName(plugin.name),
        blurb: hand.blurb || hand.description || plugin.blurb || plugin.description || "",
        icon: hand.icon || plugin.icon || `icons/${plugin.name.replace(/^omarchy-/, "")}.svg`,
        html_url: plugin.html_url || `https://github.com/${OWNER}/${plugin.name}`,
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-cache" });
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

async function loadIcon(path) {
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error("missing icon");
    return await response.text();
  } catch {
    const fallback = await fetch("./icons/default.svg");
    return fallback.text();
  }
}

function cardTemplate(plugin, iconMarkup) {
  const article = document.createElement("article");
  article.className = "card";
  article.innerHTML = `
    <div class="card-top">
      <div class="icon" aria-hidden="true">${iconMarkup}</div>
      <div>
        <h3>${escapeHtml(plugin.title)}</h3>
        <p class="one-line">${escapeHtml(plugin.blurb)}</p>
      </div>
    </div>
    <div class="cmd">
      <pre><code></code></pre>
      <button type="button">Copy</button>
    </div>
    <a class="repo" href="${plugin.html_url}">${plugin.name} ↗</a>
  `;
  article.querySelector("code").textContent = installCommand(plugin.name);
  const button = article.querySelector("button");
  button.addEventListener("click", async () => {
    const command = installCommand(plugin.name);
    try {
      await navigator.clipboard.writeText(command);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select";
      const range = document.createRange();
      range.selectNodeContents(article.querySelector("code"));
      const selection = getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    setTimeout(() => {
      button.textContent = "Copy";
    }, 1400);
  });
  return article;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function render() {
  try {
    const [listed, overrides] = await Promise.all([
      fetchJson("./data/plugins.json"),
      fetchJson("./data/overrides.json"),
    ]);
    const plugins = mergePlugins(listed.plugins || listed, overrides);
    grid.innerHTML = "";
    if (!plugins.length) {
      grid.innerHTML = `<p class="empty">No public omarchy-* plugins yet.</p>`;
      countEl.textContent = "";
      return;
    }
    countEl.textContent = `${plugins.length} public repos`;
    const icons = await Promise.all(plugins.map((plugin) => loadIcon(plugin.icon)));
    plugins.forEach((plugin, index) => {
      grid.append(cardTemplate(plugin, icons[index]));
    });
  } catch (error) {
    grid.innerHTML = `<p class="empty">Could not load the plugin list.</p>`;
    console.error(error);
  }
}

initScheme();
render();
