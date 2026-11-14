import os
from PIL import Image, ImageDraw, ImageFont

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads", "demo")
os.makedirs(output_dir, exist_ok=True)

# Define items with colors and labels
items = [
    ("bottle_drinkware.png", "Stainless Steel Flask", "#0284c7", "#e0f2fe", "Bottles & Drinkware"),
    ("jacket_clothing.png", "Warm Campus Jacket", "#4f46e5", "#eef2ff", "Clothing & Accessories"),
    ("backpack_bags.png", "College Laptop Backpack", "#7c3aed", "#f5f3ff", "Bags"),
    ("keys_cards.png", "Dorm Room Keys & Tag", "#ea580c", "#fff7ed", "Keys & Cards"),
    ("sports_equipment.png", "Badminton Racket & Grip", "#16a34a", "#f0fdf4", "Sports Equipment"),
    ("personal_items.png", "Spectacles in Matte Case", "#d97706", "#fffbeb", "Personal Items"),
    ("misc_item.png", "Lab Protective Glasses", "#475569", "#f8fafc", "Miscellaneous"),
    ("phone_electronic.png", "Smart Smartphone & Case", "#2563eb", "#eff6ff", "Electronics"),
    ("wallet_bags.png", "Brown Leather Wallet", "#b45309", "#fef3c7", "Bags"),
    ("idcard_documents.png", "University Student ID", "#0d9488", "#ccfbf1", "Books & Documents"),
    ("tumbler_drinkware.png", "Insulated Travel Mug", "#0891b2", "#ecfeff", "Bottles & Drinkware"),
    ("umbrella_clothing.png", "Compact Black Umbrella", "#334155", "#f1f5f9", "Clothing & Accessories"),
]

for filename, title, border_col, bg_col, category in items:
    path = os.path.join(output_dir, filename)
    if os.path.exists(path):
        continue
    img = Image.new("RGBA", (600, 450), color=bg_col)
    draw = ImageDraw.Draw(img)
    
    # Outer border and banner
    draw.rectangle([10, 10, 590, 440], outline=border_col, width=4)
    draw.rectangle([10, 10, 590, 70], fill=border_col)
    
    # Header text
    draw.text((25, 25), category.upper(), fill="#ffffff")
    
    # Center decorative frame
    draw.rounded_rectangle([60, 110, 540, 360], radius=15, outline=border_col, fill="#ffffff", width=2)
    
    # Title in center
    draw.text((80, 190), title, fill="#1e293b")
    draw.text((80, 240), f"Category: {category}", fill="#64748b")
    draw.text((80, 270), "Found It University Portal Verified Item", fill="#94a3b8")
    
    # Footer
    draw.rectangle([10, 400, 590, 440], fill="#f1f5f9")
    draw.text((25, 412), "Official Campus Found Report - Reference Demo Asset", fill="#64748b")
    
    img.convert("RGB").save(path, "PNG")

print("Demo images created successfully.")
