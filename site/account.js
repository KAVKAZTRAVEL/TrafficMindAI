const loginForm = document.querySelector("#login-form");
const settingsForm = document.querySelector("#settings-form");
const loginStatus = document.querySelector("#login-status");
const saveStatus = document.querySelector("#save-status");
const siteStat = document.querySelector("#site-stat");
const syncStat = document.querySelector("#sync-stat");
const planInput = settingsForm.elements.plan;

let currentAccount = null;

const planOrder = { trial: 0, pro399: 1, ai_future: 2 };
const planCopy = {
  trial: {
    title: "Активен бесплатный тариф",
    text: "Можно бесплатно проверить сайт 1 раз в 7 дней и увидеть первые риски по открытым данным. Подключения GA4, рекламы, CRM, звонков, пикселей и расширенных метрик доступны на платном тарифе за 399 ₽."
  },
  pro399: {
    title: "Активен платный тариф за 399 ₽",
    text: "Открыты все доступные источники данных, расширенные метрики, AI Growth Council, модуль потерь денег, CRM, звонки, email, пиксели, алерты владельца и мониторинг до 3 конкурентов."
  },
  ai_future: {
    title: "AI Intelligence в разработке",
    text: "Будущий уровень с собственной AI-системой анализа: прогнозы, поиск скрытых закономерностей, сценарии роста и стратегические рекомендации. Сейчас базой остается платный тариф за 399 ₽."
  }
};
const featurePlans = {
  link_report: "trial",
  saved_account: "trial",
  ai_actions: "trial",
  money_loss: "pro399",
  deep_sources: "pro399",
  competitors: "pro399"
};

const planAllows = (currentPlan, requiredPlan = "trial") => planOrder[currentPlan] >= planOrder[requiredPlan];

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Запрос не выполнен.");
  return payload;
}

const closeAllSelects = () => {
  document.querySelectorAll(".select-shell.open").forEach((shell) => {
    shell.classList.remove("open");
    shell.querySelector(".custom-select-button")?.setAttribute("aria-expanded", "false");
  });
};

function enhanceSelects() {
  document.querySelectorAll("select").forEach((select) => {
    if (select.dataset.enhanced === "true") return;
    select.dataset.enhanced = "true";
    select.classList.add("select-native");

    const shell = document.createElement("div");
    shell.className = "select-shell";
    select.parentNode.insertBefore(shell, select);
    shell.appendChild(select);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "custom-select-button";
    button.setAttribute("aria-expanded", "false");
    button.innerHTML = '<span class="custom-select-value"></span><svg class="custom-select-arrow" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const menu = document.createElement("div");
    menu.className = "custom-select-menu";
    menu.setAttribute("role", "listbox");
    const label = button.querySelector(".custom-select-value");

    const updateLabel = () => {
      const selected = select.options[select.selectedIndex];
      label.textContent = selected ? selected.textContent : "Выберите";
      menu.querySelectorAll(".custom-select-option").forEach((item) => {
        item.classList.toggle("active", item.dataset.value === select.value);
        const sourceOption = [...select.options].find((option) => option.value === item.dataset.value);
        item.classList.toggle("is-disabled", Boolean(sourceOption?.disabled));
      });
    };

    function addOption(option) {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "custom-select-option";
      item.dataset.value = option.value;
      if (option.dataset.minPlan) item.dataset.minPlan = option.dataset.minPlan;
      item.textContent = option.textContent;
      item.addEventListener("click", () => {
        if (option.disabled) return;
        select.value = option.value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
        updateLabel();
        closeAllSelects();
      });
      menu.appendChild(item);
    }

    [...select.children].forEach((child) => {
      if (child.tagName === "OPTGROUP") {
        const group = document.createElement("div");
        group.className = "custom-select-group";
        group.textContent = child.label;
        menu.appendChild(group);
        [...child.children].forEach((option) => addOption(option));
      } else if (child.tagName === "OPTION") {
        addOption(child);
      }
    });

    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const shouldOpen = !shell.classList.contains("open");
      closeAllSelects();
      shell.classList.toggle("open", shouldOpen);
      button.setAttribute("aria-expanded", String(shouldOpen));
    });

    select.addEventListener("change", updateLabel);
    shell.appendChild(button);
    shell.appendChild(menu);
    updateLabel();
  });
}

function setControlValue(name, value) {
  const field = settingsForm.elements[name];
  if (!field || value === undefined || value === null) return;
  if (field.type === "checkbox") field.checked = Boolean(value);
  else field.value = value;
}

function applySettings(saved = {}) {
  const prefs = saved.preferences || {};
  const merged = {
    ...saved,
    ...prefs,
    notify_money_loss: prefs.notifications?.money_loss,
    notify_leads_drop: prefs.notifications?.leads_drop,
    notify_ads_spike: prefs.notifications?.ads_spike,
    notify_competitors: prefs.notifications?.competitors,
    weekly_digest: prefs.notifications?.weekly_digest,
    channel_seo: prefs.channels?.seo,
    channel_ads: prefs.channels?.ads,
    channel_yandex_direct: prefs.channels?.yandex_direct,
    channel_social: prefs.channels?.social,
    channel_vk: prefs.channels?.vk,
    channel_email: prefs.channels?.email,
    channel_calls: prefs.channels?.calls,
    channel_crm: prefs.channels?.crm,
    competitor_1: prefs.competitors?.[0],
    competitor_2: prefs.competitors?.[1],
    competitor_3: prefs.competitors?.[2]
  };
  Object.entries(merged).forEach(([name, value]) => setControlValue(name, value));
  siteStat.textContent = saved.website || "example.com";
  setPlan(saved.plan || planInput.value || "pro399", { persist: false });
}

function setPlan(plan, options = {}) {
  const currentPlan = planCopy[plan] ? plan : "pro399";
  planInput.value = currentPlan;

  document.querySelectorAll(".plan-card").forEach((card) => {
    const active = card.dataset.plan === currentPlan;
    card.classList.toggle("active", active);
    card.setAttribute("aria-pressed", String(active));
  });

  const summary = document.querySelector("#plan-summary");
  summary.querySelector("strong").textContent = planCopy[currentPlan].title;
  summary.querySelector("span").textContent = planCopy[currentPlan].text;

  document.querySelectorAll("[data-feature]").forEach((item) => {
    const allowed = planAllows(currentPlan, featurePlans[item.dataset.feature]);
    item.classList.toggle("locked", !allowed);
  });

  settingsForm.querySelectorAll("[data-min-plan]").forEach((node) => {
    const allowed = planAllows(currentPlan, node.dataset.minPlan);
    if (node.tagName === "OPTION") {
      node.disabled = !allowed;
      return;
    }
    node.classList.toggle("is-plan-locked", !allowed);
    node.querySelectorAll("input, select").forEach((field) => {
      field.disabled = !allowed;
      if (!allowed && field.type === "checkbox") field.checked = false;
      if (!allowed && field.name?.startsWith("competitor_")) field.value = "";
    });
  });

  settingsForm.querySelectorAll("select").forEach((select) => {
    const selectedOption = select.options[select.selectedIndex];
    if (selectedOption?.disabled) {
      const fallback = [...select.options].find((option) => !option.disabled);
      if (fallback) select.value = fallback.value;
    }
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });

  if (options.persist !== false) saveStatus.textContent = "Тариф выбран. Нажмите “Сохранить настройки”, чтобы закрепить его в аккаунте.";
}

function settingsPayload() {
  const data = Object.fromEntries(new FormData(settingsForm).entries());
  const preferences = {
    show_money_first: true,
    language: "ru",
    plan: data.plan,
    telegram_sync: Boolean(data.telegram_sync),
    region: data.region,
    currency: data.currency,
    primary_conversion: data.primary_conversion,
    average_order_value: data.average_order_value,
    lead_value: data.lead_value,
    monthly_budget: data.monthly_budget,
    communication_tone: data.communication_tone,
    notifications: {
      money_loss: Boolean(data.notify_money_loss),
      leads_drop: Boolean(data.notify_leads_drop),
      ads_spike: Boolean(data.notify_ads_spike),
      competitors: Boolean(data.notify_competitors),
      weekly_digest: Boolean(data.weekly_digest)
    },
    channels: {
      seo: Boolean(data.channel_seo),
      ads: Boolean(data.channel_ads),
      yandex_direct: Boolean(data.channel_yandex_direct),
      social: Boolean(data.channel_social),
      vk: Boolean(data.channel_vk),
      email: Boolean(data.channel_email),
      calls: Boolean(data.channel_calls),
      crm: Boolean(data.channel_crm)
    },
    competitors: [data.competitor_1, data.competitor_2, data.competitor_3].filter(Boolean)
  };

  return {
    telegram_id: data.telegram_id || null,
    website: data.website,
    business_name: data.business_name,
    business_niche: data.business_niche,
    plan: data.plan,
    goal: data.goal,
    report_frequency: data.report_frequency,
    alert_level: data.alert_level,
    timezone: "Europe/Moscow",
    onboarding_completed: true,
    preferences
  };
}

async function refreshAccount() {
  const me = await api("/api/auth/me");
  currentAccount = me.authenticated ? me.user : null;
  if (!currentAccount) {
    loginStatus.textContent = "Создайте аккаунт или войдите, чтобы настройки сохранялись на сервере.";
    syncStat.textContent = "Нужен вход";
    return;
  }
  loginStatus.textContent = `Вы вошли как ${currentAccount.email}. Настройки сохраняются в аккаунте.`;
  syncStat.textContent = "Сессия активна";
  if (me.settings) applySettings(me.settings);
}

document.addEventListener("click", closeAllSelects);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeAllSelects();
});

enhanceSelects();
document.querySelectorAll(".plan-card").forEach((card) => {
  card.addEventListener("click", () => setPlan(card.dataset.plan));
});
setPlan(planInput.value || "pro399", { persist: false });

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const action = event.submitter?.dataset.action || "login";
  const form = Object.fromEntries(new FormData(loginForm).entries());
  loginStatus.textContent = action === "register" ? "Создаю аккаунт..." : "Проверяю email и пароль...";
  try {
    const result = await api(action === "register" ? "/api/auth/register" : "/api/auth/login", {
      method: "POST",
      body: JSON.stringify(form)
    });
    currentAccount = result.user;
    loginStatus.textContent = `Готово. Вы вошли как ${currentAccount.email}.`;
    syncStat.textContent = "Сессия активна";
    if (result.settings) applySettings(result.settings);
  } catch (error) {
    loginStatus.textContent = error.message;
  }
});

settingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!currentAccount) {
    saveStatus.textContent = "Сначала создайте аккаунт или войдите. Настройки больше не сохраняются только в браузере.";
    return;
  }
  const payload = settingsPayload();
  siteStat.textContent = payload.website || "example.com";
  saveStatus.textContent = "Сохраняю настройки на сервере...";
  try {
    const result = await api("/api/account/settings", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    currentAccount = result.user;
    saveStatus.textContent = "Настройки сохранены в аккаунте. Они будут доступны после повторного входа.";
  } catch (error) {
    saveStatus.textContent = error.message;
  }
});

refreshAccount().catch(() => {
  loginStatus.textContent = "Кабинет работает. Войдите, чтобы включить серверное сохранение.";
});
