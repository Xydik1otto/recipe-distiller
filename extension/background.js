// Recipe Distiller — MV3 service worker.
// Clicking the toolbar button on any http(s) page opens the local distiller
// with that page's URL pre-filled (?url=...), so the UI starts extracting
// immediately. "I just wanted a recipe" traffic, stable path.

const DEFAULT_DISTILLER = "http://localhost:8000";

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !/^https?:/i.test(tab.url || "")) return; // ignore chrome:// etc.
  const { distiller } = await chrome.storage.sync.get({ distiller: DEFAULT_DISTILLER });
  const base = String(distiller || DEFAULT_DISTILLER).replace(/\/+$/, "");
  chrome.tabs.create({ url: base + "/?url=" + encodeURIComponent(tab.url) });
});
