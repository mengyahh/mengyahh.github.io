/* "近期留言" widget in the blog index sidebar. Stays hidden if the comments API is unreachable or has nothing to show. */
(function () {
  var box = document.querySelector('.rc-widget');
  if (!box || !window.fetch) return;
  var api = (box.getAttribute('data-api') || '').replace(/\/+$/, '');
  if (!api) return;

  var titles = {};
  Array.prototype.forEach.call(document.querySelectorAll('.post-row'), function (r) {
    var h = r.querySelector('h3');
    titles[r.getAttribute('data-slug')] = h ? h.textContent : '';
  });

  fetch(api + '/comments/recent')
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (d) {
      var list = box.querySelector('.rc-list');
      var n = 0;
      (d.comments || []).forEach(function (c) {
        var m = /^\/blog\/(\d{4}-\d{2}-\d{2})\/$/.exec(c.page || '');
        if (!m || !titles[m[1]]) return;                       // the article may have been removed
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = m[1] + '/#c-' + c.id;
        var who = document.createElement('span');
        who.className = 'rc-who';
        who.textContent = c.name;
        var on = document.createElement('span');
        on.className = 'rc-on';
        on.textContent = ' 於〈' + titles[m[1]] + '〉';
        var text = document.createElement('span');
        text.className = 'rc-text';
        text.textContent = c.snippet;
        a.appendChild(who);
        a.appendChild(on);
        a.appendChild(text);
        li.appendChild(a);
        list.appendChild(li);
        n++;
      });
      if (n) box.hidden = false;
    })
    .catch(function () { /* keep the widget hidden */ });
})();
