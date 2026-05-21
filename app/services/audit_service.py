import httpx
from bs4 import BeautifulSoup


async def audit_domain(domain: str) -> dict:
    url = f"https://{domain}"
    result = {
        "domain": domain,
        "available": False,
        "cms": "Не определена",
        "speed": "Нужно проверить",
        "mobile": "Верстка выглядит адаптивной, если есть viewport.",
        "analytics": [],
        "lead_forms": False,
        "contacts": [],
        "seo": [],
        "pages": [],
        "summary": "",
    }
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(url)
        result["available"] = response.status_code < 500
        result["speed"] = "Сайт отвечает быстро" if response.elapsed.total_seconds() < 2.5 else "Сайт отвечает медленнее желаемого"
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        text = html.lower()
        if "wp-content" in text:
            result["cms"] = "WordPress"
        elif "tilda" in text:
            result["cms"] = "Tilda"
        elif "bitrix" in text:
            result["cms"] = "Bitrix"
        if "gtag(" in text or "google-analytics" in text:
            result["analytics"].append("Google Analytics")
        if "fbq(" in text:
            result["analytics"].append("Meta Pixel")
        if "ttq." in text:
            result["analytics"].append("TikTok Pixel")
        result["lead_forms"] = bool(soup.find("form"))
        if soup.find("meta", attrs={"name": "viewport"}):
            result["mobile"] = "Мобильная адаптация включена"
        if soup.title and soup.title.text.strip():
            result["seo"].append("Есть title")
        if soup.find("meta", attrs={"name": "description"}):
            result["seo"].append("Есть meta description")
        for link in soup.find_all("a", href=True)[:80]:
            href = link["href"]
            if href.startswith(("tel:", "https://wa.me", "https://t.me", "mailto:")):
                result["contacts"].append(href)
            if href.startswith("/") and href not in result["pages"]:
                result["pages"].append(href)
    except Exception as exc:
        result["summary"] = f"Сайт не удалось проверить: {exc}"
        return result

    good = []
    bad = []
    good.append("сайт доступен") if result["available"] else bad.append("сайт недоступен")
    good.append("есть формы заявок") if result["lead_forms"] else bad.append("не найдены формы заявок")
    good.append("подключена аналитика") if result["analytics"] else bad.append("не найдена аналитика")
    result["summary"] = f"Что хорошо: {', '.join(good) or 'нужно больше данных'}. Что улучшить: {', '.join(bad) or 'критичных проблем не видно'}."
    return result
