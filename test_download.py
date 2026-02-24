import asyncio
import httpx

async def main():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6InN1cGVyYWRtaW4iLCJleHAiOjE3NzE5OTAwMjQsInR5cGUiOiJhY2Nlc3MifQ.btp4nuaiyswkyYsbpSkkCvIIcVEAVMyY89OyXxbbzMQ"
    try:
        async with httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0'}, timeout=15) as client:
            resp = await client.get(
                'https://plugins.leclee.top/api/v1/store/download/theme_aurora_premium',
                headers={'Authorization': f'Bearer {token}'}
            )
            print("Status:", resp.status_code)
            print("Headers:", resp.headers)
            print("Body (first 200 chars):", resp.text[:200])
    except Exception as e:
        print("Error:", repr(e))

if __name__ == '__main__':
    asyncio.run(main())
