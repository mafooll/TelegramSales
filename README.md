# TelegramSales

Телеграм-магазин на aiogram. Один процесс, long polling, PostgreSQL.

## Запуск

```bash
cp .env.example .env
docker compose up -d
```

`migrate` накатывает миграции и завершается, это ожидаемо. Бот стартует после
него. На сервере ставь `BOT_TARGET=runtime`, локально годится `dev` с
перезапуском по изменению файлов.

## Бекапы

Сервис `backup` раз в сутки снимает `pg_dump` в формате custom в том
`postgres_backups` и удаляет дампы старше двух недель. Интервал и срок хранения
меняются через `BACKUP_INTERVAL` и `BACKUP_KEEP_DAYS`.

```bash
make backup                                  # снять дамп прямо сейчас
make backups                                 # что лежит в томе
make restore f=telegramsales-20260101-000000.dump
```

Восстановление перезаписывает текущую базу, бота лучше остановить заранее.
Забрать дамп с сервера:

```bash
docker compose cp backup:/backups/<файл> .
```

## Проверки

```bash
make check    # линт, типы, тесты
make quick    # то же самое без тестов с базой
```
