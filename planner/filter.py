def filter_poi(points, exclude_names=None, exclude_categories=None, exclude_tags=None):
    """
    Убирает из списка POI те, которые:
     - содержат в имени любое из exclude_names
     - принадлежат к category из exclude_categories
     - имеют OSM-тег (key или value) из exclude_tags
    """
    exclude_names      = {n.lower() for n in (exclude_names or [])}
    exclude_categories = {c.lower() for c in (exclude_categories or [])}
    exclude_tags       = {t.lower() for t in (exclude_tags or [])}

    filtered = []
    for p in points:
        props    = p.get("properties", {})
        name     = props.get("name", "").lower()
        category = props.get("category", "").lower()
        tags     = {k.lower(): v.lower() for k, v in props.get("tags", {}).items()}

        # 1) по имени
        if any(ex in name for ex in exclude_names):
            continue

        # 2) по категории
        if any(ex in category for ex in exclude_categories):
            continue

        # 3) по любому тегу
        #    – ключ тега или его значение
        skip = False
        for t in exclude_tags:
            if t in tags.keys() or t in tags.values():
                skip = True
                break
        if skip:
            continue

        filtered.append(p)
    return filtered
