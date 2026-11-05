# 🤝 Contributing to Recipe Distiller

Дякуємо за інтерес! Проєкт маленький і локальний за духом — будь-яка допомога
вітається. / Thanks for your interest! The project is small and local-first —
all help is welcome.

## Як допомогти / How to help

- **Bug reports / ідеї** — відкрийте Issue за шаблоном (`.github/ISSUE_TEMPLATE/`),
  українською або англійською / open an Issue using the templates, in Ukrainian
  or English.
- **Pull requests** — форк → гілка `feature/<щось>` → PR.
  / fork → branch `feature/<something>` → PR.

## Перед PR / Before you PR

```bash
pip install -e ".[dev]"
pytest            # усі тести мають бути зелені / all tests must pass
```

- Кожна фіча — з тестом / every feature comes with a test.
- Стиль: маленькі коміти, зрозумілі повідомлення / small commits, clear messages.
- **Мови інтерфейсу: лише українська та англійська.** Російську локалізацію
  не додавати — це свідоме рішення власника проєкту. / UI locales: Ukrainian
  and English only. **No Russian localization** — a deliberate project decision;
  such PRs will be declined.

## Що точно потрібно / What's especially needed

- парсинг складних сайтів (TIER-3 евристики в `app/extractor.py`);
- база замін інгредієнтів (`app/substitutions.py`) — нові пари;
- щільність інгредієнтів для конвертації (`app/convert.py`);
- переклад-вичитка English рядків у `static/i18n.js`.

## Ліцензія / License

Вносячи зміни, ви погоджуєтеся, що вони публікуються під ліцензією проєкту
(MIT, див. `LICENSE`). / By contributing you agree your changes are released
under the project's MIT license.
