const OWNER = "paytbidd";
const SELF = "omarchy-plugins";
const SCHEME_KEY = "plugin-scheme";

const COPY_ICON = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 6h12v2H8zM4 2h12v2H4zm2 6h2v12H6zM2 4h2v12H2zm6 16h12v2H8zM20 8h2v12h-2zm-4-4h2v2h-2zM4 16h2v2H4z"/></svg>`;
const CHECK_ICON = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M10 18H8v-2h2v2Zm-2-2H6v-2h2v2Zm4-2v2h-2v-2h2Zm-6 0H4v-2h2v2Zm8 0h-2v-2h2v2Zm2-2h-2v-2h2v2Zm2-2h-2V8h2v2Zm2-2h-2V6h2v2Z"/></svg>`;
const GITHUB_ICON = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/></svg>`;

const grid = document.querySelector("[data-plugin-grid]");
const schemeBtn = document.querySelector("[data-scheme-toggle]");

function systemScheme() {
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyScheme(scheme, persist) {
  const next = scheme === "dark" ? "dark" : "light";
  document.documentElement.dataset.scheme = next;
  if (persist) localStorage.setItem(SCHEME_KEY, next);
  if (schemeBtn) {
    schemeBtn.setAttribute(
      "aria-label",
      next === "dark" ? "Switch to day" : "Switch to night"
    );
  }
}

function initScheme() {
  const stored = localStorage.getItem(SCHEME_KEY);
  applyScheme(stored || systemScheme(), false);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (event) => {
    if (!localStorage.getItem(SCHEME_KEY)) {
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

function rowTemplate(plugin, iconMarkup) {
  const article = document.createElement("article");
  article.className = "row";
  article.innerHTML = `
    <div class="icon" aria-hidden="true">${iconMarkup}</div>
    <div class="body">
      <h2>${escapeHtml(plugin.title)}</h2>
      <p class="one-line">${escapeHtml(plugin.blurb)}</p>
      <div class="cmd">
        <code></code>
        <button class="copy" type="button" aria-label="Copy install command">${COPY_ICON}</button>
      </div>
      <a class="repo" href="${plugin.html_url}">${GITHUB_ICON}<span>${escapeHtml(plugin.name)}</span></a>
    </div>
  `;
  article.querySelector("code").textContent = installCommand(plugin.name);
  const button = article.querySelector(".copy");
  button.addEventListener("click", async () => {
    const command = installCommand(plugin.name);
    try {
      await navigator.clipboard.writeText(command);
      button.innerHTML = CHECK_ICON;
      button.setAttribute("aria-label", "Copied");
    } catch {
      const range = document.createRange();
      range.selectNodeContents(article.querySelector("code"));
      const selection = getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    setTimeout(() => {
      button.innerHTML = COPY_ICON;
      button.setAttribute("aria-label", "Copy install command");
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
      return;
    }
    const icons = await Promise.all(plugins.map((plugin) => loadIcon(plugin.icon)));
    plugins.forEach((plugin, index) => {
      grid.append(rowTemplate(plugin, icons[index]));
    });
  } catch (error) {
    grid.innerHTML = `<p class="empty">Could not load the plugin list.</p>`;
    console.error(error);
  }
}

initScheme();
render();
