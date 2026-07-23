from skills.hotel_skill import HotelSkill
import json

skill = HotelSkill()

result = skill.execute({
    "location": "Dubai",
    "check_in": "2026-08-10",
    "check_out": "2026-08-15",
    "adults": 2,
})

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("Saved to result.json")