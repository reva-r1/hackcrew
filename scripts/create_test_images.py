import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_font(size=24):
    for font_name in ["arial.ttf", "calibri.ttf", "tahoma.ttf", "seguiemj.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            pass
    return ImageFont.load_default()

def create_image(filename: str, title: str, lines: list, bg_color=(255, 255, 255), text_color=(15, 23, 42)):
    width = 900
    height = 650
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    title_font = get_font(32)
    body_font = get_font(22)
    small_font = get_font(18)

    # Header bar
    draw.rectangle([0, 0, width, 80], fill=(30, 41, 59))
    draw.text((40, 24), title, fill=(255, 255, 255), font=title_font)

    # Body lines
    y = 120
    for line in lines:
        if line.startswith("## "):
            draw.text((40, y), line[3:], fill=(14, 116, 144), font=get_font(26))
            y += 45
        elif line.startswith("- "):
            draw.text((60, y), line, fill=text_color, font=body_font)
            y += 36
        elif line == "":
            y += 18
        else:
            draw.text((40, y), line, fill=text_color, font=body_font)
            y += 34

    # Footer
    draw.line([(40, height - 50), (width - 40, height - 50)], fill=(203, 213, 225), width=1)
    draw.text((40, height - 40), "CONFIDENTIAL - INTERNAL CORPORATE POLICY ONLY", fill=(148, 163, 184), font=small_font)

    output_path = Path("data") / "test_assets" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path))
    print(f"Created {output_path} ({os.path.getsize(output_path)} bytes)")
    return str(output_path)

if __name__ == "__main__":
    create_image(
        "it_security_policy.png",
        "GLOBAL IT SECURITY & LAPTOP REPLACEMENT POLICY",
        [
            "## 1. Laptop Upgrade Schedule",
            "- All engineering laptops are eligible for replacement every 24 months.",
            "- Default developer machine: 16-inch MacBook Pro M3 Max with 64GB RAM.",
            "- Non-engineering staff receive MacBook Air 15-inch with 24GB RAM.",
            "",
            "## 2. Password & Multi-Factor Authentication",
            "- Master corporate passwords must be at least 16 characters in length.",
            "- Hardware YubiKey hardware tokens are strictly mandatory for all AWS access.",
            "- Passwords expire every 180 days with no password reuse within 10 cycles."
        ]
    )

    create_image(
        "corporate_travel_stipend.jpg",
        "CORPORATE TRAVEL & DAILY EXPENSE POLICY",
        [
            "## 1. Daily Meal & Per Diem Rates",
            "- The domestic daily meal per diem stipend is $85 per day.",
            "- The international travel meal per diem allowance is $120 per day.",
            "- Receipts are required for any single meal expense exceeding $25.",
            "",
            "## 2. Flight & Accommodation Guidelines",
            "- Economy plus is permitted for international flights exceeding 6 hours.",
            "- Hotel bookings must not exceed $250 per night in Tier 1 metropolitan areas.",
            "- Uber and Lyft rides between airport and hotel are 100% reimbursable."
        ]
    )

    create_image(
        "campus_cafeteria_perks.webp",
        "CAMPUS CAFETERIA & WELLNESS PERKS",
        [
            "## 1. Daily Catering & Meal Schedules",
            "- Gourmet hot breakfast is served daily from 8:00 AM to 10:00 AM.",
            "- Catered artisan buffet lunch is provided free every weekday at 12:30 PM.",
            "- Fresh organic cold brew and espresso bar operates until 4:30 PM.",
            "",
            "## 2. Dietary Accommodations",
            "- 100% certified Halal, Kosher, and Vegan stations are available every day.",
            "- Gluten-free snack stations are restocked on the 3rd floor pantry twice daily."
        ]
    )
