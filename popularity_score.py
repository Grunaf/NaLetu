import json
from shapely.geometry import shape
import time
import requests
import urllib.parse

def calculate_base_interest_score(properties, geom):
    score = 0.0
    tourism = properties.get('tourism')
    if   tourism == 'museum':    return 100.0
    elif tourism == 'gallery':   return  90.0
    elif tourism == 'aquarium':  return  90.0
    elif tourism == 'zoo':       return  85.0
    elif tourism == 'viewpoint': return  75.0
    elif tourism == 'attraction':score =  70.0

    amenity = properties.get('amenity')
    if   amenity == 'arts_centre': score = max(score, 70.0)
    elif amenity == 'theatre':     score = max(score, 80.0)

    historic = properties.get('historic')
    if historic in ('castle','fort','city_gate','memorial','monument',
                    'arch','monastery','ship'):
        return 95.0
    elif isinstance(historic, str) and historic.strip():
        score = max(score, 60.0)

    return float(score)


def calculate_popularity_score(properties, geom):
    popularity_score = 0
    if properties.get('wikipedia'): popularity_score += 30
    if properties.get('wikidata'):   popularity_score += 20
    return float(popularity_score)

def calculate_total_interest_score(properties, geom):
    base  = properties.get('base_interest_score',  0.0)
    pop   = properties.get('popularity_score',     0.0)
    norm  = properties.get('normalized_wiki_views',0.0)
    # я убрал user_interest_match, его вы рассчитываете уже в боте
    return float(0.35*base + 0.25*pop + 0.25*norm*100)

def get_wikipedia_views(wikipedia_tag):
    if not wikipedia_tag or ':' not in wikipedia_tag:
        return 0
    lang, page = wikipedia_tag.split(':', 1)
    if lang != 'ru':
        print(f"⚡ Пропускаем не-русскую статью: {wikipedia_tag}")
        return 0
    title = urllib.parse.quote(page.replace(' ', '_'))
    url = (
      f"https://wikimedia.org/api/rest_v1/metrics/pageviews/"
      f"per-article/ru.wikipedia.org/all-access/user/"
      f"{title}/monthly/20240401/20240430"
    )
    print(f"🔵 Запрашиваем просмотры для «{wikipedia_tag}»: {url}")
    try:
        r = requests.get(url, headers={'User-Agent':'MyResearchBot/1.0'})
        time.sleep(0.3)
        j = r.json()
        views = j.get('items',[{}])[0].get('views',0)
        print(f"✅ Получили {views} просмотров")
        return views
    except Exception as e:
        print(f"❌ Ошибка при запросе {wikipedia_tag}: {e}")
        return 0
    
in_path  = "Mus-Aqua-Zoo-Gal-View-Attrac(Peter)v2.geojson"
out_path = "with_popularity_(MAqZGVA)(Peter)v2.geojson"
print(f"📂 Читаем файл {in_path}…")
with open(in_path, encoding="utf-8") as f:
    geo = json.load(f)
print("✅ Файл загружен.")

# === 4) Пробегаемся по всем feature ===
print("⏳ Собираем Wikipedia views…")
for feat in geo.get("features", []):
    props = feat.setdefault("properties", {})
    # подпишем счётчики просмотров прямо здесь
    wiki_tag = props.get("wikipedia")
    props["wiki_views"] = get_wikipedia_views(wiki_tag)
    # нормализовать будем после цикла
print("✅ Все Wikipedia views собраны.")

# найдём максимум просмотров
max_views = max(f["properties"]["wiki_views"] for f in geo["features"]) or 1
print(f"ℹ️ Максимум просмотров = {max_views}, нормализуем…")
# и сразу добавим normalized_wiki_views
for feat in geo["features"]:
    props = feat["properties"]
    props["normalized_wiki_views"] = float(props["wiki_views"] / max_views)
print("✅ Нормализация завершена.")

# добавляем три поля interest внутри того же цикла
print("⏳ Считаем interest-оценки…")
for feat in geo["features"]:
    props = feat["properties"]
    # geometry shapely:
    try:
        geom = shape(feat["geometry"])
    except:
        geom = None

    # считаем и записываем
    props["base_interest_score"]  = calculate_base_interest_score (props, geom)
    props["popularity_score"]     = calculate_popularity_score     (props, geom)
    props["total_interest_score"] = calculate_total_interest_score(props, geom)
print("✅ Вычислены все interest-оценки.")

# === 5) Сохраняем обратно в geojson ===
print(f"💾 Сохраняем в файл {out_path}…")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(geo, f, ensure_ascii=False, indent=2)

print(f"✅ Файл «{out_path}» создан с новыми колонками.")
