import random

def recommend_price(category, weight, location):

    base_prices = {
        "plastic": 18,
        "metal": 45,
        "paper": 12,
        "ewaste": 70,
        "glass": 10
    }

    base = base_prices.get(category, 20)

    # weight impact
    if weight > 50:
        base *= 0.9
    elif weight < 5:
        base *= 1.1

    # location factor
    urban = ["delhi", "mumbai", "bangalore", "hyderabad", "pune"]
    if location.lower() in urban:
        base *= 1.12
        demand = "High"
    else:
        base *= 0.95
        demand = "Moderate"

    price = round(base, 2)

    # price range
    min_price = round(price * 0.88, 2)
    max_price = round(price * 1.18, 2)

    # resale score simulation
    resale_score = random.randint(60, 90)

    # market message
    insights = {
        "plastic": "Artists use plastic for eco-sculptures",
        "metal": "Metal scrap has strong resale demand",
        "paper": "Paper scrap used for recycled art",
        "ewaste": "E-waste valuable for creative installations",
        "glass": "Glass scrap used in mosaic artwork"
    }

    insight_msg = insights.get(category, "Stable demand material")

    return {
        "price": price,
        "min": min_price,
        "max": max_price,
        "demand": demand,
        "resale": resale_score,
        "insight": insight_msg
    }
