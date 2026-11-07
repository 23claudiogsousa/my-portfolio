/* Claudio Sousa — portfolio behaviour */
(function () {
  "use strict";

  var root = document.documentElement;
  var header = document.querySelector(".site-header");
  var nav = document.getElementById("nav");
  var menuToggle = document.getElementById("menuToggle");
  var themeToggle = document.getElementById("themeToggle");
  var toast = document.getElementById("toast");
  var copyButton = document.querySelector(".copy-btn");
  var themeMeta = document.querySelector('meta[name="theme-color"]');
  var toastTimer = null;

  function t(key) {
    return window.portfolioI18n ? window.portfolioI18n.t(key) : "";
  }

  function currentTheme() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function updateThemeLabel() {
    if (!themeToggle) return;
    var dark = currentTheme() === "dark";
    var label = t(dark ? "themeToLight" : "themeToDark");
    if (!label) label = dark ? "Ativar modo claro" : "Ativar modo escuro";
    themeToggle.setAttribute("aria-label", label);
    themeToggle.setAttribute("title", label);
  }

  function setTheme(theme, persist) {
    root.setAttribute("data-theme", theme);
    if (themeMeta) {
      themeMeta.setAttribute("content", theme === "dark" ? "#14120F" : "#F6F2E8");
    }
    updateThemeLabel();
    if (persist) {
      try { window.localStorage.setItem("portfolio-theme", theme); } catch (error) {}
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      setTheme(currentTheme() === "dark" ? "light" : "dark", true);
    });
  }

  setTheme(currentTheme(), false);

  var systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
  if (systemTheme.addEventListener) {
    systemTheme.addEventListener("change", function (event) {
      var saved = null;
      try { saved = window.localStorage.getItem("portfolio-theme"); } catch (error) {}
      if (!saved) setTheme(event.matches ? "dark" : "light", false);
    });
  }

  function menuIsOpen() {
    return !!(nav && nav.classList.contains("is-open"));
  }

  function setMenu(open) {
    if (!nav || !menuToggle) return;
    nav.classList.toggle("is-open", open);
    menuToggle.classList.toggle("is-open", open);
    document.body.classList.toggle("menu-open", open);
    menuToggle.setAttribute("aria-expanded", String(open));
    menuToggle.setAttribute("aria-label", open ? t("menuClose") : t("menuOpen"));
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", function () {
      setMenu(!menuIsOpen());
    });
  }

  if (nav) {
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () { setMenu(false); });
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && menuIsOpen()) setMenu(false);
  });

  document.addEventListener("click", function (event) {
    if (!menuIsOpen()) return;
    if (nav && nav.contains(event.target)) return;
    if (menuToggle && menuToggle.contains(event.target)) return;
    setMenu(false);
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth > 1024 && menuIsOpen()) setMenu(false);
  });

  function showToast(message) {
    if (!toast || !message) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () {
      toast.classList.remove("is-visible");
    }, 2400);
  }

  function fallbackCopy(text) {
    var field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.top = "-1000px";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    var copied = false;
    try { copied = document.execCommand("copy"); } catch (error) { copied = false; }
    document.body.removeChild(field);
    return copied;
  }

  if (copyButton) {
    copyButton.addEventListener("click", function () {
      var email = copyButton.getAttribute("data-copy") || "";
      function done(copied) {
        showToast(t(copied ? "emailCopied" : "copyError"));
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(email).then(function () { done(true); }, function () { done(fallbackCopy(email)); });
      } else {
        done(fallbackCopy(email));
      }
    });
  }

  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".nav a"));
  var sections = navLinks.map(function (link) {
    var id = link.getAttribute("href");
    return id && id.charAt(0) === "#" ? document.querySelector(id) : null;
  });

  function updateActiveNav() {
    var offset = (header ? header.offsetHeight : 0) + 160;
    var active = -1;
    sections.forEach(function (section, index) {
      if (section && section.getBoundingClientRect().top <= offset) active = index;
    });
    navLinks.forEach(function (link, index) {
      var isActive = index === active;
      link.classList.toggle("is-active", isActive);
      if (isActive) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  }

  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      var y = window.scrollY || window.pageYOffset;
      if (header) header.classList.toggle("is-scrolled", y > 12);
      updateActiveNav();
      ticking = false;
    });
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  document.addEventListener("languagechange", function () {
    updateThemeLabel();
    if (menuToggle) {
      menuToggle.setAttribute("aria-label", menuIsOpen() ? t("menuClose") : t("menuOpen"));
    }
  });
})();
