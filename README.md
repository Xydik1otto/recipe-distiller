# 🍲 Recipe Distiller — «Just the recipe»

![tests](https://github.com/bigpi/recipe-distiller/actions/workflows/tests.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.12+-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![version](https://img.shields.io/badge/version-0.3.0-orange)

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

## Як це працює — 3-tier pipeline

```
                    ┌─────────────────────────────┐
   URL ──httpx──▶   │  fetch: retries + mobile UA │
                    └──────────────┬──────────────┘
                                   ▼
        ┌──────────────────────────────────────────────────┐
        │  TIER 1  JSON-LD  <script type="application/ld+  │  ← найнадійніше
        │          json"> schema.org/Recipe (@graph теж)   │
        ├──────────────────────────────────────────────────┤
        │  TIER 2  Microdata  itemscope / itemprop         │  ← fallback
        ├──────────────────────────────────────────────────┤
        │  TIER 3  Евристики: ul/ol біля "Ingredients" /   │  ← останній шанс
        │          "Instructions" / "Directions"           │
        └──────────────────────────┬───────────────────────┘
                                   ▼
          нормалізація кількостей (½, 1/2, 0.5 → 0.5 + ingredients_parsed)
                                   ▼
        {title, servings, times, ingredients[], steps[], canonical_url}
                                   ▼
              SQLite: кеш (24 год) + книга рецептів (теги, пошук,
              export/import JSON) + printable view
```

Перший рівень, що повернув інгредієнти/кроки, виграє; скрипти, навігація та
реклама видаляються перед парсингом нижніх рівнів. Вкладені `HowToSection`
(«For the dough» → HowToStep…) рекурсивно розгортаються у плоский список кроків.

Результат:

```json
{
  "title": "Grandma's Borscht",
  "servings": "6 servings",
  "prep_time": "20 min", "cook_time": "1 hr", "total_time": "1 hr 20 min",
  "ingredients": ["3 beets, grated", "1/2 cup sour cream"],
  "ingredients_parsed": [{"qty": 3.0, "unit": "", "name": "beets, grated"}],
  "steps": ["Grate the beets.", "For the dough", "Mix flour and eggs."],
  "canonical_url": "https://example.com/borscht"
}
```

## Швидкий старт

```bash
git clone https://github.com/bigpi/recipe-distiller.git
cd recipe-distiller
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000

pytest                               # 61 тест, без мережі — фіксовані HTML-фікстури
```

## Bookmarklet

Перетягни цей код у панель закладок — на сторінці будь-якого рецепта один клік
витягне рецепт, збереже у книгу і відкриє чисту printable-версію:

```javascript
javascript:(async()=>{const b='http://127.0.0.1:8000';try{const r=await fetch(b+'/api/recipes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:location.href})});const d=await r.json();if(d.id)window.open(b+'/print/'+d.id);else alert('No recipe found: '+(d.detail||''));}catch(e){alert('Recipe Distiller not running on '+b)}})()
```

(Сервер має бути запущений локально; сторінка-кнопка для перетягування —
`/bookmarklet`.)

## API

| Метод | Шлях | Що робить |
|---|---|---|
| POST | `/api/extract` `{url}` | завантажити + витягти рецепт (кеш у SQLite на 24 год) |
| POST | `/api/recipes` `{url}` | витягти і зберегти у книгу рецептів |
| GET | `/api/recipes?q=&tag=` | список; пошук по назві/інгредієнтах, фільтр за тегом |
| PUT | `/api/recipes/{id}/tags` `{tags: []}` | встановити теги |
| GET | `/api/recipes/export` | експорт усіх збережених у JSON |
| POST | `/api/recipes/import` | імпорт з export-формату (`{"recipes":[…]}` або `[…]`) |
| POST | `/api/scale` `{recipe, servings\|factor}` | перерахунок кількостей під нові порції |
| POST | `/api/recipes/{id}/scale` `{servings}` | масштабувати збережений рецепт |
| POST | `/api/shopping-list` `{recipe_ids: []}` | об'єднати інгредієнти кількох рецептів |
| GET | `/api/plan` | план на тиждень (7 слотів Пн–Нд) |
| PUT | `/api/plan` `{slot, recipe_id\|null}` | призначити/очистити слот |
| GET | `/api/plan/shopping-list` | список покупок, згенерований з плану |
| GET | `/bookmarklet` | сторінка з кнопкою bookmarklet (drag) |
| GET | `/api/recipes/{id}` | один збережений рецепт |
| DELETE | `/api/recipes/{id}` | видалити |
| GET | `/print/{id}` | printable view (для друку/PDF) |
| GET | `/` | веб-UI: поле URL → картка рецепта → Save |

## Структура

- `app/extractor.py` — JSON-LD → microdata → евристики; рекурсивний
  HowToSection/HowToStep; очищення від реклами.
- `app/quantities.py` — парсинг кількостей: `1/2`, `½`, `0.5`, `1 1/2`, `1,5` →
  нормалізований float + зворотне pretty-форматування.
- `app/fetcher.py` — httpx + retries + mobile UA fallback.
- `app/db.py` — SQLite: кеш extraction + книга рецептів (теги, пошук,
  export/import).
- `app/main.py` — FastAPI endpoints.
- `static/index.html` — односторінковий UI (без фреймворків).
- `tests/fixtures/` — зафіксовані HTML-сторінки (JSON-LD, JSON-LD із секціями,
  дроби, microdata, heuristic, не-рецепт) — тести не ходять у мережу.

## Статус

**v0.3.0**:

- Extraction pipeline: JSON-LD (з @graph, вкладеними HowToSection/HowToStep) →
  microdata → евристики; нормалізація кількостей (`½`, `1/2`, `0.5` → parsed qty).
- Книга рецептів: пошук по назві/інгредієнтах, теги, export/import JSON.
- Bookmarklet: кнопка-закладка для будь-якого сайта (CORS, `/bookmarklet`).
- Serving scaling: порції ×N з перерахунком кількостей (`/api/scale`).
- Shopping list: об'єднання інгредієнтів кількох рецептів (`1 cup` + `2 cups` → `3 cups`).
- Meal plan: 7 слотів на тиждень (drag & drop) + автогенерація списку покупок з плану.
- Printable view, кеш на 24 год; 61 тест, без мережі.

Дорожня карта — [PLAN.md](PLAN.md).

## Ліцензія

[MIT](LICENSE) © bigpi
