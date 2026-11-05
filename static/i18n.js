/* Recipe Distiller i18n — UA/EN only (no other locales by design).
   Auto-detects the browser language, persists the choice in localStorage,
   translates static elements via data-i18n / data-i18n-ph / data-i18n-title
   and dynamic strings via t(key). */
const I18N = {
  ua: {
    tagline: 'Встав посилання на рецепт — отримай лише рецепт, без життя-історій та реклами.',
    url_ph: 'https://example.com/borscht',
    extract: 'Extract',
    subst_summary: '🔁 Заміни інгредієнтів (масло ↔ маргарин, тощо)',
    subst_title: 'Заміна',
    book: '📖 Моя книга рецептів',
    search_ph: 'Пошук: назва або інгредієнт…',
    tag_ph: 'тег…',
    sort_new: 'спочатку нові (дата додавання)',
    sort_rating: 'за рейтингом',
    sort_title: 'за назвою',
    favonly: 'лише ♥',
    shop_selected: '🛒 Список покупок (обрані)',
    plan_title: '📅 План на тиждень',
    plan_hint: 'Перетягни рецепт зі списку вище на день — або клікни слот, щоб призначити перший збережений.',
    shop_plan: '🛒 Список покупок з плану',
    export_link: '⬇ Export JSON',
    export_csv: '⬇ Export CSV',
    delete_confirm: 'Видалити рецепт назавжди?',
    import_btn: '⬆ Import JSON',
    ingredients: 'Ingredients',
    steps: 'Steps',
    servings_ph: 'порцій',
    rescale: '× перерахувати',
    reset_checks: '☑ скидання',
    save: '💾 Save',
    saved_ok: '✅ Saved',
    saved_err: '❌ Error',
    original: 'original ↗',
    empty_book: 'Ще нічого не збережено.',
    distilling: '⏳ Дістаю рецепт…',
    favorite_title: 'улюблене',
    tags_title: 'теги',
    delete_title: 'видалити рецепт',
    pick_aria: 'обрати для списку покупок',
    stars_aria: 'зірок',
    clear_slot: 'звільнити слот',
    not_now: 'не зараз',
    free_slot: '— вільно —',
    shop_list: 'Список покупок',
    shop_list_plan: 'Список покупок з плану',
    recipes_suffix: 'рецептів',
    empty_list: 'Список порожній.',
    print_list: '🖨 Друк списку',
    imported: '⬆ Імпортовано',
    invalid_json: '❌ Невалідний JSON',
    tags_prompt: 'Теги через кому:',
    error_suffix: '❌',
    days: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'],
    demo_invite: 'Книга порожня. Хочеш спробувати на демо-рецептах?',
    demo_btn: '🧪 Завантажити демо',
    demo_done: '🧪 Додано демо-рецепти',
    lang_title: 'Мова інтерфейсу',
    pantry_summary: '🧊 Що є в холодильнику',
    pantry_hint: 'Впиши продукти через кому — застосунок покаже, які збережені рецепти вже можна готувати.',
    pantry_ph: 'буряк, картопля, яйця…',
    pantry_save: '💾 Зберегти',
    pantry_saved: '🧊 Список продуктів збережено',
    pantry_match: '🍳 Що можна готувати?',
    pantry_none: 'Книга порожня — немає чого зіставляти.',
    pantry_missing: 'бракує',
  },
  en: {
    tagline: 'Paste a recipe link — get just the recipe, no life stories, no ads.',
    url_ph: 'https://example.com/borscht',
    extract: 'Extract',
    subst_summary: '🔁 Ingredient substitutions (butter ↔ margarine, etc.)',
    subst_title: 'Substitute',
    book: '📖 My recipe book',
    search_ph: 'Search: title or ingredient…',
    tag_ph: 'tag…',
    sort_new: 'newest first (date added)',
    sort_rating: 'by rating',
    sort_title: 'by title',
    favonly: '♥ only',
    shop_selected: '🛒 Shopping list (selected)',
    plan_title: '📅 Weekly meal plan',
    plan_hint: 'Drag a recipe from the list above onto a day — or click a slot to assign the first saved recipe.',
    shop_plan: '🛒 Shopping list from plan',
    export_link: '⬇ Export JSON',
    export_csv: '⬇ Export CSV',
    delete_confirm: 'Delete this recipe permanently?',
    import_btn: '⬆ Import JSON',
    ingredients: 'Ingredients',
    steps: 'Steps',
    servings_ph: 'servings',
    rescale: '× rescale',
    reset_checks: '☑ reset',
    save: '💾 Save',
    saved_ok: '✅ Saved',
    saved_err: '❌ Error',
    original: 'original ↗',
    empty_book: 'Nothing saved yet.',
    distilling: '⏳ Distilling the recipe…',
    favorite_title: 'favorite',
    tags_title: 'tags',
    delete_title: 'delete recipe',
    pick_aria: 'pick for shopping list',
    stars_aria: 'stars',
    clear_slot: 'clear slot',
    not_now: 'not now',
    free_slot: '— free —',
    shop_list: 'Shopping list',
    shop_list_plan: 'Shopping list from plan',
    recipes_suffix: 'recipes',
    empty_list: 'The list is empty.',
    print_list: '🖨 Print list',
    imported: '⬆ Imported',
    invalid_json: '❌ Invalid JSON',
    tags_prompt: 'Tags, comma-separated:',
    error_suffix: '❌',
    days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    demo_invite: 'Your book is empty. Want to try it on demo recipes?',
    demo_btn: '🧪 Load demo',
    demo_done: '🧪 Demo recipes added',
    lang_title: 'Interface language',
    pantry_summary: '🧊 What is in the fridge',
    pantry_hint: 'Enter the food you have, comma-separated — the app shows which saved recipes you can already cook.',
    pantry_ph: 'beetroot, potatoes, eggs…',
    pantry_save: '💾 Save',
    pantry_saved: '🧊 Pantry list saved',
    pantry_match: '🍳 What can I cook?',
    pantry_none: 'The book is empty — nothing to match.',
    pantry_missing: 'missing',
  },
};

let _lang = null;
try { _lang = localStorage.getItem('rd-lang'); } catch {}
if (_lang !== 'ua' && _lang !== 'en') {
  _lang = (navigator.language || '').toLowerCase().startsWith('uk') ? 'ua' : 'en';
}
let _dict = I18N[_lang];

function t(key) { return _dict[key] ?? I18N.en[key] ?? key; }

function applyI18n() {
  document.documentElement.lang = _lang === 'ua' ? 'uk' : 'en';
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.dataset.i18nTitle); });
  document.querySelectorAll('[data-i18n-label]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nLabel)); });
  document.querySelectorAll('#sort option[data-i18n]').forEach(o => { o.textContent = t(o.dataset.i18n); });
}

function setLang(lang) {
  if (!I18N[lang]) return;
  _lang = lang; _dict = I18N[lang];
  try { localStorage.setItem('rd-lang', lang); } catch {}
  applyI18n();
  document.querySelectorAll('.langbtn').forEach(b =>
    b.classList.toggle('on', b.dataset.lang === lang));
}

function currentLang() { return _lang; }
