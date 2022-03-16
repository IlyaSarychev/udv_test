import aiohttp
import asyncio


async def set_currency_request(session, data, params):
    async with session.post('http://localhost:8080/database', params=params, data=data) as resp:
        print(resp.status)
        print(await resp.text())

async def convert_currency_request(session, params):
    async with session.get('http://localhost:8080/convert', params=params) as resp:
        print(resp.status)
        print(await resp.text())

async def main():
    async with aiohttp.ClientSession() as session:
        await set_currency_request(
                                    session, 
                                    {
                                        'USDRUB': 112.26,
                                        'EURRUB': 144.84,
                                        'CNYRUB': 18.88
                                    }, 
                                    {
                                        'merge': 1
                                    })
        await set_currency_request(
                                    session, 
                                    {
                                        'USDRUB': 108.39
                                    }, 
                                    {
                                        'merge': 0
                                    })
        await convert_currency_request(session, {'from': 'USD', 'to': 'RUB', 'amount': 2})
        await convert_currency_request(session, {'from': 'EUR', 'to': 'RUB', 'amount': 1})


if __name__ == '__main__':
    asyncio.run(main())