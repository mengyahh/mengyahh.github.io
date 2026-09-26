/* Shows the GoatCounter visit count for the current page (needs "Allow adding visitor counts" enabled in GoatCounter). */
(function () {
  var el = document.querySelector('.views[data-code]');
  if (!el || !window.fetch) return;
  var url = 'https://' + el.getAttribute('data-code') + '.goatcounter.com/counter/' +
            encodeURIComponent(location.pathname) + '.json';
  fetch(url).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (d && d.count) {
      el.textContent = (el.getAttribute('data-tpl') || '瀏覽 {n} 次').replace('{n}', d.count);
      el.hidden = false;
    }
  }).catch(function () {});
})();
