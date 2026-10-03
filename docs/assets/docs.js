// look + color mode switches, shared with the kitchen sink through localStorage
(() => {
  const root = document.documentElement;
  const current = { look: root.dataset.look, theme: root.dataset.bsTheme || "auto" };
  for (const [name, value] of Object.entries(current)) {
    const radio = document.querySelector(`input[name=${name}][value=${value}]`);
    if (radio) radio.checked = true;
  }
  document.querySelectorAll("input[name=look], input[name=theme]").forEach(radio => radio.addEventListener("change", () => {
    const { name, value } = radio;
    if (name === "look") root.dataset.look = value;
    else if (value === "auto") root.removeAttribute("data-bs-theme");
    else root.dataset.bsTheme = value;
    try { localStorage.setItem(name, value); } catch {}
  }));
})();

// highlight the top-level section in the navbar
(() => {
  const area = location.pathname.includes("/examples/") ? "examples" : document.querySelector(".bd-sidebar") ? "docs" : null;
  const link = area && document.querySelector(`[data-bd-nav=${area}]`);
  if (link) { link.classList.add("active"); link.setAttribute("aria-current", "true"); }
})();

// copy buttons on code blocks
document.addEventListener("click", async e => {
  const button = e.target.closest(".bd-copy");
  if (!button) return;
  const code = button.parentElement.querySelector("pre").innerText;
  try {
    await navigator.clipboard.writeText(code);
    button.textContent = "Copied!";
  } catch {
    button.textContent = "Press Ctrl+C";
  }
  setTimeout(() => { button.textContent = "Copy"; }, 1500);
});

// mark the section in view in the sidebar toc
(() => {
  const links = [...document.querySelectorAll(".bd-toc-side a")];
  const targets = links.map(a => document.getElementById(a.hash.slice(1))).filter(Boolean);
  if (!targets.length || !("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(e => e.isIntersecting).map(e => e.target.id);
    if (!visible.length) return;
    links.forEach(a => a.classList.toggle("active", a.hash === `#${visible[0]}`));
  }, { rootMargin: "0px 0px -70% 0px" });
  targets.forEach(t => observer.observe(t));
})();

// example links go nowhere
document.addEventListener("click", e => {
  const link = e.target.closest('.bd-example a[href="#"]');
  if (link) e.preventDefault();
});

// example forms don't submit
document.addEventListener("submit", e => {
  if (e.target.closest(".bd-example")) e.preventDefault();
});

// Bootstrap leaves these to the page: tooltips and popovers are opt-in, toasts are shown from code,
// and a native <dialog class="modal"> opens itself.
(() => {
  if (!window.bootstrap) return;
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
  document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => new bootstrap.Popover(el));
  document.addEventListener("click", e => {
    const toast = e.target.closest("[data-bd-toast]"), dialog = e.target.closest("[data-bd-dialog]");
    if (toast) bootstrap.Toast.getOrCreateInstance(document.querySelector(toast.dataset.bdToast)).show();
    if (dialog) document.querySelector(dialog.dataset.bdDialog).showModal();
    if (e.target.matches("dialog.modal")) e.target.close();
    if (e.target.closest("dialog.modal [data-bs-dismiss=modal]")) e.target.closest("dialog").close();
  });
})();
