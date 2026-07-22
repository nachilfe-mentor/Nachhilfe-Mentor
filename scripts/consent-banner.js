/**
 * Cookie-Consent-Banner für Google Analytics (GA4, G-EJGS7V6113).
 * DSGVO/TDDDG: gtag.js wird erst NACH aktiver Einwilligung geladen
 * (Google Consent Mode v2 als zusätzliche Absicherung).
 * Widerruf jederzeit über den 🍪-Button unten links.
 */
(function () {
  'use strict';

  var GA_ID = 'G-EJGS7V6113';
  var STORAGE_KEY = 'nm-ga-consent'; // 'granted' | 'denied'

  var LANG = (document.documentElement.lang || 'de').slice(0, 2);
  var TEXTS = {
    de: {
      title: 'Cookies für Statistik?',
      body: 'Wir möchten mit Google Analytics verstehen, wie unsere Website genutzt wird. Dabei werden Cookies gesetzt und Daten (z. B. gekürzte IP-Adresse) an Google übertragen. Die Nutzung ist freiwillig – die Website funktioniert auch ohne. Details in der ',
      policy: 'Datenschutzerklärung',
      policyUrl: '/datenschutzerklaerung.html',
      accept: 'Akzeptieren',
      decline: 'Ablehnen',
      settings: 'Cookie-Einstellungen'
    },
    en: {
      title: 'Cookies for statistics?',
      body: 'We would like to use Google Analytics to understand how our website is used. This sets cookies and transfers data (e.g. a truncated IP address) to Google. This is optional – the website works without it. Details in our ',
      policy: 'Privacy Policy',
      policyUrl: '/privacy-policy.html',
      accept: 'Accept',
      decline: 'Decline',
      settings: 'Cookie settings'
    },
    fr: {
      title: 'Cookies statistiques ?',
      body: 'Nous souhaitons utiliser Google Analytics pour comprendre l’utilisation de notre site. Des cookies sont alors déposés et des données (p. ex. adresse IP tronquée) transmises à Google. C’est facultatif – le site fonctionne sans. Détails dans notre ',
      policy: 'Politique de confidentialité',
      policyUrl: '/politique-de-confidentialite.html',
      accept: 'Accepter',
      decline: 'Refuser',
      settings: 'Paramètres des cookies'
    }
  };
  var T = TEXTS[LANG] || TEXTS.de;

  function loadGA() {
    if (window.__nmGaLoaded) return;
    window.__nmGaLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { dataLayer.push(arguments); };
    gtag('consent', 'default', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: 'granted'
    });
    gtag('js', new Date());
    gtag('config', GA_ID);
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
  }

  function css() {
    if (document.getElementById('nm-consent-css')) return;
    var st = document.createElement('style');
    st.id = 'nm-consent-css';
    st.textContent =
      '#nm-consent{position:fixed;left:16px;right:16px;bottom:16px;z-index:99999;max-width:460px;margin:0 auto;' +
      'background:#0d1117;border:1px solid rgba(255,255,255,0.12);border-radius:16px;padding:20px 22px;' +
      'box-shadow:0 18px 50px rgba(0,0,0,0.6);font-family:Inter,-apple-system,sans-serif;color:#f1f5f9;}' +
      '#nm-consent h3{margin:0 0 8px;font-size:16px;font-weight:700;font-family:"Space Grotesk",Inter,sans-serif;}' +
      '#nm-consent p{margin:0 0 16px;font-size:13.5px;line-height:1.6;color:#94a3b8;}' +
      '#nm-consent p a{color:#4facfe;text-decoration:underline;}' +
      '#nm-consent .nm-row{display:flex;gap:10px;flex-wrap:wrap;}' +
      '#nm-consent button{flex:1;min-width:120px;cursor:pointer;font-family:"Space Grotesk",Inter,sans-serif;' +
      'font-size:14px;font-weight:600;padding:11px 18px;border-radius:10px;border:1px solid transparent;}' +
      '#nm-consent .nm-accept{background:linear-gradient(135deg,#4facfe 0%,#8b5cf6 100%);color:#fff;}' +
      '#nm-consent .nm-decline{background:rgba(255,255,255,0.05);border-color:rgba(255,255,255,0.15);color:#f1f5f9;}' +
      '#nm-cookie-chip{position:fixed;left:14px;bottom:14px;z-index:99998;background:#0d1117;' +
      'border:1px solid rgba(255,255,255,0.12);border-radius:999px;width:38px;height:38px;font-size:17px;' +
      'cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,0.45);line-height:1;}' +
      '@media print{#nm-consent,#nm-cookie-chip{display:none!important;}}';
    document.head.appendChild(st);
  }

  function removeBanner() {
    var b = document.getElementById('nm-consent');
    if (b) b.remove();
  }

  function showChip() {
    if (document.getElementById('nm-cookie-chip')) return;
    var c = document.createElement('button');
    c.id = 'nm-cookie-chip';
    c.type = 'button';
    c.title = T.settings;
    c.setAttribute('aria-label', T.settings);
    c.textContent = '🍪';
    c.addEventListener('click', function () { showBanner(); });
    document.body.appendChild(c);
  }

  function decide(value) {
    try { localStorage.setItem(STORAGE_KEY, value); } catch (e) {}
    removeBanner();
    showChip();
    if (value === 'granted') loadGA();
    else if (window.__nmGaLoaded && window.gtag) {
      gtag('consent', 'update', { analytics_storage: 'denied' });
    }
  }

  function showBanner() {
    if (document.getElementById('nm-consent')) return;
    css();
    var b = document.createElement('div');
    b.id = 'nm-consent';
    b.setAttribute('role', 'dialog');
    b.setAttribute('aria-label', T.title);

    var h = document.createElement('h3');
    h.textContent = '🍪 ' + T.title;

    var p = document.createElement('p');
    p.appendChild(document.createTextNode(T.body));
    var a = document.createElement('a');
    a.href = T.policyUrl;
    a.textContent = T.policy;
    p.appendChild(a);
    p.appendChild(document.createTextNode('.'));

    var row = document.createElement('div');
    row.className = 'nm-row';
    var acc = document.createElement('button');
    acc.className = 'nm-accept';
    acc.type = 'button';
    acc.textContent = T.accept;
    acc.addEventListener('click', function () { decide('granted'); });
    var dec = document.createElement('button');
    dec.className = 'nm-decline';
    dec.type = 'button';
    dec.textContent = T.decline;
    dec.addEventListener('click', function () { decide('denied'); });
    row.appendChild(acc);
    row.appendChild(dec);

    b.appendChild(h);
    b.appendChild(p);
    b.appendChild(row);
    document.body.appendChild(b);
  }

  window.openCookieSettings = showBanner;

  function init() {
    var stored = null;
    try { stored = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    if (stored === 'granted') { loadGA(); showChip(); }
    else if (stored === 'denied') { showChip(); }
    else { showBanner(); }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
