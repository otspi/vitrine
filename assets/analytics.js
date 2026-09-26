/* Mesure d'audience Matomo, configurée pour l'exemption de consentement (recommandations de la CNIL) :
   aucun cookie, respect de la mention « Do Not Track ». L'instance est hébergée chez o2switch (France),
   sous le contrôle de l'éditeur. Voir les mentions légales. */
(function () {
  var base = "https://stats.otspi.org/";
  var _paq = (window._paq = window._paq || []);
  _paq.push(["disableCookies"]);
  _paq.push(["setDoNotTrack", true]);
  _paq.push(["trackPageView"]);
  _paq.push(["enableLinkTracking"]);
  _paq.push(["setTrackerUrl", base + "matomo.php"]);
  _paq.push(["setSiteId", "1"]);
  var script = document.createElement("script");
  script.async = true;
  script.src = base + "matomo.js";
  document.head.appendChild(script);
})();
