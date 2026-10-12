/* Header drop-down (工作 > AppSheet): opens on hover / focus (CSS), and with the ▾ button on touch screens. */
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('.topnav .has-sub'));
  if (!items.length) return;
  function closeAll(except) {
    items.forEach(function (li) {
      if (li === except) return;
      var b = li.querySelector('.sub-btn');
      li.classList.remove('open');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  }
  items.forEach(function (li) {
    var b = li.querySelector('.sub-btn');
    if (!b) return;
    b.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var open = li.classList.toggle('open');
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
      closeAll(li);
    });
  });
  document.addEventListener('click', function (ev) { if (!ev.target.closest('.has-sub')) closeAll(); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') closeAll(); });
})();
