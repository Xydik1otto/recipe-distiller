# Security Policy / Політика безпеки

## Supported versions / Підтримувані версії

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ |
| < 1.0   | ❌ (upgrade) |

## Reporting a vulnerability / Як повідомити про вразливість

**Не відкривайте публічний Issue для вразливостей.**
/ **Do NOT open a public issue for vulnerabilities.**

- Напишіть на: **security@bigpi.dev** (або через GitHub — приватне
  повідомлення власнику репозиторію) / Email the maintainer privately, or use
  GitHub's "Report a vulnerability" (Security → Advisories).
- Опишіть: версію, кроки відтворення, очікуваний vs фактичний результат.
  / Include version, reproduction steps, expected vs actual behaviour.
- Відповідь — протягом 7 днів. / Response within 7 days.

## Scope / Що в межах

Recipe Distiller — це **локальний** сервер (за замовчуванням `127.0.0.1`) і
статичне MV3-розширення. Актуальні класи проблем:

- SSRF через `/api/extract` (сервер fetch-ить довільні URL за запитом);
- XSS у відображенні витягнутого контенту (назви, інгредієнти, кроки);
- ін'єкції в SQLite-запитах;
- надмірні дозволи браузерного розширення.

Everything runs on your machine: we treat any data leaving the device
unexpectedly as a security bug.

## Дані / Data

Ніякої телеметрії немає. Книга рецептів зберігається локально у `recipes.db`.
/ No telemetry. The recipe book lives locally in `recipes.db`.
