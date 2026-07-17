DAILY THUNDER WEBSITE

Náhľad stránky:
1. Otvorte súbor index.html dvojklikom, alebo
2. spustite lokálny webový server v tomto priečinku.

Obsah:
- index.html — domovská stránka
- privacy.html — ochrana súkromia pre web a Daily Thunder Publisher
- terms.html — podmienky používania
- styles.css — vzhľad a responzívna mobilná verzia
- script.js — menu a jemné animácie
- assets/ — logo, banner a favicon
- data/war-thunder-news.json — posledná uložená verzia War Thunder radaru
- data/war-thunder-news.js — rovnaké novinky dostupné aj pri otvorení webu priamo zo súboru
- translations.js — slovenská, česká a anglická verzia rozhrania a právnych stránok
- scripts/update_war_thunder_news.py — načítanie noviniek a patch notes
- .github/workflows/ — automatická aktualizácia každých 6 hodín po nasadení na GitHub Pages

AUTOMATICKÉ NOVINKY
Po nasadení stránky na GitHub Pages sa workflow spustí každých 6 hodín.
Načíta články a patch notes iba z oficiálneho webu War Thunder, spojí ich
podľa dátumu a uloží 6 najnovších položiek. Pri chybe zostáva zobrazená
posledná úspešná verzia.

Pred verejným nasadením doplňte finálnu doménu do TikTok Developer Portalu.
