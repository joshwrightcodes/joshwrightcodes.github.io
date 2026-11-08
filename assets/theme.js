(function () {
  var KEY = "theme";
  var root = document.documentElement;

  function readSaved() {
    try {
      var value = localStorage.getItem(KEY);
      return value === "light" || value === "dark" ? value : null;
    } catch (error) {
      return null;
    }
  }

  function save(value) {
    try {
      localStorage.setItem(KEY, value);
    } catch (error) {
      return;
    }
  }

  function currentTheme() {
    if (root.dataset.theme) {
      return root.dataset.theme;
    }
    return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  var saved = readSaved();
  if (saved) {
    root.dataset.theme = saved;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("theme-toggle");
    button.hidden = false;
    button.setAttribute("aria-pressed", String(currentTheme() === "dark"));
    button.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      save(next);
      button.setAttribute("aria-pressed", String(next === "dark"));
    });
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
      button.setAttribute("aria-pressed", String(currentTheme() === "dark"));
    });
  });
})();
