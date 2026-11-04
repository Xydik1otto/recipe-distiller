# Recipe Distiller — «Just the recipe»

URL → чистий рецепт. Без реклами, без 1200 слів про дитинство, без попапів.

## Проблема

Кулінарні сайти перетворилися на SEO-сміттєзвалища: щоб дізнатися 6 інгредієнтів,
треба прогорнути «історію бабусі», 14 рекламних блоків і попап «підпишись на
newsletter». Це масове роздратування:

- вірусні пости **«I just wanted a recipe 😫»** регулярно злітають на
  r/mildlyinfuriating та r/webdev;
- існуючий сервіс justtherecipe.food **довів попит** — люди готові користуватися
  навіть примітивним інструментом лише заради «тільки рецепт»;
- аналіз 9363 постів підтверджує стабільний **anti-bloat тренд** — користувачі
  дедалі голосніше вимагають чистого контенту.

## Як працює (MVP)

Трирівнева Extraction Pipeline:

1. **JSON-LD** `schema.org/Recipe` — основний шлях, найнадійніший.
2. **Microdata** (`itemscope`/`itemprop`) — fallback.
3. **Евристики** — `ul`/`ol` біля слів Ingredients / Instructions / Directions.

Завантаження сторінки: httpx із повторними спробами та **mobile UA fallback**
(багато сайтів віддають чистішу верстку мобільним). Результат:

```json
{
  "title": "Grandma's Borscht",
  "servings": "6 servings",
  "prep_time": "20 min", "cook_time": "1 hr", "total_time": "1 hr 20 min",
  "ingredients": ["3 beets, grated", "..."],
  "steps": ["Grate the beets.", "..."],
  "canonical_url": "https://example.com/borscht"
}
```

## Швидкий старт

```bash
cd recipe-distiller
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000

pytest                               # тести (18 шт, без мережі — фіксовані HTML-фікстури)
```

API:

| Метод | Шлях | Що робить |
|---|---|---|
| POST | `/api/extract` `{url}` | завантажити + витягти рецепт (кеш у SQLite на 24 год) |
| POST | `/api/recipes` `{url}` | витягти і зберегти у книгу рецептів |
| GET | `/api/recipes` | список збережених |
| GET | `/api/recipes/{id}` | один збережений рецепт |
| DELETE | `/api/recipes/{id}` | видалити |
| GET | `/print/{id}` | printable view (для друку/PDF) |
| GET | `/` | веб-UI: поле URL → картка рецепта → Save |

## Структура

- `app/extractor.py` — JSON-LD → microdata → евристики; очищення від реклами.
- `app/fetcher.py` — httpx + retries + mobile UA fallback.
- `app/db.py` — SQLite: кеш extraction + книга рецептів.
- `app/main.py` — FastAPI endpoints.
- `static/index.html` — односторінковий UI (без фреймворків).
- `tests/fixtures/` — зафіксовані HTML-сторінки (JSON-LD, microdata, heuristic,
  не-рецепт) — тести не ходять у мережу.

## Статус

MVP v0.1.0: extraction pipeline (3 рівні), кеш, книга рецептів, printable view,
18 тестів зелені. Дорожня карта — [PLAN.md](PLAN.md).
