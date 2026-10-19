// "In the field" gallery: click and drag with the mouse to scroll sideways.
// Touch swiping, trackpads, shift + wheel and the keyboard (the strip is focusable)
// use the browser's native scrolling.
(function () {
  var scroller = document.querySelector(".field__scroller");
  if (!scroller) return;
  var startX = 0, startScroll = 0, dragging = false, moved = false;

  scroller.addEventListener("pointerdown", function (e) {
    if (e.pointerType !== "mouse" || e.button !== 0) return;
    dragging = true;
    moved = false;
    startX = e.clientX;
    startScroll = scroller.scrollLeft;
    scroller.setPointerCapture(e.pointerId);
    scroller.classList.add("is-dragging");
  });
  scroller.addEventListener("pointermove", function (e) {
    if (!dragging) return;
    var dx = e.clientX - startX;
    if (Math.abs(dx) > 3) moved = true;
    scroller.scrollLeft = startScroll - dx;
  });
  function end(e) {
    if (!dragging) return;
    dragging = false;
    scroller.classList.remove("is-dragging");
    if (scroller.hasPointerCapture(e.pointerId)) scroller.releasePointerCapture(e.pointerId);
  }
  scroller.addEventListener("pointerup", end);
  scroller.addEventListener("pointercancel", end);
  // Stop the browser's own image drag, and swallow the click that ends a drag.
  scroller.addEventListener("dragstart", function (e) { e.preventDefault(); });
  scroller.addEventListener("click", function (e) { if (moved) { e.preventDefault(); e.stopPropagation(); } }, true);
})();
