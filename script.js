const translations = window.DT_TRANSLATIONS || {};
const supportedLanguages = ['sk', 'cs', 'en'];
const pageName = location.pathname.endsWith('privacy.html')
  ? 'privacy'
  : location.pathname.endsWith('terms.html')
    ? 'terms'
    : 'home';

const readLanguage = () => {
  try {
    const saved = localStorage.getItem('daily-thunder-language');
    if (supportedLanguages.includes(saved)) return saved;
  } catch (_) {
    // The page still works when local storage is blocked.
  }
  const browserLanguage = (navigator.language || '').toLowerCase();
  if (browserLanguage.startsWith('cs')) return 'cs';
  if (browserLanguage.startsWith('en')) return 'en';
  return 'sk';
};

let activeLanguage = readLanguage();
let activeNewsData = null;

const translate = (key, language = activeLanguage) => (
  translations[language]?.[key]
  ?? translations.sk?.[key]
  ?? key
);

const applyLanguage = (language, persist = true) => {
  activeLanguage = supportedLanguages.includes(language) ? language : 'sk';
  document.documentElement.lang = activeLanguage;

  document.querySelectorAll('[data-i18n]').forEach((element) => {
    element.textContent = translate(element.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-html]').forEach((element) => {
    element.innerHTML = translate(element.dataset.i18nHtml);
  });
  document.querySelectorAll('[data-i18n-aria]').forEach((element) => {
    element.setAttribute('aria-label', translate(element.dataset.i18nAria));
  });
  document.querySelectorAll('[data-language-select]').forEach((select) => {
    select.value = activeLanguage;
  });

  document.title = translate(`meta.${pageName}.title`);
  const description = document.querySelector('[data-i18n-meta-description]');
  if (description) description.content = translate(`meta.${pageName}.description`);

  if (persist) {
    try {
      localStorage.setItem('daily-thunder-language', activeLanguage);
    } catch (_) {
      // Language switching remains available for the current page.
    }
  }

  document.dispatchEvent(new CustomEvent('daily-thunder-language-change', {
    detail: { language: activeLanguage },
  }));
};

document.querySelectorAll('[data-language-select]').forEach((select) => {
  select.addEventListener('change', (event) => applyLanguage(event.target.value));
});
applyLanguage(activeLanguage, false);

const header = document.querySelector('[data-header]');
const menuToggle = document.querySelector('[data-menu-toggle]');
const nav = document.querySelector('[data-nav]');

const updateHeader = () => header?.classList.toggle('scrolled', window.scrollY > 24);
updateHeader();
window.addEventListener('scroll', updateHeader, { passive: true });

menuToggle?.addEventListener('click', () => {
  const open = menuToggle.getAttribute('aria-expanded') !== 'true';
  menuToggle.setAttribute('aria-expanded', String(open));
  nav?.classList.toggle('open', open);
});

nav?.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => {
    menuToggle?.setAttribute('aria-expanded', 'false');
    nav?.classList.remove('open');
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -35px' });

document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
document.querySelectorAll('[data-year]').forEach((element) => {
  element.textContent = String(new Date().getFullYear());
});

const localeFor = (language) => ({ sk: 'sk-SK', cs: 'cs-CZ', en: 'en-GB' }[language] || 'sk-SK');

const formatNewsDate = (date) => {
  const value = new Date(`${date}T12:00:00`);
  return new Intl.DateTimeFormat(localeFor(activeLanguage), {
    day: 'numeric', month: 'numeric', year: 'numeric',
  }).format(value);
};

const formatUpdatedDate = (date) => {
  const value = new Date(date);
  return new Intl.DateTimeFormat(localeFor(activeLanguage), {
    day: 'numeric', month: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(value);
};

const legacyCategoryKey = (item) => {
  if (item.kind === 'update') return 'update';
  const labels = {
    'VÝVOJ': 'development', 'DEVELOPMENT': 'development', EVENT: 'event', ESPORTS: 'esports',
    SHOP: 'shop', MARKET: 'market', DECALS: 'decals', 'FAIR PLAY': 'fair_play', SPECIAL: 'special',
    NOVINKA: 'news', NEWS: 'news', UPDATE: 'update',
  };
  return labels[item.category] || 'news';
};

const createNewsCard = (item) => {
  const card = document.createElement('a');
  card.className = 'news-card reveal visible';
  card.href = item.url;
  card.target = '_blank';
  card.rel = 'noopener noreferrer';

  const meta = document.createElement('span');
  meta.className = 'news-meta';
  const time = document.createElement('time');
  time.dateTime = item.date;
  time.textContent = formatNewsDate(item.date);
  const category = document.createElement('b');
  const categoryKey = item.category_key || legacyCategoryKey(item);
  category.dataset.i18n = `category.${categoryKey}`;
  category.textContent = translate(category.dataset.i18n);
  meta.append(time, category);

  const title = document.createElement('h3');
  title.textContent = item.title;
  const summary = document.createElement('p');
  summary.textContent = item.summary;
  const link = document.createElement('span');
  link.className = 'card-link';
  link.dataset.i18n = 'news.read';
  link.textContent = translate('news.read');

  card.append(meta, title, summary, link);
  return card;
};

const renderWarThunderNews = (data) => {
  const grid = document.querySelector('[data-news-grid]');
  if (!grid || !Array.isArray(data?.items) || data.items.length === 0) return;
  activeNewsData = data;
  grid.replaceChildren(...data.items.slice(0, 6).map(createNewsCard));
  const updated = document.querySelector('[data-news-updated]');
  if (updated && data.updated_at) updated.textContent = formatUpdatedDate(data.updated_at);
};

const loadWarThunderNews = async () => {
  if (!document.querySelector('[data-news-grid]')) return;
  if (window.DT_NEWS_DATA) {
    renderWarThunderNews(window.DT_NEWS_DATA);
    return;
  }
  if (window.location.protocol === 'file:') return;

  try {
    const response = await fetch('data/war-thunder-news.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderWarThunderNews(await response.json());
  } catch (error) {
    console.info('Using the last embedded War Thunder radar.', error);
  }
};

document.addEventListener('daily-thunder-language-change', () => {
  if (activeNewsData) renderWarThunderNews(activeNewsData);
});
loadWarThunderNews();
