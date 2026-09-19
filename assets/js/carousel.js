/* Adds prev/next buttons and dots to every .carousel that has 2+ slides. The scroll-snap track works without JS. */
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.querySelectorAll('.carousel').forEach(function (c) {
    var track = c.querySelector('.track');
    var n = track.children.length;
    if (n < 2) return;

    function btn(cls, label, text) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'cb ' + cls;
      b.setAttribute('aria-label', label);
      b.textContent = text;
      return b;
    }
    var prev = btn('prev', '上一張', '‹');
    var next = btn('next', '下一張', '›');
    var dots = document.createElement('div');
    dots.className = 'dots';
    var dotBtns = [];
    for (var i = 0; i < n; i++) {
      (function (k) {
        var d = document.createElement('button');
        d.type = 'button';
        d.setAttribute('aria-label', '第 ' + (k + 1) + ' 張，共 ' + n + ' 張');
        d.addEventListener('click', function () { go(k); });
        dots.appendChild(d);
        dotBtns.push(d);
      })(i);
    }
    c.appendChild(prev);
    c.appendChild(next);
    c.appendChild(dots);

    function current() { return Math.round(track.scrollLeft / track.clientWidth); }
    function go(k) {
      k = Math.max(0, Math.min(n - 1, k));
      track.scrollTo({ left: k * track.clientWidth, behavior: reduce ? 'auto' : 'smooth' });
    }
    function update() {
      var k = current();
      dotBtns.forEach(function (d, j) { d.setAttribute('aria-current', j === k ? 'true' : 'false'); });
      prev.disabled = k <= 0;
      next.disabled = k >= n - 1;
    }
    prev.addEventListener('click', function () { go(current() - 1); });
    next.addEventListener('click', function () { go(current() + 1); });

    var raf;
    track.addEventListener('scroll', function () {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(update);
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  });
})();
