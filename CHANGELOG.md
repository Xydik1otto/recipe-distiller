# Changelog

Усі помітні зміни проєкту документуються тут.

Формат — [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/),
версіонування — [Semantic Versioning](https://semver.org/lang/uk/).

## [Unreleased]

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
- `CHANGELOG.md`, `FUNDING.yml` (GitHub Sponsors), favicon + OG-мета,
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
