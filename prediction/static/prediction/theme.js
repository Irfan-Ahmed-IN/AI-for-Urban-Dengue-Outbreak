(() => {
  let theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  try { theme = localStorage.getItem("dg-theme") || theme; } catch {}
  document.documentElement.dataset.theme = theme;
  addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("theme");
    const label = () => {
      button.textContent = theme === "dark" ? "☀  " + button.dataset.light : "☾  " + button.dataset.dark;
    };
    label();
    button.addEventListener("click", () => {
      theme = theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = theme;
      try { localStorage.setItem("dg-theme", theme); } catch {}
      label();
    });
  });
})();
