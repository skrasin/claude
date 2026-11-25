# Установка и обновление бота на NAS: пошагово

Всё делается в браузере через DSM (`https://quickconnect.to/fancymusic`), SSH не нужен.
Инструкция годится и для первой установки, и для обновления: ваши настройки
(`config.json`, `vpn/amnezia.conf`, установленный wireproxy, сохранённые заметки) при
копировании не затираются — их нет в архиве.

Что получится: каждый вечер в 20:00 — расписание дочери на завтра и отсчёт до зачётов за
7 дней; бот принимает заметки и файлы; Telegram работает через туннель Amnezia.

---

## Шаг 1. Скачать код
На компьютере: https://github.com/skrasin/claude → ветка **main** → **Code → Download ZIP**.

## Шаг 2. Залить на NAS
1. **File Station** → **home** → **Загрузить** → `claude-main.zip`.
2. Правый клик по архиву → **Извлечь → Извлечь сюда**.
3. Откройте `claude-main/telegram-bot`, выделите папки
   **`common`, `listener`, `tools`, `vpn`, `rea-schedule`** (с Ctrl).
4. Правый клик → **Копировать в…** → `home/bot` → на вопрос о совпадениях **Перезаписать**.
5. Удалите `claude-main` и `claude-main.zip`.

## Шаг 3. Проверить настройки (один раз)
1. `home/bot/config.json` — открыть Текстовым редактором. Должно быть:
   ```json
   {
     "token": "ваш токен",
     "owner_chat_id": 349362961,
     "allowed_chat_ids": [],
     "proxy": "http://127.0.0.1:10809"
   }
   ```
2. В `home/bot/vpn/` должен лежать `amnezia.conf` (отдельный для NAS).
3. **Панель управления → Региональные параметры** — часовой пояс **(GMT+03:00) Москва**.

## Шаг 4. Постоянная задача `bot-run`
**Панель управления → Планировщик задач.** Если задачи `bot-run` нет — **Создать →
Запланированная задача → Определяемый пользователем сценарий**; если есть — правый клик →
**Изменить** и сверить.
- **Общие:** задача `bot-run`, пользователь `fancymusic`, **Включено**.
- **Расписание:** **Выполнять ежедневно**; первый запуск **00:00**; частота **каждые 10 минут**;
  последний запуск **23:50**.
- **Настройки задачи → сценарий:**
  ```bash
  cd /volume1/homes/fancymusic/bot
  python3 tools/autoupdate.py >> tools/autoupdate.log 2>&1
  python3 vpn/awg_setup.py ensure >> vpn/ensure.log 2>&1
  nohup python3 listener/listener.py >/dev/null 2>&1 &
  ```
  Первая строка — автообновление из GitHub (нужен `~/bot-repo`, см. конец файла). Без
  `~/bot-repo` она пришлёт одно «⚠️» и не мешает остальному.

Каждые 10 минут она поднимает VPN-туннель и приёмник, если что-то упало
(в том числе после перезагрузки NAS). Расписание и напоминания отправляет приёмник —
отдельной задачи на 20:00 не нужно.

## Шаг 5. Применить обновление
Приёмник читает код при запуске, поэтому после копирования его надо перезапустить.
Разовая задача `bot-update` (создать один раз, потом только **Выполнить** после каждого обновления):
- **Общие:** `bot-update`, пользователь `fancymusic`.
- **Расписание:** «Выполнить в следующую дату», сегодня, **не повторять**.
- **Сценарий:**
  ```bash
  cd /volume1/homes/fancymusic/bot
  export PYTHONUNBUFFERED=1
  {
    date
    echo "0. версия кода: $(grep -c 'cmd_week' listener/commands.py)"
    ls -l listener/listener.py listener/commands.py
    echo "1. останавливаю бота"
    python3 listener/listener.py --stop
    echo "2. проверяю туннель"
    python3 vpn/awg_setup.py ensure
    python3 vpn/awg_setup.py status
    echo "3. сообщение, которое придёт в 20:00:"
    python3 rea-schedule/from_file.py
    echo "4. запускаю бота"
    nohup python3 listener/listener.py >/dev/null 2>&1 &
    sleep 3
    echo "   pid: $(cat listener/listener.lock)"
    echo "=== ГОТОВО ==="
  } > update.log 2>&1
  ```
  `listener.py --stop` находит бота по аргументам запуска процесса, поэтому не задевает саму
  задачу. **Не используйте `pkill -f …listener.py` в задачах Планировщика:** DSM передаёт весь
  текст сценария одной командой, и `pkill` убивает саму задачу.

**ОК** → выделить → **Выполнить**. Через 1–2 минуты открыть `home/bot/update.log`:
должно быть «Telegram через туннель: доступен», текст сообщения на завтра, новый pid и `=== ГОТОВО ===`.

## Шаг 6. Проверить в Telegram
| Команда | Ожидаемый ответ |
|---|---|
| `/status` | аптайм NAS, нагрузка, свободное место |
| `/reminders` | `20:00 (каждый день): расписание на завтра из файла` |
| `/exams` | семь зачётов с отсчётом дней |
| переслать любое сообщение | бот ставит 👍 |

## Шаг 7. Убрать лишнее
- В Планировщике удалить разовые задачи: **`bot-check`, `bot-vpn-setup`, `rea-check`**.
- В `home/bot` удалить логи: `check.log`, `vpn-check.log`, `rea-check.log`,
  `rea-schedule/probe.log`, `rea-schedule/dump.html` (каких нет — пропустить).
- **Не удалять:** `config.json`, `vpn/amnezia.conf`, `vpn/wireproxy`, `vpn/wireproxy.conf`,
  папку `data/`, файлы `state.json`.

---

## Потом: обновить расписание
Новые скриншоты rasp.rea.ru → в сессию Claude, которая собирает расписание; она обновляет
`telegram-bot/rea-schedule/timetable/schedule-*.json` в `main`. Затем скачать этот файл
(на GitHub: открыть файл → **Download raw file**) и загрузить в `home/bot/rea-schedule/timetable/`
с перезаписью. Перезапуск не нужен — файл читается каждый вечер.
За 3 дня до конца данных бот сам напомнит прислать новые скриншоты.

## Если что-то не так
| Признак | Что делать |
|---|---|
| Бот не отвечает | Выполнить `bot-update`, прислать Claude `update.log` |
| «Telegram через туннель: НЕДОСТУПЕН» | `vpn/wireproxy.log` → Claude; проверить, что Amnezia-сервер работает |
| `/exams` — «Не знаю такой команды» | папка `listener` не перезаписалась: повторить шаги 2 и 5 |
| В 20:00 ничего не пришло | `listener/listener.log` → Claude |

---

## Автообновление из GitHub: доступ NAS к репозиторию (один раз, из дома)
NAS получает ключ **только для чтения** репозитория `skrasin/claude` (deploy key) и сам
скачивает обновления. Подключение к GitHub — по SSH через порт 443 (`ssh.github.com`).

1. На Mac: `ssh nas`
2. На NAS — ключ и настройка:
   ```bash
   ssh-keygen -t ed25519 -N "" -C "nas-bot read-only skrasin/claude" -f ~/.ssh/id_ed25519_github_deploy
   printf '\nHost github-deploy\n  HostName ssh.github.com\n  Port 443\n  User git\n  IdentityFile ~/.ssh/id_ed25519_github_deploy\n  IdentitiesOnly yes\n' >> ~/.ssh/config
   chmod 600 ~/.ssh/config ~/.ssh/id_ed25519_github_deploy
   cat ~/.ssh/id_ed25519_github_deploy.pub
   ```
3. GitHub → `skrasin/claude` → **Settings → Deploy keys → Add deploy key**: Title
   `NAS bot (read-only)`, Key — строка из `.pub`, **«Allow write access» не отмечать**.
4. На NAS — проверить ключ GitHub и подключиться:
   ```bash
   # ssh-keyscan в DSM нет: ключ GitHub берём из официального API GitHub по HTTPS
   # Все три ключа GitHub: старый ssh в DSM спрашивает ECDSA, одного ED25519 мало
   curl -sS https://api.github.com/meta | python3 -c 'import json,sys; [print("[ssh.github.com]:443 "+k) for k in json.load(sys.stdin)["ssh_keys"]]' > /tmp/gh.key
   ssh-keygen -lf /tmp/gh.key
   # ED25519 SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
   # ECDSA   SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM
   # RSA     SHA256:uNiVztksCsDhcc0u9e8BujQXVUpKZIDTMczCvj3tD2s
   grep -v 'ssh.github.com' ~/.ssh/known_hosts > /tmp/kh; cat /tmp/gh.key >> /tmp/kh
   mv /tmp/kh ~/.ssh/known_hosts && chmod 600 ~/.ssh/known_hosts && rm /tmp/gh.key
   ssh -T github-deploy              # «Hi skrasin/claude! You've successfully authenticated…»
   ```
5. На NAS — скачать репозиторий и проверить:
   ```bash
   git clone --depth 1 --branch main git@github-deploy:skrasin/claude.git ~/bot-repo
   echo "@eaDir/" >> ~/bot-repo/.git/info/exclude
   cd ~/bot-repo && git log --oneline -1 && git pull --ff-only
   diff -rq ~/bot-repo/telegram-bot ~/bot | grep -v -e '^Only in /volume1/homes/fancymusic/bot' -e '^Only in /var/services/homes/fancymusic/bot'
   ```
   Последняя команда показывает расхождения кода на NAS и в репозитории (ожидается пусто
   или почти пусто; файлы, которые есть только на NAS — настройки, логи, VPN — скрыты).

6. Включить автообновление (из того же Терминала на NAS):
   ```bash
   cd ~/bot-repo && git pull --ff-only
   cp telegram-bot/tools/autoupdate.py ~/bot/tools/
   cd ~/bot && python3 tools/autoupdate.py
   ```
   Первый запуск копирует весь код из репозитория в `~/bot` и перезапускает бота; в Telegram
   приходит «🔄 Бот обновлён». Затем в Планировщике добавить в `bot-run` строку
   `python3 tools/autoupdate.py >> tools/autoupdate.log 2>&1` (см. шаг 4).

**Дальше:** всё, что попадает в `main`, через ≤10 минут оказывается на NAS. ZIP, File Station и
`bot-update` больше не нужны (`bot-update` можно оставить для ручной диагностики).
Журнал: `~/bot/tools/autoupdate.log`. Принудительно: `python3 tools/autoupdate.py --force`.

## Приглашения в iCloud Calendar

После доставки новой версии откройте в File Station **home → bot**.
Сохраните копию файла **calendar.example.json** под именем **calendar.local.json**
в той же папке. В копии заполните поля:

- **enabled** — значение **true** включает распознавание.
- **openai_api_key** — отдельный ключ OpenAI API.
- **icloud_account** — адрес учётной записи Apple.
- **icloud_app_password** — [пароль приложения Apple](https://support.apple.com/ru-ru/102654).
- **calendar_name** — точное имя календаря iCloud. По умолчанию **Calendar**.

Вносите ключ и пароль в **calendar.local.json** на NAS. Убедитесь, что этот
файл доступен только учётной записи бота. Он исключён из Git. Бот читает
его при следующем сообщении.

В личном чате с ботом отправьте текст приглашения, пересланное сообщение,
афишу, PDF или голосовое. Содержимое разбирает OpenAI API. Сообщения по-прежнему
сохраняются во входящих. Если дата и время однозначны, бот добавит личную
запись в календарь и пришлёт подтверждение. Для события без времени окончания
он выделяет час. Время без указанной зоны считается московским.

При вопросе бота ответьте на его сообщение через «Ответить». Если в
сообщении только ссылка, приложите текст или скриншот страницы. При смене
календаря или ключа достаточно обновить **calendar.local.json**.
