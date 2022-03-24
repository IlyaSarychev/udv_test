# Тестовое UDV
## Установка

Предварительно создайте и активируйте виртуальную среду

Запуск сервера Redis:
```sh
redis-server
```

Установка зависимостей:
```sh
pip install -r requirements.txt
```

Запуск приложения:
```sh
python server.py
```

Запуск клиента с тестовыми запросами:
```sh
python client.py
```

## Запуск тестов

Для тестов использовалась библиотека pytest-aiohttp. Запуск через команду pytest

## Запуск через docker-compose

```sh
docker-compose -f docker-compose.dev.yaml up --build
```