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
  var en = document.documentElement.lang === 'en';
  document.querySelectorAll('[data-countdown]').forEach(function (el) {
    var parts = el.getAttribute('data-countdown').split('-').map(Number);
    var target = Date.UTC(parts[0], parts[1] - 1, parts[2]);
    var now = new Date();
    var today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    var days = Math.round((target - today) / DAY);
    if (days > 0) {
      el.textContent = 'J-' + days;
      el.setAttribute('title', (en ? 'Deadline: ' : 'Échéance : ') + new Date(target).toLocaleDateString(en ? 'en-GB' : 'fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }));
    } else {
      el.textContent = en ? 'In force' : 'En vigueur';
    }
  });
})();

// Partage : partage natif (mobile), copie du message ou du lien, choix de l'instance Mastodon.
(function () {
  function flash(button) {
    var label = button.innerHTML;
    button.classList.add('is-done');
    button.textContent = button.getAttribute('data-copied') || '✓';
    setTimeout(function () {
      button.innerHTML = label;
      button.classList.remove('is-done');
    }, 2000);
  }

  function copy(text, button) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { flash(button); });
    }
  }

  document.querySelectorAll('[data-copy-target]').forEach(function (button) {
    button.addEventListener('click', function () {
      var source = document.getElementById(button.getAttribute('data-copy-target'));
      if (source) copy(source.textContent.trim(), button);
    });
  });

  document.querySelectorAll('[data-copy-text]').forEach(function (button) {
    button.addEventListener('click', function () {
      copy(button.getAttribute('data-copy-text'), button);
    });
  });

  if (navigator.share) {
    document.querySelectorAll('.share-native').forEach(function (button) {
      button.hidden = false;
      button.addEventListener('click', function () {
        navigator.share({
          title: button.getAttribute('data-share-title'),
          text: button.getAttribute('data-share-text'),
          url: button.getAttribute('data-share-url')
        }).catch(function () {});
      });
    });
  }

  var STORAGE_KEY = 'otspi-mastodon-instance';
  document.querySelectorAll('[data-mastodon]').forEach(function (button) {
    var form = document.getElementById(button.getAttribute('aria-controls'));
    if (!form) return;
    var input = form.querySelector('input');
    try { input.value = localStorage.getItem(STORAGE_KEY) || ''; } catch (e) {}

    button.addEventListener('click', function () {
      var open = form.hidden;
      form.hidden = !open;
      button.setAttribute('aria-expanded', String(open));
      if (open) input.focus();
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var instance = input.value.trim().replace(/^https?:\/\//, '').replace(/[\/@].*$/, '');
      if (!/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(instance)) {
        input.focus();
        return;
      }
      try { localStorage.setItem(STORAGE_KEY, instance); } catch (e) {}
      var text = encodeURIComponent(button.getAttribute('data-mastodon'));
      window.open('https://' + instance + '/share?text=' + text, '_blank', 'noopener');
    });
  });
})();
