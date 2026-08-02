from skills.recommendation_skill import RecommendationSkill

skill = RecommendationSkill()

intent_data = {
    "departure_city": "Amman",
    "budget": 1500,
    "currency": "USD",
    "departure_date": "2026-07-29",
    "return_date": "2026-08-03",
}

result = skill.execute(intent_data)

print(result)