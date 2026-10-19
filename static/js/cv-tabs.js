// CV section selector: shows one CV panel at a time. Without this script every panel is
// visible in order. Follows the WAI-ARIA tabs pattern (arrow keys, Home/End) and keeps
// the selected section in the URL hash (e.g. /about/#cv-edu) so it can be linked.
(function () {
  var list = document.querySelector(".cv-tabs");
  if (!list) return;
  var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
  var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute("aria-controls")); });
  list.hidden = false;
  document.documentElement.classList.add("cv-tabbed");

  function select(i, focus, updateHash) {
    tabs.forEach(function (t, j) {
      var on = j === i;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      panels[j].hidden = !on;
    });
    if (focus) tabs[i].focus();
    if (updateHash && history.replaceState) history.replaceState(null, "", "#" + panels[i].id);
  }

  tabs.forEach(function (t, i) {
    t.addEventListener("click", function () { select(i, false, true); });
    t.addEventListener("keydown", function (e) {
      var k = e.key, n = tabs.length, next = null;
      if (k === "ArrowRight") next = (i + 1) % n;
      else if (k === "ArrowLeft") next = (i - 1 + n) % n;
      else if (k === "Home") next = 0;
      else if (k === "End") next = n - 1;
      if (next !== null) { e.preventDefault(); select(next, true, true); }
    });
  });

  var start = panels.findIndex(function (p) { return "#" + p.id === location.hash; });
  select(start >= 0 ? start : 0, false, false);
  if (start >= 0 || location.hash === "#cv") {
    document.getElementById("cv").scrollIntoView();
  }
})();
