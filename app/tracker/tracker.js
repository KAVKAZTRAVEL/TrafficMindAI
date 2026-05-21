(function () {
  const currentScript = document.currentScript;
  const token = currentScript && currentScript.dataset.token;
  const endpoint = (currentScript && currentScript.dataset.endpoint) || "http://localhost:8000/tracker/event";
  if (!token || window.__trafficMindLoaded) return;
  window.__trafficMindLoaded = true;

  const visitorKey = "trafficmind_visitor_id";
  const visitorId = localStorage.getItem(visitorKey) || crypto.randomUUID();
  localStorage.setItem(visitorKey, visitorId);

  let maxScroll = 0;
  const utm = {};
  new URLSearchParams(location.search).forEach((value, key) => {
    if (key.startsWith("utm_")) utm[key] = value;
  });

  function send(eventType, payload) {
    const body = JSON.stringify({
      token,
      visitor_id: visitorId,
      event_type: eventType,
      event_name: payload.event_name || null,
      url: location.href,
      title: document.title,
      referrer: document.referrer,
      utm,
      scroll_depth: maxScroll,
      time_on_page: Math.round((performance.now() || 0) / 1000),
      payload
    });
    if (navigator.sendBeacon) {
      navigator.sendBeacon(endpoint, new Blob([body], { type: "application/json" }));
      return;
    }
    fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => {});
  }

  send("page_view", { device: /Mobi|Android/i.test(navigator.userAgent) ? "mobile" : "desktop", browser: navigator.userAgent });

  window.addEventListener("scroll", () => {
    const doc = document.documentElement;
    const depth = Math.round(((window.scrollY + window.innerHeight) / Math.max(doc.scrollHeight, 1)) * 100);
    maxScroll = Math.max(maxScroll, Math.min(depth, 100));
  }, { passive: true });

  document.addEventListener("click", (event) => {
    const target = event.target.closest("a,button,input[type=submit]");
    if (!target) return;
    const href = target.href || "";
    const name = target.innerText || target.value || href || target.tagName;
    send("click", { event_name: name.slice(0, 120), href });
  });

  document.addEventListener("submit", (event) => {
    send("form_submit", { event_name: event.target.getAttribute("name") || "form" });
  }, true);

  window.TrafficMind = {
    event: function (name, data) {
      send("custom", Object.assign({ event_name: name }, data || {}));
    }
  };
})();
