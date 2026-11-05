# Changelog

Усі помітні зміни проєкту документуються тут.

Формат — [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/),
версіонування — [Semantic Versioning](https://semver.org/lang/uk/).

## [Unreleased]

### Added
- **Pantry («що є в холодильнику»)**: таблиця `pantry` у SQLite, `GET/PUT
  /api/pantry` та `GET /api/pantry/match` — збережені рецепти,
  відсортовані за покриттям наявними продуктами (прапорець `can_cook`,
  список відсутніх інгредієнтів); базові продукти (сіль, перець, вода,
  олія, цукор, борошно) вважаються завжди наявними; матчинг з врахуванням
  множини та меж слів; блок «🧊 Що є в холодильнику» в UI.
- **Приблизна оцінка поживності**: `app/nutrition.py` — таблиця ~40
  продуктів (ккал/білки/жири/вуглеводи на 100 г), конверсія кількостей у
  грами (г/кг/мл/л, ложки, чашки з щільністю для борошна/цукру/молока…,
  типові ваги штуки — яйце ~50 г); `POST /api/nutrition {recipe}` +
  `GET /api/recipes/{id}/nutrition`, покриття оцінки (`coverage`) і список
  нерозпізнаних рядків; рядок «≈ поживність» у картці рецепта.
- **Автодоповнення тегів**: `GET /api/tags/suggest?q=` — словник тегів
  книги з кількістю використань (злиття варіантів у різному регистрі,
  префіксний фільтр), `datalist` під фільтром за тегом в UI.

### Removed
- Monetization scaffolding — проєкт 100% безкоштовний open-source:
  видалено `.github/FUNDING.yml` (GitHub Sponsors), секцію «Монетизація»
  та Pro/paid-згадки з PLAN.md.

## [1.0.0] — 2026-11-05

### Added
- **Browser extension (MV3, unpacked)**: папка `extension/` — кнопка на панелі
  інструментів відкриває дистилер з URL сторінки рецепта (`/?url=…`,
  автозапуск extraction), адреса сервера налаштовується через Options.
- **Substitution hints**: база ~45 типових замін (`butter↔margarine`,
  `egg→flax egg`, `buttermilk→milk+lemon`…), `GET /api/substitutions` +
  `POST /api/substitutions/match`, підказки поруч з інгредієнтами та
  огляд бази в UI; матчинг по межах слів («butter» не спрацьовує всередині
  «buttermilk»).
- **Дата додавання + новизна**: явне сортування `sort=new`, дата 📅 біля
  кожного збереженого рецепта.
- **Друк списку покупок**: кнопка 🖨 у списку + print-CSS, що показує
  лише список.
- **i18n UA/EN**: перемикач UA/EN, автовизначення мови браузера, збереження
  вибору, словники з парністю ключів. Російську локалізацію не додано
  (свідоме рішення).
- **First-run demo**: opt-in банер «Завантажити демо» → 3 демо-рецепти
  (`POST /api/demo`, ідемпотентно).
- **INSTALL.md** + `start.bat` / `install.bat` + systemd user unit
  (`deploy/recipe-distiller.service`).
- **Packaging**: повний `pyproject.toml`, консольна команда `recipe-distiller`,
  `pip install -e .` працює.
- **Data safety**: `GET /api/recipes/export.csv` (one-click CSV) +
  підтвердження перед видаленням рецепта.
- **A11y**: aria-labels на всіх іконкових кнопках (з назвою рецепта),
  зірки-кнопки, `:focus-visible` обведення, підвищений контраст `.muted`.
- **README.en.md** — англійська версія README.

### OSS
- `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/` (bug + feature, UA/EN),
  `SECURITY.md`, розширений `.gitignore` (`.env*`, `*.sqlite3`), секція
  Contributing + GitHub topics у README.

## [0.4.0] — 2026-11-05

### Added
- **Улюблені + оцінки**: прапорець ♥ і 5-зірковий рейтинг у книзі рецептів;
  сортування (нові / за рейтингом / за назвою) та фільтр «лише улюблені»;
  `PUT /api/recipes/{id}/rating`; рейтинг переживає export/import.
- **Конвертація одиниць**: cups→ml→g для типових інгредієнтів (борошно, цукор,
  масло, молоко, олія, мед…); `POST /api/convert`; підказки «≈ 240 г» поруч
  з оригіналом у картці рецепта та у printable-версії.
- **Print-friendly CSS**: оновлений `/print` — справжній `@media print`
  (12pt, без кнопок і тулбару, без розривів списків посеред рядка),
  екранування HTML у назві/інгредієнтах/кроках, футер із посиланням на джерело.
- **PWA offline**: service worker (`/sw.js`) кешує оболонку застосунку та
  збережену книгу рецептів (`/api/recipes*` — network-first із кеш-фолбеком);
  `manifest.webmanifest` для встановлення як застосунок.
- **Інгредієнти-чекліст**: чекбокси в картці рецепта, стан зберігається
  у localStorage (ключ на рецепт), закреслення відмічених, кнопка скидання.

### Docs / infra
- `CHANGELOG.md`, favicon + OG-мета,
  `scripts/smoke.sh` (запуск сервера на випадковому порту + перевірка ендпоінтів),
  README-секція «Чому це існує».

## [0.3.0] — 2026-11-04

### Added
- **Щотижневий план харчування**: 7 слотів (Пн–Нд) у SQLite, drag & drop,
  `GET/PUT /api/plan`, автогенерація списку покупок з плану.
- **Список покупок**: об'єднання кількостей кількох рецептів
  (`1 cup` + `2 cups` → `3 cups`), POST `/api/shopping-list`.
- **Масштабування порцій**: перерахунок кількостей під цільові порції
  (`/api/scale`, `/api/recipes/{id}/scale`).
- **Bookmarklet**: кнопка-закладка для будь-якого кулінарного сайту
  (CORS `allow-*`, сторінка `/bookmarklet`).

## [0.2.0]

### Added
- Книга рецептів: JSON export/import, пошук по назві/інгредієнтах (`?q=`),
  фільтр за тегами (`?tag=`), керування тегами.
- Парсинг дробів: `1/2 cup`, `½`, `0.5`, `1,5` → нормалізовані кількості
  (`app/quantities.py`), `ingredients_parsed` у відповіді extraction.
- Вкладені `HowToSection`/`HowToStep` у JSON-LD рекурсивно розгортаються
  у плоский список кроків.

## [0.1.0] — alpha

### Added
- 3-tier extraction pipeline: JSON-LD → microdata → евристики.
- SQLite: кеш extraction (24 год) + книга рецептів.
- Односторінковий UI без фреймворків + printable view.
- Bookmarklet (перший prototype), CI- воркфлоу pytest.

[Unreleased]: https://github.com/bigpi/recipe-distiller/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/bigpi/recipe-distiller/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/bigpi/recipe-distiller/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bigpi/recipe-distiller/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/bigpi/recipe-distiller/releases/tag/v0.1.0-alpha
