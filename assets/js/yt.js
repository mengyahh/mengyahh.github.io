/* YouTube "click to play": the page only shows a local poster image; the player (youtube-nocookie) loads when someone presses play. */
(function () {
  Array.prototype.forEach.call(document.querySelectorAll('button.yt[data-yt]'), function (b) {
    b.addEventListener('click', function () {
      var id = b.getAttribute('data-yt');
      if (!/^[\w-]{6,20}$/.test(id)) return;
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0';
      f.title = b.getAttribute('aria-label') || '影片';
      f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.allowFullscreen = true;
      f.referrerPolicy = 'strict-origin-when-cross-origin';
      b.textContent = '';
      b.appendChild(f);
      b.removeAttribute('aria-label');
      f.focus();
    }, { once: true });
  });
})();
