// Menu de navigation mobile : bascule accessible, fermeture après sélection ou avec Échap.
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('navigation');
  if (!toggle || !nav) return;

  function setOpen(open) {
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
  }

  toggle.addEventListener('click', function () {
    setOpen(!nav.classList.contains('is-open'));
  });

  nav.addEventListener('click', function (event) {
    if (event.target.closest('a')) setOpen(false);
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && nav.classList.contains('is-open')) {
      setOpen(false);
      toggle.focus();
    }
  });
})();

// Compte à rebours vers une échéance réglementaire (data-countdown="AAAA-MM-JJ").
// Sans JavaScript, la date reste affichée telle quelle.
(function () {
  var DAY = 86400000;
  document.querySelectorAll('[data-countdown]').forEach(function (el) {
    var parts = el.getAttribute('data-countdown').split('-').map(Number);
    var target = Date.UTC(parts[0], parts[1] - 1, parts[2]);
    var now = new Date();
    var today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    var days = Math.round((target - today) / DAY);
    if (days > 0) {
      el.textContent = 'J-' + days;
      el.setAttribute('title', 'Échéance : ' + new Date(target).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }));
    } else {
      el.textContent = 'En vigueur';
    }
  });
})();
