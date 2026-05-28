const http = require("http");
const fs = require("fs");
const path = require("path");

const root = __dirname;
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8"
};

const port = Number(process.env.PORT || 4174);

function readBody(req) {
  return new Promise((resolve) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        resolve({});
      }
    });
  });
}

function sendJson(res, payload, status = 200) {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
  });
  res.end(JSON.stringify(payload, null, 2));
}

function cleanDomain(value = "example.com") {
  return String(value)
    .replace(/^https?:\/\//, "")
    .replace(/\/.*$/, "")
    .trim() || "example.com";
}

function linkOnlyReport(domain = "example.com") {
  const clean = cleanDomain(domain);
  return {
    mode: "demo",
    domain: clean,
    generated_at: new Date().toISOString(),
    confidence: {
      score: 64,
      label: "Предварительная оценка",
      explanation: "Отчет построен без подключенных GA4, CRM, рекламных кабинетов и пикселей."
    },
    executive_summary: {
      headline: `Сайт ${clean} может терять заявки из-за слабого измерения, неочевидного CTA и неполной воронки.`,
      client_text: "Даже без интеграций видно, какие зоны могут мешать росту: аналитика, формы, доверие, скорость и путь до заявки.",
      business_risk: "medium",
      estimated_revenue_leak: "35 000-120 000 ₽/мес",
      next_best_action: "Проверить первый экран, форму заявки и подключить базовый трекинг."
    },
    scores: [
      { name: "Готовность к заявкам", score: 64, status: "нужно усилить" },
      { name: "Измеримость маркетинга", score: 38, status: "высокий риск" },
      { name: "SEO-база", score: 71, status: "нормально" },
      { name: "Доверие и оффер", score: 66, status: "есть потенциал" }
    ],
    visible: [
      "структура страницы, формы, CTA и контакты",
      "публичные признаки счетчиков и пикселей",
      "базовые SEO и UX-гипотезы"
    ],
    not_visible: [
      "реальные продажи и выручка без CRM",
      "CPL, ROAS и расходы без рекламных кабинетов",
      "качество лидов без CRM-стадий и звонков"
    ],
    money_leaks: [
      {
        title: "Заявки без источника",
        estimated_loss: "15 000-50 000 ₽/мес",
        fix: "Передавать источник, кампанию, страницу входа и device в CRM."
      },
      {
        title: "Невидимая реклама",
        estimated_loss: "20 000-70 000 ₽/мес",
        fix: "Подключить рекламные кабинеты и UTM/yclid/gclid."
      },
      {
        title: "Потерянные теплые посетители",
        estimated_loss: "10 000-35 000 ₽/мес",
        fix: "Установить Meta Pixel, TikTok Pixel или GTM."
      }
    ],
    today_actions: [
      {
        priority: 1,
        title: "Поставить цель формы и кликов по мессенджерам",
        effect: "+15-30% точности в понимании заявок",
        complexity: "низкая"
      },
      {
        priority: 2,
        title: "Переписать первый экран под конкретное обещание",
        effect: "+5-12% к конверсии первого касания",
        complexity: "средняя"
      },
      {
        priority: 3,
        title: "Добавить UTM-шаблон для рекламы",
        effect: "понятная карта источников после первых кликов",
        complexity: "низкая"
      }
    ],
    required_connections: ["GA4", "Яндекс Метрика", "CRM", "Google Ads", "Яндекс Директ", "Call Tracking", "GTM"]
  };
}

const integrations = [
  ["ga4", "Google Analytics 4", "analytics", "События, аудитории, конверсии и путь пользователя."],
  ["gsc", "Google Search Console", "analytics", "Запросы, показы, клики, CTR и SEO-возможности."],
  ["yandex_metrika", "Яндекс Метрика", "analytics", "Визиты, цели, источники и поведение."],
  ["google_ads", "Google Ads", "ads", "Расходы, кампании, клики, CPL и ROAS."],
  ["yandex_direct", "Яндекс Директ", "ads", "Кампании, расходы, клики, конверсии и CPL."],
  ["meta_ads", "Meta Ads", "ads", "Instagram/Facebook реклама, креативы, расходы и лиды."],
  ["vk", "VK API", "social", "Сообщества, публикации, охваты, вовлеченность и VK-сигналы."],
  ["tiktok_ads", "TikTok Ads", "ads", "Видео, расходы, лиды и эффективность креативов."],
  ["linkedin_ads", "LinkedIn Ads", "ads", "B2B кампании, расходы, лиды и CPL."],
  ["hubspot", "HubSpot", "crm", "Лиды, сделки, стадии и revenue attribution."],
  ["bitrix24", "Bitrix24", "crm", "Лиды, сделки, статусы и причины потерь."],
  ["amocrm", "AmoCRM", "crm", "Воронки, сделки, источники и этапы."],
  ["instagram", "Instagram", "social", "Публикации, охваты, вовлеченность и контент."],
  ["tiktok", "TikTok", "social", "Видео, просмотры, вовлеченность и тренды."],
  ["facebook", "Facebook", "social", "Страницы, посты, охваты и переходы."],
  ["linkedin", "LinkedIn", "social", "B2B публикации и контентные сигналы."],
  ["youtube", "YouTube", "social", "Видео, удержание, источники и идеи контента."],
  ["mailchimp", "Mailchimp", "email", "Email-кампании, аудитории, клики и доход."],
  ["brevo", "Brevo", "email", "Email/SMS кампании, контакты и конверсии."],
  ["klaviyo", "Klaviyo", "email", "Email/SMS, ecommerce-события и revenue attribution."],
  ["meta_pixel", "Meta Pixel", "pixels", "События сайта для ретаргетинга и Meta Ads."],
  ["tiktok_pixel", "TikTok Pixel", "pixels", "События сайта для TikTok Ads."],
  ["gtm", "Google Tag Manager", "pixels", "Единая установка тегов, пикселей и событий."],
  ["call_tracking", "Call Tracking", "calls", "Звонки, источник звонка и связь с CRM."]
].map(([code, title, category, purpose]) => ({
  code,
  title,
  category,
  purpose,
  auth_type: ["pixels"].includes(category) ? "install_snippet" : "demo_connect",
  setup_time: category === "calls" ? "5 минут" : "2-3 минуты",
  status: "available_in_demo"
}));

function growthDemo() {
  return {
    profit_map: {
      channels: [
        { name: "TikTok Ads", revenue: 420000, roi: 2.8, leads: 86 },
        { name: "SEO", revenue: 310000, roi: 5.4, leads: 64 },
        { name: "Яндекс Директ", revenue: 220000, roi: 1.7, leads: 48 },
        { name: "Instagram", revenue: 120000, roi: 1.1, leads: 39 }
      ]
    },
    insights: [
      { severity: "high", title: "Яндекс Директ дает лиды, но ROI ниже SEO", recommendation: "Перенести часть бюджета в кампании с лучшей конверсией." },
      { severity: "medium", title: "TikTok дает быстрый рост заявок", recommendation: "Масштабировать бюджет на 15-20% и держать CPL под контролем." }
    ],
    today_actions: [
      { step: 1, title: "Проверить форму заявки", expected_effect: "+5-12% к конверсии" },
      { step: 2, title: "Подключить CRM-источник", expected_effect: "точный CPL и качество лидов" },
      { step: 3, title: "Перераспределить бюджет", expected_effect: "+12-18% к заявкам" }
    ],
    forecast: { current: 1070000, predicted: 1240000, uplift_percent: 16 }
  };
}

function aiCouncilDemo() {
  return {
    summary: "Главная точка роста - связать заявки с источниками и перераспределить бюджет в каналы с лучшим ROI.",
    main_problem: "Бизнес видит трафик, но не видит, какие каналы реально приносят деньги.",
    evidence: ["SEO показывает высокий ROI", "TikTok масштабируется быстрее Instagram", "часть заявок не имеет источника в CRM"],
    debate: [
      { agent: "GPT Strategist", role: "growth", message: "Сначала нужно увеличить долю каналов с доказанным ROI." },
      { agent: "DeepSeek Analyst", role: "numbers", message: "Без CRM-источника нельзя точно считать CPL и CAC по лидам." },
      { agent: "Grok Challenger", role: "risk", message: "Масштабировать рекламу опасно, пока нет контроля качества лидов." }
    ],
    action_plan: [
      { step: 1, title: "Подключить CRM и цели", why: "иначе заявки нельзя связать с деньгами", how: "передавать UTM, gclid/yclid и форму в CRM", expected_effect: "точная карта прибыли", priority: "high" },
      { step: 2, title: "Проверить форму и первый экран", why: "часть спроса теряется до заявки", how: "сделать один главный CTA и короткий путь до контакта", expected_effect: "+5-12% к конверсии", priority: "high" },
      { step: 3, title: "Перенести бюджет в сильные каналы", why: "часть рекламы дает дорогие лиды", how: "сравнить CPL, ROI и качество лидов", expected_effect: "+12-18% к заявкам", priority: "medium" }
    ],
    confidence: 0.82,
    fallback_models: ["GPT Strategist demo", "DeepSeek Analyst demo", "Grok Challenger demo"]
  };
}

async function handleApi(req, res, pathname, searchParams) {
  if (req.method === "OPTIONS") {
    sendJson(res, { ok: true });
    return true;
  }

  if (pathname === "/health") {
    sendJson(res, { ok: true, service: "TrafficMind AI demo server" });
    return true;
  }

  if (pathname === "/api/reports/link-only-demo") {
    sendJson(res, linkOnlyReport(searchParams.get("domain") || "example.com"));
    return true;
  }

  if (pathname === "/api/growth/demo") {
    sendJson(res, growthDemo());
    return true;
  }

  if (pathname === "/api/ai-council/demo") {
    sendJson(res, aiCouncilDemo());
    return true;
  }

  if (pathname === "/api/integrations") {
    sendJson(res, { integrations });
    return true;
  }

  const setupMatch = pathname.match(/^\/api\/integrations\/([^/]+)\/setup$/);
  if (setupMatch) {
    const item = integrations.find((integration) => integration.code === setupMatch[1]);
    if (!item) {
      sendJson(res, { detail: "Integration not found." }, 404);
      return true;
    }
    sendJson(res, {
      integration: item.code,
      title: item.title,
      auth_type: item.auth_type,
      setup_time: item.setup_time,
      required_env: item.auth_type === "demo_connect" ? [`${item.code.toUpperCase()}_CLIENT_ID`, `${item.code.toUpperCase()}_CLIENT_SECRET`] : [],
      instructions: [
        "В demo-режиме подключение имитируется без внешнего OAuth.",
        "В production нужно создать приложение у провайдера и добавить redirect URI.",
        "После этого TrafficMind сможет получать реальные метрики по этому источнику."
      ]
    });
    return true;
  }

  if (pathname === "/api/account/demo") {
    sendJson(res, {
      profile: { name: "Business owner", telegram_id: "100001", role: "owner", plan: "PRO" },
      websites: [{ domain: "example.com", status: "active", health_score: 82 }],
      subscription: { plan: "PRO", price: 799, max_websites: 3, used_websites: 1, status: "demo" },
      growth: growthDemo(),
      integrations
    });
    return true;
  }

  if (pathname === "/api/account/telegram-link" && req.method === "POST") {
    const body = await readBody(req);
    const code = String(body.link_code || "100001");
    const telegramId = Number(code.replace(/\D/g, "") || 100001);
    sendJson(res, {
      ok: true,
      telegram_id: telegramId,
      username: "demo_owner",
      first_name: "Demo",
      link_status: "linked",
      source: body.source || "web_account",
      account: { settings: { demo: true, linked_at: new Date().toISOString() } }
    });
    return true;
  }

  if (pathname === "/api/account/settings" && req.method === "POST") {
    const body = await readBody(req);
    sendJson(res, {
      ok: true,
      mode: "demo",
      saved_at: new Date().toISOString(),
      settings: body
    });
    return true;
  }

  if (pathname === "/billing/stripe/checkout" && req.method === "POST") {
    sendJson(res, {
      ok: true,
      mode: "demo",
      checkout_url: "/account.html?billing=demo-success",
      session_id: "demo_checkout_session"
    });
    return true;
  }

  return false;
}

http.createServer(async (req, res) => {
  const parsed = new URL(req.url, `http://127.0.0.1:${port}`);
  const pathname = decodeURIComponent(parsed.pathname);

  if (await handleApi(req, res, pathname, parsed.searchParams)) return;

  let urlPath = pathname;
  if (urlPath === "/") urlPath = "/index.html";
  if (urlPath.startsWith("/site/")) urlPath = urlPath.replace(/^\/site/, "") || "/index.html";

  const file = path.normalize(path.join(root, urlPath));
  if (!file.startsWith(root)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.readFile(file, (error, body) => {
    if (error) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    res.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" });
    res.end(body);
  });
}).listen(port, "127.0.0.1", () => {
  console.log(`TrafficMind site: http://127.0.0.1:${port}/`);
  console.log(`TrafficMind account: http://127.0.0.1:${port}/account.html`);
  console.log(`TrafficMind tariffs: http://127.0.0.1:${port}/tariffs.html`);
  console.log(`TrafficMind demo API: http://127.0.0.1:${port}/api/reports/link-only-demo?domain=example.com`);
});
