/* Minimal lightbox: any <a class="ph" href="full.webp" data-group="…"> opens in a <dialog>. */
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('a.ph[data-group]'));
  if (!links.length || typeof HTMLDialogElement === 'undefined') return;

  var dlg = document.createElement('dialog');
  dlg.className = 'lb';
  dlg.setAttribute('aria-label', '照片檢視');
  dlg.innerHTML =
    '<div class="lb-inner">' +
    '<img alt="">' +
    '<button type="button" class="x" aria-label="關閉">×</button>' +
    '<button type="button" class="prev" aria-label="上一張">‹</button>' +
    '<button type="button" class="next" aria-label="下一張">›</button>' +
    '<div class="lb-cap" aria-live="polite"></div>' +
    '</div>';
  document.body.appendChild(dlg);

  var img = dlg.querySelector('img');
  var cap = dlg.querySelector('.lb-cap');
  var prev = dlg.querySelector('.prev');
  var next = dlg.querySelector('.next');
  var group = [], idx = 0;

  function show(i) {
    idx = (i + group.length) % group.length;
    var a = group[idx];
    img.src = a.href;
    img.alt = a.getAttribute('data-alt') || '';
    var t = a.getAttribute('data-title') || '';
    cap.textContent = t;
    if (group.length > 1) {
      var n = document.createElement('span');
      n.className = 'mono';
      n.textContent = (idx + 1) + ' / ' + group.length;
      cap.appendChild(n);
    }
    prev.hidden = next.hidden = group.length < 2;
  }

  links.forEach(function (a) {
    a.addEventListener('click', function (ev) {
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button === 1) return; // let "open in new tab" work
      ev.preventDefault();
      var g = a.getAttribute('data-group');
      group = links.filter(function (l) { return l.getAttribute('data-group') === g; });
      dlg.showModal();
      show(group.indexOf(a));
    });
  });

  prev.addEventListener('click', function () { show(idx - 1); });
  next.addEventListener('click', function () { show(idx + 1); });
  dlg.querySelector('.x').addEventListener('click', function () { dlg.close(); });
  dlg.addEventListener('click', function (ev) {
    if (ev.target === dlg || ev.target.classList.contains('lb-inner')) dlg.close();
  });
  dlg.addEventListener('keydown', function (ev) {
    if (ev.key === 'ArrowLeft') { ev.preventDefault(); show(idx - 1); }
    else if (ev.key === 'ArrowRight') { ev.preventDefault(); show(idx + 1); }
  });
  dlg.addEventListener('close', function () { img.removeAttribute('src'); });
})();
