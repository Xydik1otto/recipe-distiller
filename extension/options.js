const input = document.getElementById("distiller");
const status = document.getElementById("saved");

chrome.storage.sync.get({ distiller: "http://localhost:8000" }, ({ distiller }) => {
  input.value = distiller;
});

document.getElementById("save").onclick = () => {
  chrome.storage.sync.set({ distiller: input.value.trim() || "http://localhost:8000" }, () => {
    status.textContent = "✓ Збережено";
    setTimeout(() => (status.textContent = ""), 2000);
  });
};
