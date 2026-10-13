/* "TOP" button: a small floating button that scrolls back to the top; it appears once the page has been scrolled down a bit. */
(function () {
  var lang = (document.documentElement.lang || 'zh').slice(0, 2);
  var label = { en: 'Back to top', ja: 'ページの先頭へ' }[lang] || '回到最上面';

  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'to-top';
  btn.setAttribute('aria-label', label);
  btn.innerHTML = '<svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" ' +
                  'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 7.5 6 4l3.5 3.5"/></svg><span>TOP</span>';
  document.body.appendChild(btn);

  var show = false;
  function update() {                               // cheap: it only reads the scroll position and toggles a class when it changes
    var should = (window.pageYOffset || document.documentElement.scrollTop) > Math.max(480, window.innerHeight * 0.6);
    if (should !== show) {
      show = should;
      btn.classList.toggle('show', show);
    }
  }
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();

  btn.addEventListener('click', function () {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
  });
})();
