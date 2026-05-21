import httpx


class GoogleAnalyticsClient:
    async def fetch_sources(self, property_id: str, access_token: str, days: int = 7) -> list[dict]:
        url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
        payload = {
            "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
            "dimensions": [{"name": "sessionSource"}, {"name": "sessionMedium"}],
            "metrics": [{"name": "sessions"}, {"name": "conversions"}, {"name": "averageSessionDuration"}],
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        rows = response.json().get("rows", [])
        return [
            {
                "source": row["dimensionValues"][0]["value"],
                "medium": row["dimensionValues"][1]["value"],
                "sessions": int(float(row["metricValues"][0]["value"])),
                "conversions": int(float(row["metricValues"][1]["value"])),
                "avg_time": float(row["metricValues"][2]["value"]),
            }
            for row in rows
        ]
