/* Header drop-downs (工作 > AppSheet, and the language menu): open on hover / focus (CSS) and with the button on touch screens. */
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('.topnav .has-sub'));
  if (!items.length) return;

  function reset(li) {
    var sub = li.querySelector('.sub');
    if (sub) { sub.style.left = ''; sub.style.right = ''; }
  }
  function closeAll(except) {
    items.forEach(function (li) {
      if (li === except) return;
      var b = li.querySelector('.sub-btn');
      li.classList.remove('open');
      reset(li);
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  }
  function keepOnScreen(li) {                     // a menu that would run off the screen edge is aligned to its button instead
    var sub = li.querySelector('.sub');
    if (!sub) return;
    reset(li);
    var r = sub.getBoundingClientRect();
    if (r.left < 8) { sub.style.left = '0'; sub.style.right = 'auto'; }
    else if (r.right > window.innerWidth - 8) { sub.style.left = 'auto'; sub.style.right = '0'; }
  }

  items.forEach(function (li) {
    var b = li.querySelector('.sub-btn');
    if (!b) return;
    b.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var open = li.classList.toggle('open');
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
      closeAll(li);
      if (open) keepOnScreen(li);
    });
  });
  document.addEventListener('click', function (ev) { if (!ev.target.closest('.has-sub')) closeAll(); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') closeAll(); });
})();
