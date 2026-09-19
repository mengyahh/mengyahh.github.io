/* Series filter for the blog index. Without JS the full list is shown and the chips stay hidden. */
(function () {
  var box = document.querySelector('.filters');
  if (!box) return;
  var chips = Array.prototype.slice.call(box.querySelectorAll('.fchip'));
  var rows = Array.prototype.slice.call(document.querySelectorAll('.post-row'));
  var years = Array.prototype.slice.call(document.querySelectorAll('.year[data-year]'));
  box.hidden = false;

  function apply(series) {
    rows.forEach(function (r) { r.hidden = !!series && r.getAttribute('data-series') !== series; });
    years.forEach(function (y) {
      var any = y.querySelector('.post-row:not([hidden])');
      y.hidden = !any;
      var n = y.querySelectorAll('.post-row:not([hidden])').length;
      var small = y.querySelector('h2 small');
      if (small) small.textContent = n + ' 篇';
    });
    chips.forEach(function (c) { c.setAttribute('aria-pressed', c.getAttribute('data-series') === series ? 'true' : 'false'); });
  }
  chips.forEach(function (c) {
    c.addEventListener('click', function () { apply(c.getAttribute('data-series')); });
  });
})();
