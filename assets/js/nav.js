/* "工作" drop-down in the top navigation: click to open, Esc / click elsewhere to close */
(function () {
  var btns = Array.prototype.slice.call(document.querySelectorAll('.topnav .sub-btn'));
  if (!btns.length) return;
  function close(except) {
    btns.forEach(function (b) {
      var sub = document.getElementById(b.getAttribute('aria-controls'));
      if (sub === except) return;
      sub.classList.remove('open');
      b.setAttribute('aria-expanded', 'false');
    });
  }
  btns.forEach(function (b) {
    var sub = document.getElementById(b.getAttribute('aria-controls'));
    b.addEventListener('click', function (e) {
      e.stopPropagation();
      close(sub);
      b.setAttribute('aria-expanded', sub.classList.toggle('open') ? 'true' : 'false');
    });
  });
  document.addEventListener('click', function (e) { if (!e.target.closest('.has-sub')) close(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { close(); if (btns[0]) btns[0].focus(); }
  });
})();
