import aioredis
import string
import os

from aiohttp import web
from dotenv import load_dotenv


load_dotenv()
routes = web.RouteTableDef()

@routes.get('/convert')
async def convert_handler(request):
    params = request.rel_url.query
    
    try:
        from_param = params.get('from').upper()
        to_param = params.get('to').upper()
        pair = from_param + to_param
        amount = float(params.get('amount'))

        if len(from_param) != 3:
            raise ValueError('Parameter "from" must be of length 3')

        if len(to_param) != 3:
            raise ValueError('Parameter "to" must be of length 3')

    except AttributeError:
        return web.HTTPBadRequest(text='Invalid query parameters')
    except ValueError as err:
        return web.HTTPBadRequest(text=str(err))

    async with aioredis.from_url(os.getenv('AIOREDIS_HOST_NAME'), db=request.app['DB_INDEX'], decode_responses=True) as r:
        rate = await r.get(pair)
        if rate:
            rate = float(rate)
            res = amount * rate
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
    data = await request.json()

    async with aioredis.from_url(os.getenv('AIOREDIS_HOST_NAME'), db=request.app['DB_INDEX'], decode_responses=True) as r:
        if not to_merge:
            await r.flushdb()
            
        for key, value in data.items():

            print(key, value)

            key = key[:6].upper()

            # Валидация пары
            try:
                for letter in key:
                    if not letter in string.ascii_letters:
                        raise ValueError('Invalid pair name. The word must consist of latin letters')
            except ValueError as err:
                return web.HTTPBadRequest(text=str(err))

            # Валидация курса
            try:
                value = float(value)
                assert value != 0
            except ValueError as err:
                return web.HTTPBadRequest(text='Invalid pair rate value')
            except AssertionError:
                return web.HTTPBadRequest(text='Rate cannot be 0')

            # Запись в бд
            await r.set(key, value)

            # обратная пара
            key = key[3:6] + key[:3]
            value = 1 / value
            await r.set(key, value)
    
    return web.json_response({'success': True})


def get_application(db_index):
    app = web.Application()
    app['DB_INDEX'] = db_index
    app.add_routes(routes)
    return app

def main():
    app = web.Application()
    app['DB_INDEX'] = 0
    app.add_routes(routes)
    web.run_app(app)

if __name__ == '__main__':
    main()
