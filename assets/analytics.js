/* Mesure d'audience Matomo Tag Manager (conteneur GR7y5y3d), configurée pour l'exemption de consentement
   (recommandations de la CNIL) : aucun cookie, respect de la mention « Do Not Track ». Ces réglages sont
   portés par la variable « Matomo Configuration » du conteneur. L'instance est hébergée chez o2switch
   (France), sous le contrôle de l'éditeur. Chargé depuis un fichier, sans script en ligne, pour respecter
   la politique de sécurité du contenu. Voir les mentions légales.

   Le conteneur mesure les pages vues, les liens sortants et les téléchargements. Ce fichier y ajoute des
   événements anonymes sur l'usage des pages (catégorie, action, nom) : aucun texte saisi, aucune donnée
   personnelle. Après toute modification, incrémenter le paramètre ?v= dans les pages. */
(function () {
  var _mtm = (window._mtm = window._mtm || []);
  _mtm.push({ "mtm.startTime": new Date().getTime(), event: "mtm.Start" });
  var script = document.createElement("script");
  script.async = true;
  script.src = "https://stats.otspi.org/js/container_GR7y5y3d.js";
  script.onload = function () {
    var matomo = window.Matomo;
    if (!matomo) return;
    if (matomo.getAsyncTrackers().length) ready(matomo.getAsyncTrackers()[0]);
    else matomo.on("TrackerAdded", ready);
  };
  document.head.appendChild(script);

  // Le traceur est créé par le conteneur. Pas de file _paq : remplie avant le conteneur, elle créerait
  // un second traceur sans adresse de collecte. Les événements attendent le traceur ; s'il est bloqué,
  // ils ne partent jamais.
  var tracker = null;
  var pending = [];

  function ready(created) {
    // Laisse la balise du conteneur envoyer la page vue avant les événements.
    setTimeout(function () {
      tracker = created;
      // Temps passé plus juste sur la dernière page de la visite.
      tracker.enableHeartBeatTimer(15);
      pending.forEach(function (event) { tracker.trackEvent.apply(tracker, event); });
      pending = [];
    }, 0);
  }

  function track(category, action, name) {
    if (tracker) tracker.trackEvent(category, action, name);
    else pending.push([category, action, name]);
  }

  // Emplacement d'un élément : menu, pied de page ou section de la page.
  function zone(el) {
    if (el.closest("header, nav")) return "menu";
    if (el.closest("footer")) return "pied de page";
    var section = el.closest("section[id]");
    return section ? section.id : "page";
  }

  var SHARE = {
    "www.linkedin.com": "LinkedIn", "x.com": "X", "www.facebook.com": "Facebook",
    "bsky.app": "Bluesky", "wa.me": "WhatsApp"
  };

  // Clics sur les liens qui comptent : signature, livre blanc, consultation, partage.
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a[href]");
    if (!link) return;
    var url;
    try { url = new URL(link.href); } catch (e) { return; }
    var where = zone(link);

    if (url.hostname === "manifesto-sign.otspi.org") {
      track("Manifeste", "Ouvrir le formulaire", where);
    } else if (url.hostname === location.hostname && /^\/(en\/)?manifest[eo]/.test(url.pathname)
               && url.pathname !== location.pathname) {
      track("Manifeste", "Aller au manifeste", where);
    } else if (url.hostname === location.hostname && /^#(signer|sign)$/.test(url.hash)) {
      track("Manifeste", "Aller à la signature", where);
    } else if (url.hostname === "about.otspi.org" && /^\/(livre-blanc|white-paper)\//.test(url.pathname)) {
      var pdf = /\.pdf$/.test(url.pathname);
      track("Livre blanc", pdf ? "PDF" : "Web", pdf ? where : (url.hash ? url.hash.slice(1) : "sommaire"));
    } else if (url.hostname === "github.com" && /\/discussions/.test(url.pathname)) {
      track("Consultation", "Commenter", where);
    } else if (SHARE[url.hostname]) {
      track("Partage", SHARE[url.hostname], where);
    }
  });

  // Boutons de partage et de copie (voir script.js).
  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("button");
    if (!button) return;
    var where = zone(button);
    if (button.hasAttribute("data-mastodon")) track("Partage", "Mastodon", where);
    else if (button.classList.contains("share-native")) track("Partage", "Partage natif", where);
    else if (button.hasAttribute("data-copy-text")) track("Partage", "Copier le lien", where);
    else if (button.hasAttribute("data-copy-target")) track("Copie", button.getAttribute("data-copy-target"), where);
  });

  // Questions de la FAQ ouvertes (l'événement toggle ne remonte pas : écoute en capture).
  document.addEventListener("toggle", function (event) {
    var details = event.target;
    if (!details.matches || !details.matches("details.faq-item") || !details.open) return;
    var summary = details.querySelector("summary");
    track("FAQ", "Ouvrir", summary ? summary.textContent.trim() : "");
  }, true);

  // Sections lues : une fois par page, quand la moitié de la section est visible ou, pour une section
  // plus haute que l'écran, quand elle en occupe la moitié.
  if ("IntersectionObserver" in window) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.intersectionRatio < 0.5 && entry.intersectionRect.height < window.innerHeight / 2) return;
        seen.unobserve(entry.target);
        track("Lecture", "Section vue", entry.target.id);
      });
    }, { threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5] });
    document.addEventListener("DOMContentLoaded", function () {
      document.querySelectorAll("main section[id]").forEach(function (section) {
        seen.observe(section);
      });
    });
  }

  // Profondeur de lecture : 25, 50, 75 et 100 % de la page, une fois chacun.
  var steps = [25, 50, 75, 100];
  var ticking = false;
  function depth() {
    ticking = false;
    var doc = document.documentElement;
    var scrollable = doc.scrollHeight - window.innerHeight;
    var percent = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 100;
    while (steps.length && percent >= steps[0] - 1) {
      track("Lecture", "Profondeur", steps.shift() + " %");
    }
    if (!steps.length) window.removeEventListener("scroll", onScroll);
  }
  function onScroll() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(depth); }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
})();
