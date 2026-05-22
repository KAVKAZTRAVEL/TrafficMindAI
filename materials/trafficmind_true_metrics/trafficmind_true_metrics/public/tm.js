(function () {
  var script = document.currentScript || {};
  var endpoint = script.getAttribute && script.getAttribute('data-endpoint') || '/collect';
  var projectId = script.getAttribute && script.getAttribute('data-project') || 'default';
  var siteId = script.getAttribute && script.getAttribute('data-site') || location.hostname;

  function id(key) {
    try {
      var existing = localStorage.getItem(key);
      if (existing) return existing;
      var created = (crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + '-' + Math.random();
      localStorage.setItem(key, created);
      return created;
    } catch (_) {
      return String(Date.now()) + '-' + Math.random();
    }
  }

  function sessionId() {
    var key = 'tm_session_id';
    var now = Date.now();
    try {
      var raw = sessionStorage.getItem(key);
      if (raw) return raw;
      var created = String(now) + '-' + Math.random().toString(16).slice(2);
      sessionStorage.setItem(key, created);
      return created;
    } catch (_) {
      return String(now);
    }
  }

  function utm() {
    var p = new URLSearchParams(location.search);
    return {
      source: p.get('utm_source') || '',
      medium: p.get('utm_medium') || '',
      campaign: p.get('utm_campaign') || '',
      content: p.get('utm_content') || '',
      term: p.get('utm_term') || ''
    };
  }

  function send(event, properties) {
    var payload = {
      event: event,
      projectId: projectId,
      siteId: siteId,
      visitorId: id('tm_visitor_id'),
      sessionId: sessionId(),
      url: location.href,
      path: location.pathname,
      title: document.title,
      referrer: document.referrer,
      utm: utm(),
      properties: properties || {},
      source: 'browser'
    };

    try {
      var body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        navigator.sendBeacon(endpoint, new Blob([body], { type: 'application/json' }));
      } else {
        fetch(endpoint, { method: 'POST', headers: { 'content-type': 'application/json' }, body: body, keepalive: true });
      }
    } catch (_) {}
  }

  send('pageview', { screen: screen.width + 'x' + screen.height, language: navigator.language });

  var maxScroll = 0;
  window.addEventListener('scroll', function () {
    var doc = document.documentElement;
    var height = Math.max(doc.scrollHeight - window.innerHeight, 1);
    var pct = Math.round((window.scrollY / height) * 100);
    if (pct > maxScroll && pct % 25 === 0) {
      maxScroll = pct;
      send('scroll_depth', { percent: pct });
    }
  }, { passive: true });

  document.addEventListener('click', function (e) {
    var target = e.target && e.target.closest && e.target.closest('a,button,[data-track]');
    if (!target) return;
    send('click', {
      text: (target.innerText || target.getAttribute('aria-label') || '').slice(0, 120),
      href: target.href || '',
      tag: target.tagName
    });
  }, true);

  window.TrafficMindMetrics = { track: send };
})();
