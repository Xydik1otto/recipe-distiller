# 🚀 Recipe Distiller — встановлення покроково

Для не-програміста. Мета: за 5 хвилину локальний «just the recipe» працює у вашому
браузері. Ніяких хмар, реєстрацій і Docker — все на вашому комп'ютері.

## Windows (10/11)

1. **Встановіть Python** (один раз): завантажте з <https://www.python.org/downloads/>
   і при встановленні поставте галочку **«Add python.exe to PATH»**.
2. **Завантажте проєкт**: кнопка *Code → Download ZIP* на GitHub, розпакуйте
   (наприклад, у `C:\Projects\recipe-distiller`).
3. **Встановіть залежності** (один раз): відкрийте подвійним кліком
   `install.bat` у папці проєкту — він сам поставить усе потрібне.
4. **Запустіть**: подвійний клік по `start.bat`. Відкриється браузер на
   <http://localhost:8000>. Чорне вікно консолі — це ваш сервер, не закривайте його
   (закрили — застосунок «вимкнувся», просто запустіть `start.bat` знову).
5. **Автозапуск** (за бажанням): натисніть `Win+R`, введіть `shell:startup`, Enter —
   і покладіть у папку, що відкриється, **ярлик** на `start.bat` (ПКМ по
   `start.bat → Надіслати → Робочий стіл (створити ярлик)`, потім перетягніть ярлик
   у вікно Startup). Тепер дистилер стартує разом із Windows.

## Linux

1. Потрібні Python 3.10+ і pip (зазвичай уже є): `python3 --version`.
2. У папці проєкту:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Швидкий старт вручну:
   ```bash
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
4. **Автозапуск через systemd user unit**:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp deploy/recipe-distiller.service ~/.config/systemd/user/
   # за потреби поправте WorkingDirectory на свій шлях до проєкту
   systemctl --user daemon-reload
   systemctl --user enable --now recipe-distiller
   ```
   Перевірити: `systemctl --user status recipe-distiller`, журнали:
   `journalctl --user -u recipe-distiller -f`.
   Щоб юніт жив після виходу з сесії: `loginctl enable-linger $USER`.

## Розширення для браузера

Папка `extension/` — це unpacked-розширення (Manifest V3). Інструкція:
`chrome://extensions` → увімкніть **Developer mode** → **Load unpacked** →
виберіть папку `extension/`. Деталі: `extension/README.md`.

## Оновлення

1. Замініть файли проєкту новою версією (Download ZIP → розпакувати поверх,
   або `git pull`, якщо клонували репозиторій).
2. Ще раз запустіть `install.bat` (Windows) або
   `python3 -m pip install -r requirements.txt` (Linux) — могли з'явитися нові
   залежності.
3. Перезапустіть `start.bat` або `systemctl --user restart recipe-distiller`.

Ваші дані не страждають: книга рецептів живе у файлі `recipes.db` поруч з проєктом,
а на випадок чого — кнопка **⬇ Export JSON** у веб-інтерфейсі зберігає все у файл.

## Де що лежить

| Що | Де |
|---|---|
| база рецептів | `recipes.db` (SQLite, створюється сам) |
| резервна копія | кнопка ⬇ Export JSON в інтерфейсі |
| розширення | `extension/` |
| автозапуск Windows | ярлик на `start.bat` у папці Startup |
| автозапуск Linux | `deploy/recipe-distiller.service` |
