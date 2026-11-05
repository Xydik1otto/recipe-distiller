# PLAN — Recipe Distiller («Just the recipe»)

## 1. Цільова аудиторія

- **Домашні кулінари**, які зберігають рецепти з інтернету і втомилися від
  скролінгу рекламних лонгрідів.
- **Мобільні користувачі** на повільному з'єднанні: 5 МБ сторінки проти 30 КБ
  чистого рецепта.
- **Люди з друком/AI-асистентами**: чистий structured рецепт легко принтурувати
  або скормити голосному асистенту на кухні.

## 2. MVP scope (реалізовано, v0.1.0)

- FastAPI, endpoint `POST /api/extract {url}`.
- Завантаження: httpx + повторні спроби + mobile UA fallback.
- Extraction: JSON-LD (основний) → microdata (fallback) → евристики
  (ul/ol біля Ingredients/Instructions) — повертає title, servings,
  prep/cook/total time, ingredients[], steps[], canonical_url.
- Кеш у SQLite (TTL 24 год).
- Веб-UI: одна сторінка (input URL → картка рецепта, кнопка Save → локальна
  книга рецептів у SQLite, список збережених, printable view `/print/{id}`).
- Тести: pytest на зафіксованих HTML-фікстурах (JSON-LD, microdata, heuristic,
  не-рецепт) — повністю офлайн.

## 3. Архітектура

```
POST /api/extract ──▶ cache hit? ──▶ так ──▶ 200 {source: "cache", recipe}
                        │ ні
                        ▼
                 fetch_html (httpx, retries, desktop→mobile UA)
                        ▼
                 extract_from_html:
                   1) JSON-LD script[type=application/ld+json] → @graph/Recipe
                   2) itemscope schema.org/Recipe itemprop
                   3) headings → find_next(ul/ol)
                        ▼
                 clean recipe dict ──▶ SQLite cache ──▶ 200 {source:"live", recipe}
```

Дані: `cache(url, data, fetched_at)`, `saved(id, url, title, data, saved_at)`.
Без фонових воркерів; все синхронно, один файл БД.

## 4. Roadmap

Дорожня карта повністю безкоштовна: усі фічі — open-source, без Pro-рівнів
і платних підписок.

- **v0.2 — extraction quality**: підтримка HowToSection/HowToStep вкладеностей,
  об'єднання кількох JSON-LD вузлів, fraction-парсинг кількостей (½ cup → 0.5),
  метрики success-rate по доменах.
- **v0.3 — browser extension + bookmarklet**: «витягни рецепт звідси» одним
  кліком без копіювання URL.
- **v0.4 — імпорт/експорт**: RecipeML / JSON-LD export, імпорт bookmarks,
  пошук по книзі, теги.
- **v0.5 — meal planning**: тижневий план + автоматичний shopping list з
  вибраних рецептів (кількості складаються).
- **v1.0 — стабільний реліз**: синхронізація між пристроями, спільні книги,
  PDF-друк — усе безкоштовно, 100% open-source.

## 5. Ліцензування

Проєкт — 100% безкоштовний open-source (MIT). Жодних Pro-рівнів, підписок,
донацій чи партнерських програм: жодної реклами і жодних affiliate-посилань
у продуктовому UI — це і є ціннісна пропозиція (anti-bloat як фіча, не як баг).

## 6. Ризики та мітигація

| Ризик | Мітигація |
|---|---|
| Сайти активно блокують скрейпінг (Cloudflare, bot-детекція) | mobile UA fallback, поважати robots для масових режимів; фокус на окремих URL за запитом користувача, не на краулінгу |
| Хости зламають верстку → евристики miserab| метрики per-domain success rate; користувач може виправити вручну; roadmap — LLM-free rule packs на спільноту |
| Юридичні питання (авторські права на рецепти) | зберігаємо лише факти (інгредієнти/кроки) + посилання на оригінал; рецепти як факти не підпадають під копірайт у більшості юрисдикцій |
| Google/Facebook-рецепти за логіном | явно поза MVP; тільки публічні сторінки |
| Великий трафік на важкі сайти | агресивний кеш 24 год, rate limiting |

## 7. Метрики успіху

- Extraction success rate ≥ 85% на топ-100 кулінарних сайтах.
- Час відповіді < 3 c (без кешу) / < 100 мс (з кешем).
- Retention: % користувачів, що зберегли ≥ 3 рецепти за тиждень.
