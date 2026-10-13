/* Language menu: the list is a native <details>; this only closes it on a click elsewhere, on Escape, or after choosing,
   and keeps it on the screen. Without JavaScript the menu still opens and closes by itself. */
(function () {
  var box = document.querySelector('.lang-switch details');
  if (!box) return;
  var list = box.querySelector('.lang-list');

  function place() {
    list.style.left = ''; list.style.right = '';
    var r = list.getBoundingClientRect();
    if (r.left < 8) { list.style.left = '0'; list.style.right = 'auto'; }
  }
  box.addEventListener('toggle', function () { if (box.open) place(); });
  document.addEventListener('click', function (ev) { if (box.open && !box.contains(ev.target)) box.open = false; });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && box.open) { box.open = false; box.querySelector('summary').focus(); }
  });
})();
