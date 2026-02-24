import asyncio
import httpx

async def run():
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        resp = await client.get('https://plugins.leclee.top/api/v1/store/download/theme_aurora_premium', follow_redirects=True)
        print("Status code:", resp.status_code)
        if resp.status_code != 200:
            print("Content:", resp.text[:500])
        else:
            print("Content length:", len(resp.content))

if __name__ == "__main__":
    asyncio.run(run())
