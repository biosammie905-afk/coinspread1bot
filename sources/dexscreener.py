"""
Fetches newly profiled tokens from Dexscreener's free public API.
Docs: https://docs.dexscreener.com/api/reference

NOTE: Dexscreener doesn't expose a raw "brand new pair created" firehose on
the free tier. The closest reliable free endpoint is /token-profiles/latest/v1,
which lists tokens as they get a Dexscreener profile (usually right after
launch). If you later get access to a paid on-chain indexer (Moralis,
Bitquery, a node + subgraph), swap this function's internals for that feed
without touching bot.py.
"""
import httpx

API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"


async def fetch_new_tokens():
    """
    Returns a list of dicts: {source, item_id, name/desc, url, chain}
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(API_URL)
        resp.raise_for_status()
        data = resp.json()

    items = []
    for token in data:
        token_address = token.get("tokenAddress")
        chain_id = token.get("chainId")
        if not token_address:
            continue
        items.append({
            "source": "dexscreener",
            "item_id": f"{chain_id}:{token_address}",
            "chain": chain_id,
            "description": token.get("description") or "New token",
            "url": token.get("url"),
        })
    return items


def format_message(item: dict) -> str:
    return (
        f"⚡ <b>New token pair on {item['chain'].upper()}</b>\n\n"
        f"{item['description'][:200]}\n"
        f"{item['url']}"
    )
