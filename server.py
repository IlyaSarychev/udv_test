import aioredis

from aiohttp import web


routes = web.RouteTableDef()

@routes.get('/convert')
async def convert_handler(request):
    params = request.rel_url.query
    pair = params.get('from').upper() + params.get('to').upper()
    amount = params.get('amount')
    res = 0

    async with aioredis.from_url('redis://localhost', db=0, decode_responses=True) as r:
        rate = await r.get(pair)
        if rate:
            rate = float()
            res = int(amount) * rate
            response = {
                'success': True,
                'payload': {
                    pair: res,
                    'amount': amount
                }
            }
            return web.json_response(response)
        else:
            return web.HTTPNotFound()

@routes.post('/database')
async def database_handler(request):
    to_merge = int(request.rel_url.query.get('merge', 1))
    data = await request.post()

    async with aioredis.from_url('redis://localhost', db=0, decode_responses=True) as r:
        if not to_merge:
            await r.flushdb()
            
        for key, value in data.items():
            key = key[:6].upper()
            await r.set(key, value)

            # обратная пара
            key = key[3:6] + key[:3]
            value = 1 / float(value)
            await r.set(key, value)
    
    return web.json_response({'success': True})

def main():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)

if __name__ == '__main__':
    main()