const crypto = require("crypto");
const fs = require("fs");
const https = require("https");
const path = require("path");
const querystring = require("querystring");

const runtimeDir = path.join(__dirname, ".runtime");
const dbPath = path.join(runtimeDir, "trafficmind-db.json");
const sessionCookie = "tm_session";
const sessionTtlMs = 1000 * 60 * 60 * 24 * 7;

const integrationCatalog = [
  ["ga4", "Google Analytics 4", "analytics"],
  ["gsc", "Google Search Console", "analytics"],
  ["yandex_metrika", "Яндекс Метрика", "analytics"],
  ["google_ads", "Google Ads", "ads"],
  ["yandex_direct", "Яндекс Директ", "ads"],
  ["meta_ads", "Meta Ads", "ads"],
  ["vk", "VK API", "social"],
  ["tiktok_ads", "TikTok Ads", "ads"],
  ["linkedin_ads", "LinkedIn Ads", "ads"],
  ["hubspot", "HubSpot", "crm"],
  ["bitrix24", "Bitrix24", "crm"],
  ["amocrm", "AmoCRM", "crm"],
  ["instagram", "Instagram", "social"],
  ["tiktok", "TikTok", "social"],
  ["facebook", "Facebook", "social"],
  ["linkedin", "LinkedIn", "social"],
  ["youtube", "YouTube", "social"],
  ["mailchimp", "Mailchimp", "email"],
  ["brevo", "Brevo", "email"],
  ["klaviyo", "Klaviyo", "email"],
  ["meta_pixel", "Meta Pixel", "pixels"],
  ["tiktok_pixel", "TikTok Pixel", "pixels"],
  ["gtm", "Google Tag Manager", "pixels"],
  ["call_tracking", "Call Tracking", "calls"]
];

function ensureRuntime() {
  fs.mkdirSync(runtimeDir, { recursive: true });
  if (!fs.existsSync(dbPath)) {
    writeDb({
      users: [],
      sessions: {},
      settings: {},
      integrations: {},
      telegramCodes: {},
      createdAt: new Date().toISOString()
    });
  }
}

function readDb() {
  ensureRuntime();
  return JSON.parse(fs.readFileSync(dbPath, "utf8"));
}

function writeDb(db) {
  fs.mkdirSync(runtimeDir, { recursive: true });
  fs.writeFileSync(dbPath, JSON.stringify(db, null, 2), "utf8");
}

function json(res, payload, status = 200, extraHeaders = {}) {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    ...extraHeaders
  });
  res.end(JSON.stringify(payload, null, 2));
}

function parseCookies(req) {
  return Object.fromEntries(
    String(req.headers.cookie || "")
      .split(";")
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const index = part.indexOf("=");
        return [part.slice(0, index), decodeURIComponent(part.slice(index + 1))];
      })
  );
}

function cookie(name, value, options = {}) {
  const parts = [`${name}=${encodeURIComponent(value)}`, "Path=/", "HttpOnly", "SameSite=Lax"];
  if (options.maxAge !== undefined) parts.push(`Max-Age=${options.maxAge}`);
  if (process.env.COOKIE_SECURE === "true") parts.push("Secure");
  return parts.join("; ");
}

function normalizeEmail(email) {
  return String(email || "").trim().toLowerCase();
}

function publicUser(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    plan: user.plan || "trial",
    created_at: user.created_at
  };
}

function hashPassword(password, salt = crypto.randomBytes(16).toString("hex")) {
  const hash = crypto.scryptSync(String(password), salt, 64).toString("hex");
  return `${salt}:${hash}`;
}

function verifyPassword(password, stored) {
  const [salt, expected] = String(stored || "").split(":");
  if (!salt || !expected) return false;
  const actual = hashPassword(password, salt).split(":")[1];
  return crypto.timingSafeEqual(Buffer.from(actual, "hex"), Buffer.from(expected, "hex"));
}

function createSession(db, userId) {
  const token = crypto.randomBytes(32).toString("hex");
  db.sessions[token] = {
    userId,
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + sessionTtlMs).toISOString()
  };
  return token;
}

function currentUser(req, db = readDb()) {
  const token = parseCookies(req)[sessionCookie];
  const session = token ? db.sessions[token] : null;
  if (!session || Date.parse(session.expires_at) < Date.now()) return null;
  return db.users.find((user) => user.id === session.userId) || null;
}

function readBody(req) {
  return new Promise((resolve) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) req.destroy();
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

function cleanSettings(body = {}) {
  const allowed = [
    "telegram_id", "website", "business_name", "business_niche", "plan", "goal",
    "report_frequency", "alert_level", "timezone", "onboarding_completed", "preferences"
  ];
  return Object.fromEntries(allowed.map((key) => [key, body[key]]).filter(([, value]) => value !== undefined));
}

function envName(code, suffix) {
  return `${code.toUpperCase()}_${suffix}`;
}

function integrationStatus(code, category, db, userId) {
  const key = `${userId}:${code}`;
  if (db.integrations[key]?.status === "connected") return "connected";
  if (category === "pixels") return "snippet_required";
  if (process.env[envName(code, "CLIENT_ID")] && process.env[envName(code, "CLIENT_SECRET")]) {
    return "ready_to_connect";
  }
  return "credentials_required";
}

function integrationsForUser(db, userId) {
  return integrationCatalog.map(([code, title, category]) => ({
    code,
    title,
    category,
    status: integrationStatus(code, category, db, userId),
    auth_type: category === "pixels" ? "install_snippet" : "oauth",
    setup_time: category === "calls" ? "5 минут" : "2-3 минуты",
    connected_at: db.integrations[`${userId}:${code}`]?.connected_at || null
  }));
}

function stripeRequest(params, secretKey) {
  const payload = querystring.stringify(params);
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: "api.stripe.com",
      path: "/v1/checkout/sessions",
      method: "POST",
      headers: {
        Authorization: `Bearer ${secretKey}`,
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": Buffer.byteLength(payload)
      },
      timeout: 15000
    }, (res) => {
      let data = "";
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        try {
          const parsed = JSON.parse(data);
          if (res.statusCode >= 400) reject(new Error(parsed.error?.message || "Stripe error"));
          else resolve(parsed);
        } catch {
          reject(new Error("Stripe returned an invalid response"));
        }
      });
    });
    req.on("timeout", () => req.destroy(new Error("Stripe timeout")));
    req.on("error", reject);
    req.write(payload);
    req.end();
  });
}

function appendSecurityHeaders(res) {
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  res.setHeader("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
}

async function handleBackendApi(req, res, pathname) {
  if (req.method === "OPTIONS") {
    json(res, { ok: true });
    return true;
  }

  if (pathname === "/api/auth/register" && req.method === "POST") {
    const body = await readBody(req);
    const email = normalizeEmail(body.email);
    const password = String(body.password || "");
    if (!email.includes("@") || password.length < 8) {
      json(res, { ok: false, detail: "Введите email и пароль минимум из 8 символов." }, 400);
      return true;
    }
    const db = readDb();
    if (db.users.some((user) => user.email === email)) {
      json(res, { ok: false, detail: "Аккаунт с таким email уже существует." }, 409);
      return true;
    }
    const user = {
      id: crypto.randomUUID(),
      email,
      name: String(body.name || "Клиент TrafficMind").trim(),
      password_hash: hashPassword(password),
      plan: "trial",
      created_at: new Date().toISOString()
    };
    db.users.push(user);
    const token = createSession(db, user.id);
    writeDb(db);
    json(res, { ok: true, user: publicUser(user), settings: db.settings[user.id] || null }, 201, {
      "Set-Cookie": cookie(sessionCookie, token, { maxAge: Math.floor(sessionTtlMs / 1000) })
    });
    return true;
  }

  if (pathname === "/api/auth/login" && req.method === "POST") {
    const body = await readBody(req);
    const db = readDb();
    const user = db.users.find((item) => item.email === normalizeEmail(body.email));
    if (!user || !verifyPassword(body.password, user.password_hash)) {
      json(res, { ok: false, detail: "Неверный email или пароль." }, 401);
      return true;
    }
    const token = createSession(db, user.id);
    writeDb(db);
    json(res, { ok: true, user: publicUser(user), settings: db.settings[user.id] || null }, 200, {
      "Set-Cookie": cookie(sessionCookie, token, { maxAge: Math.floor(sessionTtlMs / 1000) })
    });
    return true;
  }

  if (pathname === "/api/auth/logout" && req.method === "POST") {
    const db = readDb();
    const token = parseCookies(req)[sessionCookie];
    if (token) delete db.sessions[token];
    writeDb(db);
    json(res, { ok: true }, 200, { "Set-Cookie": cookie(sessionCookie, "", { maxAge: 0 }) });
    return true;
  }

  if (pathname === "/api/auth/me") {
    const db = readDb();
    const user = currentUser(req, db);
    json(res, {
      authenticated: Boolean(user),
      user: user ? publicUser(user) : null,
      settings: user ? db.settings[user.id] || null : null
    });
    return true;
  }

  if (pathname === "/api/account/settings") {
    const db = readDb();
    const user = currentUser(req, db);
    if (!user) {
      json(res, { ok: false, detail: "Сначала войдите в кабинет." }, 401);
      return true;
    }
    if (req.method === "GET") {
      json(res, { ok: true, user: publicUser(user), settings: db.settings[user.id] || null });
      return true;
    }
    if (req.method === "POST") {
      const body = await readBody(req);
      const settings = {
        ...cleanSettings(body),
        updated_at: new Date().toISOString()
      };
      db.settings[user.id] = settings;
      if (settings.plan) user.plan = settings.plan;
      writeDb(db);
      json(res, { ok: true, saved_at: settings.updated_at, settings, user: publicUser(user) });
      return true;
    }
  }

  if (pathname === "/api/account/telegram-code" && req.method === "POST") {
    const db = readDb();
    const user = currentUser(req, db);
    if (!user) {
      json(res, { ok: false, detail: "Сначала войдите в кабинет." }, 401);
      return true;
    }
    const code = String(crypto.randomInt(100000, 999999));
    db.telegramCodes[code] = {
      userId: user.id,
      expires_at: new Date(Date.now() + 1000 * 60 * 10).toISOString()
    };
    writeDb(db);
    json(res, { ok: true, link_code: code, expires_in_minutes: 10 });
    return true;
  }

  if (pathname === "/api/account/telegram-link" && req.method === "POST") {
    const body = await readBody(req);
    const db = readDb();
    const code = String(body.link_code || "").trim();
    const ticket = db.telegramCodes[code];
    const user = ticket ? db.users.find((item) => item.id === ticket.userId) : currentUser(req, db);
    if (!ticket || !user || Date.parse(ticket.expires_at) < Date.now()) {
      json(res, { ok: false, detail: "Код не найден или истек. Сгенерируйте новый код в кабинете." }, 400);
      return true;
    }
    const telegramId = String(body.telegram_id || body.telegramId || "").replace(/\D/g, "");
    db.settings[user.id] = {
      ...(db.settings[user.id] || {}),
      telegram_id: telegramId || null,
      telegram_linked_at: new Date().toISOString()
    };
    delete db.telegramCodes[code];
    writeDb(db);
    json(res, { ok: true, user: publicUser(user), settings: db.settings[user.id] });
    return true;
  }

  if (pathname === "/api/integrations") {
    const db = readDb();
    const user = currentUser(req, db);
    json(res, { integrations: integrationsForUser(db, user?.id || "anonymous") });
    return true;
  }

  const setupMatch = pathname.match(/^\/api\/integrations\/([^/]+)\/setup$/);
  if (setupMatch) {
    const db = readDb();
    const user = currentUser(req, db);
    if (!user) {
      json(res, { ok: false, detail: "Сначала войдите в кабинет." }, 401);
      return true;
    }
    const item = integrationCatalog.find(([code]) => code === setupMatch[1]);
    if (!item) {
      json(res, { ok: false, detail: "Интеграция не найдена." }, 404);
      return true;
    }
    const [code, title, category] = item;
    if (category === "pixels") {
      json(res, {
        ok: true,
        integration: code,
        title,
        status: "snippet_required",
        snippet: `<!-- TrafficMind ${title}: добавьте реальный код пикселя из кабинета провайдера -->`
      });
      return true;
    }
    const clientId = process.env[envName(code, "CLIENT_ID")];
    const clientSecret = process.env[envName(code, "CLIENT_SECRET")];
    if (!clientId || !clientSecret) {
      json(res, {
        ok: false,
        status: "credentials_required",
        integration: code,
        title,
        required_env: [envName(code, "CLIENT_ID"), envName(code, "CLIENT_SECRET")],
        detail: "Для реального OAuth нужно создать приложение у провайдера и добавить ключи в env."
      }, 503);
      return true;
    }
    json(res, {
      ok: true,
      status: "ready_to_connect",
      integration: code,
      title,
      detail: "Ключи найдены. Следующий шаг - добавить provider-specific OAuth URL и callback."
    });
    return true;
  }

  if (pathname === "/billing/stripe/checkout" && req.method === "POST") {
    const db = readDb();
    const user = currentUser(req, db);
    if (!user) {
      json(res, { ok: false, detail: "Сначала войдите в кабинет." }, 401);
      return true;
    }
    const secretKey = process.env.STRIPE_SECRET_KEY;
    const priceId = process.env.STRIPE_PRICE_PRO_399;
    const siteUrl = process.env.PUBLIC_SITE_URL || `http://127.0.0.1:${process.env.PORT || 4174}`;
    if (!secretKey || !priceId) {
      json(res, {
        ok: false,
        status: "stripe_not_configured",
        required_env: ["STRIPE_SECRET_KEY", "STRIPE_PRICE_PRO_399", "PUBLIC_SITE_URL"],
        detail: "Оплата не имитируется. Добавьте Stripe ключи, чтобы создать настоящую checkout-сессию."
      }, 503);
      return true;
    }
    try {
      const session = await stripeRequest({
        mode: "subscription",
        "line_items[0][price]": priceId,
        "line_items[0][quantity]": 1,
        customer_email: user.email,
        success_url: `${siteUrl}/account.html?billing=success`,
        cancel_url: `${siteUrl}/tariffs.html?billing=cancelled`,
        "metadata[user_id]": user.id
      }, secretKey);
      json(res, { ok: true, checkout_url: session.url, session_id: session.id });
    } catch (error) {
      json(res, { ok: false, detail: error.message }, 502);
    }
    return true;
  }

  return false;
}

module.exports = {
  appendSecurityHeaders,
  handleBackendApi
};
