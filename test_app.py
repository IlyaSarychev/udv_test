import pytest
import server
import aioredis
import os

from dotenv import load_dotenv


load_dotenv()

@pytest.fixture
def client(event_loop, aiohttp_client):
    app = server.get_application(db_index=1) # индекс базы данных для теста
    return event_loop.run_until_complete(aiohttp_client(app))

@pytest.fixture
def redis_cli(event_loop):
    r = event_loop.run_until_complete(aioredis.from_url(os.getenv('AIOREDIS_HOST_NAME'), db=1, decode_responses=True))
    yield r
    event_loop.run_until_complete(r.flushdb())
    event_loop.run_until_complete(r.close())

async def test_convert_without_params(client):
    resp = await client.get('/convert')
    assert resp.status == 400
    assert await resp.text() == 'Invalid query parameters'

async def test_convert_with_no_pair_in_database(client):
    resp = await client.get('/convert', params={'from': 'EUR', 'to': 'RUB', 'amount': 1})
    assert resp.status == 404

async def test_convert_with_valid_params(client, redis_cli):
    # тестовые данные
    await redis_cli.set('USDRUB', 108.39)
    await redis_cli.set('RUBUSD', 1 / 108.39)

    resp = await client.get('/convert', params={'from': 'USD', 'to': 'RUB', 'amount': 2})
    assert resp.status == 200
    rate = (await resp.json())['payload']['USDRUB']
    assert rate == 216.78
    
    resp = await client.get('/convert', params={'from': 'RUB', 'to': 'USD', 'amount': 108})
    assert resp.status == 200
    rate = (await resp.json())['payload']['RUBUSD']
    assert isinstance(rate, float)

async def test_convert_with_invalid_params(client, redis_cli):
    # тестовые данные
    await redis_cli.set('USDRUB', 108.39)
    await redis_cli.set('RUBUSD', 1 / 108.39)

    resp = await client.get('/convert', params={'from': 10, 'to': 26, 'amount': 10})
    assert resp.status == 400

    resp = await client.get('/convert', params={'from': 'rub', 'to': 'usd', 'amount': 'str'})
    assert resp.status == 400

async def test_database_with_valid_data(client, redis_cli):
    data = {
        'USDRUB': 112.26,
        'EURRUB': 144.84,
        'CNYRUB': 19
    }
    resp = await client.post('/database', json=data)
    assert resp.status == 200
    assert (await resp.json())['success'] == True

async def test_database_with_invalid_data(client, redis_cli):
    data = {
        '99999999': '$$$$',
        ':?*((""№': 'rfr',
        '__': 'wwww',
    }
    resp = await client.post('/database', json=data)
    assert resp.status == 400
    assert (await resp.text()) == 'Invalid pair name. The word must consist of latin letters'

    resp = await client.post('/database', json={'USDRUB': 'ee'})
    assert resp.status == 400
    assert (await resp.text()) == 'Invalid pair rate value'

    resp = await client.post('/database', json={'USDRUB': 0})
    assert resp.status == 400
    assert (await resp.text()) == 'Rate cannot be 0'

async def test_database_with_merge(client, redis_cli):
    await redis_cli.set('USDRUB', 112.26)
    await redis_cli.set('EURRUB', 144.84)

    await client.post('/database', params={'merge': 1}, json={'USDRUB': 104.2})
    assert (await redis_cli.get('USDRUB')) == '104.2'
    assert (await redis_cli.get('EURRUB')) == '144.84'

async def test_database_without_merge(client, redis_cli):
    await redis_cli.set('USDRUB', 112.26)
    await redis_cli.set('EURRUB', 144.84)

    await client.post('/database', params={'merge': 0}, json={'USDRUB': 104.2})
    assert (await redis_cli.get('USDRUB')) == '104.2'
    assert (await redis_cli.get('EURRUB')) == None