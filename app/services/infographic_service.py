import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.models import TrafficSource, Website
from app.services.ai_service import explain_sources
from app.services.traffic_service import prepare_map_sources


def render_traffic_map_html(website: Website, sources: list[TrafficSource], output_path: str) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader("app/templates/infographics"), autoescape=True)
    template = env.get_template("traffic_map.html")
    shown = prepare_map_sources(sources)
    total = sum(item.visitors for item in shown) or 1
    html = template.render(
        website=website,
        sources=[
            {
                "domain": item.source_domain,
                "visitors": item.visitors,
                "percent": round(item.visitors / total * 100),
                "quality": item.quality_score,
                "category": item.category,
            }
            for item in shown
        ],
        sources_json=json.dumps([
            {
                "domain": item.source_domain,
                "visitors": item.visitors,
                "percent": round(item.visitors / total * 100),
                "quality": item.quality_score,
                "category": item.category,
            }
            for item in shown
        ]),
        ai_summary=explain_sources(sources),
    )
    output.write_text(html, encoding="utf-8")
    return str(output)
