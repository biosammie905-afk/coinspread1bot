"""
Fetches recently added coins from CoinGecko's free public API.
Docs: https://www.coingecko.com/en/api/documentation
Endpoint used: /coins/list/new (no API key needed on free tier, rate-limited)
"""
import httpx

API_URL = "https://api.coingecko.com/api/v3/coins/list/new"


async def fetch_new_coins():
    """
    Returns a list of dicts: {id, name, symbol, activated_at}
    Each item has a stable unique 'id' we use for dedup.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(API_URL)
        resp.raise_for_status()
        data = resp.json()

    items = []
    for coin in data:
        items.append({
            "source": "coingecko",
            "item_id": coin.get("id"),
            "name": coin.get("name"),
            "symbol": (coin.get("symbol") or "").upper(),
            "url": f"https://www.coingecko.com/en/coins/{coin.get('id')}",
        })
    return items


def format_message(item: dict) -> str:
    return (
        f"🆕 <b>New coin listed on CoinGecko</b>\n\n"
        f"<b>{item['name']}</b> ({item['symbol']})\n"
        f"{item['url']}"
    )
