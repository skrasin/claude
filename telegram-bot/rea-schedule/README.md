> **Не используется (16.11.2026).** rasp.rea.ru запрещает автоматический доступ (robots.txt,
> 403 на данных расписания) — обходить не стали. Вместо рассылки — напоминание владельцу в
> 20:00 (вс–пт), `listener/reminders.json`, id `rea-schedule`. Код оставлен на случай
> рассылки из выгруженного вручную `.ics`.

# Задача: расписание РЭУ → Telegram

Каждый день в 20:00 MSK — расписание группы из `settings.json` на завтра.
Перенесено из ветки `claude/zen-dijkstra-7kvorw` (`rea-schedule-bot/`) на общую основу бота:
токен и прокси берутся из `~/bot/config.json`, Telegram идёт через туннель AmneziaWG,
`rasp.rea.ru` — напрямую (зарубежным адресам он отвечает 403).

`settings.json`:
- `group` — группа, как в поиске на rasp.rea.ru;
- `recipients` — кому слать (chat_id); пусто = владельцу из `config.json`.

Режимы:
```
python3 rea-schedule/schedule_bot.py --ping        # пробное сообщение
python3 rea-schedule/schedule_bot.py --dry-run     # напечатать, не отправлять
python3 rea-schedule/schedule_bot.py --dump        # отправить и сохранить ответ сайта в dump.html
python3 rea-schedule/schedule_bot.py --date 2026-11-21 --dry-run
python3 rea-schedule/schedule_bot.py --from-file dump.html --dry-run
```
Если сайт недоступен, даты нет в расписании или скрипт упал — придёт ⚠️.
Разбор проверен только на тестовой странице; первый `--dump` с настоящего сайта — сверить.
