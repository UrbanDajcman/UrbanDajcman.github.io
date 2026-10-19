// Collaboration map: highlight a place (hover, focus or tap), and zoom/pan the map.
// Zoom: buttons, double-click, pinch, or Ctrl/Cmd + wheel (plain scrolling keeps
// scrolling the page). Without this script the map shows Europe and the list works.
(function () {
  var root = document.querySelector("[data-collab]");
  if (!root) return;
  var svg = root.querySelector(".collab__svg");
  var targets = root.querySelectorAll("[data-node]");

  // ---- Highlighting -------------------------------------------------------
  function activate(key) {
    root.classList.toggle("is-highlighting", Boolean(key));
    targets.forEach(function (el) {
      el.classList.toggle("is-active", el.getAttribute("data-node") === key);
    });
  }
  // Pop-up beside a point on the map, filled from the matching list entry.
  var mapPop = root.querySelector(".collab__mappop");
  var mapBox = root.querySelector(".collab__map");
  var hideTimer = null;
  function showMapPop(node) {
    clearTimeout(hideTimer);
    var src = root.querySelector("#pop-" + node.getAttribute("data-node"));
    if (!src || !mapPop) return;
    mapPop.innerHTML = src.innerHTML;
    mapPop.hidden = false;
    var dot = node.querySelector(".collab__dot").getBoundingClientRect();
    var box = mapBox.getBoundingClientRect();
    var x = dot.left - box.left + dot.width / 2 + 14;
    var y = dot.top - box.top - 10;
    var w = mapPop.offsetWidth, h = mapPop.offsetHeight;
    if (x + w > box.width - 8) x = dot.left - box.left - w - 14;
    mapPop.style.left = Math.max(8, x) + "px";
    mapPop.style.top = Math.min(Math.max(8, y), box.height - h - 8) + "px";
  }
  function hideMapPop() {
    hideTimer = setTimeout(function () { if (mapPop) mapPop.hidden = true; }, 250);
  }
  if (mapPop) {
    mapPop.addEventListener("mouseenter", function () { clearTimeout(hideTimer); });
    mapPop.addEventListener("mouseleave", hideMapPop);
  }

  root.querySelectorAll(".collab__node, .collab__item").forEach(function (el) {
    var key = el.getAttribute("data-node");
    var isNode = el.classList.contains("collab__node");
    el.addEventListener("mouseenter", function () { activate(key); if (isNode) showMapPop(el); });
    el.addEventListener("mouseleave", function () { activate(null); if (isNode) hideMapPop(); });
    el.addEventListener("focusin", function () { activate(key); });
    el.addEventListener("focusout", function () { activate(null); });
    if (isNode) {
      // Tap on touch screens: show the pop-up (there is no hover).
      el.addEventListener("click", function () { activate(key); showMapPop(el); });
    }
  });

  // ---- Zoom and pan --------------------------------------------------------
  var world = svg.getAttribute("data-world").split(" ").map(Number);
  var start = svg.getAttribute("viewBox").split(" ").map(Number);
  var vb = start.slice();
  var MIN_W = 120, MAX_W = world[0];
  var dots = svg.querySelectorAll("[data-x]");

  function aspect() {
    var r = svg.getBoundingClientRect();
    return r.width && r.height ? r.height / r.width : start[3] / start[2];
  }
  function clamp() {
    vb[2] = Math.min(Math.max(vb[2], MIN_W), MAX_W);
    vb[3] = vb[2] * aspect();
    vb[0] = Math.min(Math.max(vb[0], 0), world[0] - vb[2]);
    if (vb[3] >= world[1]) { vb[1] = (world[1] - vb[3]) / 2; }
    else { vb[1] = Math.min(Math.max(vb[1], 0), world[1] - vb[3]); }
  }
  // Keep dots, labels and halos the same size on screen at every zoom level.
  function rescale() {
    var upp = vb[2] / (svg.getBoundingClientRect().width || 1200);
    dots.forEach(function (g) {
      var x = +g.getAttribute("data-x"), y = +g.getAttribute("data-y"), r = +g.getAttribute("data-r");
      var home = g.classList.contains("collab__home");
      g.querySelectorAll("circle").forEach(function (c) {
        var extra = c.classList.contains("collab__halo") ? 6 : c.classList.contains("collab__home-ring") ? 5 : 0;
        c.setAttribute("r", (r + extra) * upp);
      });
      var t = g.querySelector("text");
      if (t) {
        t.setAttribute("font-size", 13 * upp);
        t.setAttribute("x", x + (r + (home ? 8 : 5)) * upp);
        t.setAttribute("y", home ? y - 8 * upp : y + 4 * upp);
      }
    });
  }
  function apply() {
    if (mapPop) mapPop.hidden = true;
    clamp();
    svg.setAttribute("viewBox", vb.join(" "));
    rescale();
  }
  function zoomAt(factor, cx, cy) {
    // cx, cy: point in map units that stays fixed.
    var w = Math.min(Math.max(vb[2] / factor, MIN_W), MAX_W);
    var f = w / vb[2];
    vb[0] = cx - (cx - vb[0]) * f;
    vb[1] = cy - (cy - vb[1]) * f;
    vb[2] = w;
    apply();
  }
  function toMap(clientX, clientY) {
    var r = svg.getBoundingClientRect();
    return [vb[0] + (clientX - r.left) / r.width * vb[2], vb[1] + (clientY - r.top) / r.height * vb[3]];
  }
  function centre() { return [vb[0] + vb[2] / 2, vb[1] + vb[3] / 2]; }

  var controls = root.querySelector(".collab__controls");
  controls.hidden = false;
  controls.addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b) return;
    var c = centre();
    switch (b.getAttribute("data-zoom")) {
      case "in": zoomAt(1.6, c[0], c[1]); break;
      case "out": zoomAt(1 / 1.6, c[0], c[1]); break;
    }
  });
  svg.addEventListener("wheel", function (e) {
    if (!e.ctrlKey && !e.metaKey) return; // do not hijack page scrolling
    e.preventDefault();
    var p = toMap(e.clientX, e.clientY);
    zoomAt(e.deltaY < 0 ? 1.25 : 0.8, p[0], p[1]);
  }, { passive: false });
  svg.addEventListener("dblclick", function (e) {
    var p = toMap(e.clientX, e.clientY);
    zoomAt(e.shiftKey ? 0.625 : 1.6, p[0], p[1]);
  });

  // Drag to pan; two pointers pinch to zoom.
  var pointers = new Map(), last = null, pinch = null;
  svg.addEventListener("pointerdown", function (e) {
    if (e.target.closest(".collab__node")) return;
    if (mapPop) mapPop.hidden = true;
    svg.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, [e.clientX, e.clientY]);
    last = [e.clientX, e.clientY];
    svg.classList.add("is-dragging");
  });
  svg.addEventListener("pointermove", function (e) {
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, [e.clientX, e.clientY]);
    var r = svg.getBoundingClientRect();
    if (pointers.size === 2) {
      var pts = Array.from(pointers.values());
      var d = Math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]);
      var mid = toMap((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2);
      if (pinch) zoomAt(d / pinch, mid[0], mid[1]);
      pinch = d;
      return;
    }
    if (last) {
      vb[0] -= (e.clientX - last[0]) / r.width * vb[2];
      vb[1] -= (e.clientY - last[1]) / r.height * vb[3];
      last = [e.clientX, e.clientY];
      apply();
    }
  });
  function end(e) {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch = null;
    if (pointers.size === 0) { last = null; svg.classList.remove("is-dragging"); }
    else { last = Array.from(pointers.values())[0]; }
  }
  svg.addEventListener("pointerup", end);
  svg.addEventListener("pointercancel", end);

  window.addEventListener("resize", apply);
  apply();
})();
