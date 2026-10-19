// Plays the optional hero video unless the visitor prefers reduced motion,
// and provides a pause/play control (WCAG 2.2.2). Without JS the still image shows.
(function () {
  var hero = document.querySelector(".hero");
  var video = hero && hero.querySelector(".hero__video");
  var button = hero && hero.querySelector(".hero__toggle");
  if (!video || !button) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  function setLabel() {
    button.textContent = video.paused ? "Play video" : "Pause video";
  }
  video.preload = "auto";
  video.play().then(function () {
    hero.classList.add("hero--playing");
    button.hidden = false;
    setLabel();
  }).catch(function () { /* autoplay blocked: keep the still image */ });
  button.addEventListener("click", function () {
    if (video.paused) { video.play(); } else { video.pause(); }
    setLabel();
  });
})();
