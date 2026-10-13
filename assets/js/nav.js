/* Language menu in the header: a button that opens a small list; closes on a click elsewhere, on Escape, or after choosing. */
(function () {
  var box = document.querySelector('.lang-switch');
  if (!box) return;
  var btn = box.querySelector('.lang-toggle');
  var list = box.querySelector('.lang-list');
  if (!btn || !list) return;
  box.classList.add('js');

  function place() {                               // keep the list on the screen
    list.style.left = ''; list.style.right = '';
    var r = list.getBoundingClientRect();
    if (r.left < 8) { list.style.left = '0'; list.style.right = 'auto'; }
    else if (r.right > window.innerWidth - 8) { list.style.left = 'auto'; list.style.right = '0'; }
  }
  function setOpen(open, returnFocus) {
    box.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) place();
    if (!open && returnFocus) btn.focus();
  }
  btn.addEventListener('click', function (ev) {
    ev.stopPropagation();
    setOpen(!box.classList.contains('open'));
  });
  document.addEventListener('click', function (ev) { if (!box.contains(ev.target)) setOpen(false); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && box.classList.contains('open')) setOpen(false, true); });
  window.addEventListener('resize', function () { if (box.classList.contains('open')) place(); });
})();
