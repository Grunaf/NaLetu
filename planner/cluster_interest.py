def calculate_cluster_interest(clusters):
    """
    Подсчитать интересность каждой локации на основе total_interest_score POI внутри неё.
    """
    cluster_scores = {}

    for cluster_id, features in clusters.items():
        scores = []
        for feature in features:
            properties = feature.get("properties", {})
            score = properties.get("total_interest_score", 0)
            scores.append(score)
        if scores:
            avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0
        cluster_scores[cluster_id] = avg_score

    return cluster_scores
