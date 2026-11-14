import argparse
import random
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.audit import AdminAuditLog
from app.models.category import Category, Subcategory
from app.models.contact import ContactRequest
from app.models.item import FoundItem, ItemImage, ItemStatusHistory
from app.models.location import CampusLocation
from app.models.notification import Notification
from app.models.user import User

CATEGORIES_DATA = [
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic gadgets, devices, and digital accessories",
        "icon": "Laptop",
        "subcategories": [
            ("Mobile Phones", "mobile-phones"),
            ("Chargers & Cables", "chargers-cables"),
            ("Earphones & Airpods", "earphones-airpods"),
            ("Headphones", "headphones"),
            ("Laptops & Tablets", "laptops-tablets"),
            ("USB Drives & Storage", "usb-storage"),
            ("Calculators", "calculators"),
            ("Power Banks", "power-banks"),
        ],
    },
    {
        "name": "Bottles & Drinkware",
        "slug": "bottles-drinkware",
        "description": "Water bottles, thermal flasks, coffee tumblers, and mugs",
        "icon": "Coffee",
        "subcategories": [
            ("Water Bottles", "water-bottles"),
            ("Thermal Flasks", "thermal-flasks"),
            ("Travel Tumblers", "travel-tumblers"),
            ("Coffee Mugs", "coffee-mugs"),
        ],
    },
    {
        "name": "Clothing & Accessories",
        "slug": "clothing-accessories",
        "description": "Outerwear, hats, watches, sunglasses, and umbrellas",
        "icon": "Shirt",
        "subcategories": [
            ("Jackets & Hoodies", "jackets-hoodies"),
            ("Caps & Hats", "caps-hats"),
            ("Shoes & Footwear", "shoes-footwear"),
            ("Umbrellas", "umbrellas"),
            ("Watches", "watches"),
            ("Sunglasses", "sunglasses"),
        ],
    },
    {
        "name": "Bags",
        "slug": "bags",
        "description": "Backpacks, laptop sleeves, pouches, and wallets",
        "icon": "Briefcase",
        "subcategories": [
            ("Backpacks", "backpacks"),
            ("Laptop Bags", "laptop-bags"),
            ("Wallets", "wallets"),
            ("Pouches & Slings", "pouches-slings"),
        ],
    },
    {
        "name": "Stationery",
        "slug": "stationery",
        "description": "Notebooks, pencil cases, geometry boxes, and drawing tools",
        "icon": "PenTool",
        "subcategories": [
            ("Notebooks & Registers", "notebooks-registers"),
            ("Pens & Pencil Sets", "pens-pencils"),
            ("Pencil Cases", "pencil-cases"),
            ("Files & Folders", "files-folders"),
            ("Geometry & Drawing Kits", "geometry-kits"),
        ],
    },
    {
        "name": "Books & Documents",
        "slug": "books-documents",
        "description": "Textbooks, reference manuals, student ID cards, and official forms",
        "icon": "BookOpen",
        "subcategories": [
            ("Academic Textbooks", "academic-textbooks"),
            ("Student ID Cards", "student-id-cards"),
            ("Access Cards", "access-cards"),
            ("Certificates & Folders", "certificates-folders"),
            ("Printed Notes & Binders", "printed-notes"),
        ],
    },
    {
        "name": "Keys & Cards",
        "slug": "keys-cards",
        "description": "Hostel room keys, vehicle keys, lanyards, and transit cards",
        "icon": "Key",
        "subcategories": [
            ("Room Keys", "room-keys"),
            ("Bike & Car Keys", "vehicle-keys"),
            ("Keychains & Lanyards", "keychains-lanyards"),
            ("Smart Transit Cards", "transit-cards"),
        ],
    },
    {
        "name": "Sports Equipment",
        "slug": "sports-equipment",
        "description": "Rackets, athletic gear, sports shoes, and balls",
        "icon": "Activity",
        "subcategories": [
            ("Badminton Rackets", "badminton-rackets"),
            ("Basketballs & Footballs", "sports-balls"),
            ("Athletic Footwear", "athletic-footwear"),
            ("Gym Accessories & Bands", "gym-accessories"),
        ],
    },
    {
        "name": "Personal Items",
        "slug": "personal-items",
        "description": "Eyewear cases, grooming kits, and lunch containers",
        "icon": "Smile",
        "subcategories": [
            ("Spectacles & Cases", "spectacles-cases"),
            ("Lunch Boxes & Containers", "lunch-boxes"),
            ("Grooming & Sanitizer Kits", "grooming-kits"),
        ],
    },
    {
        "name": "Miscellaneous",
        "slug": "miscellaneous",
        "description": "Other found items not falling under specific categories",
        "icon": "HelpCircle",
        "subcategories": [
            ("Lab Coats & Aprons", "lab-coats"),
            ("Scientific Equipment", "scientific-equipment"),
            ("Unclassified Objects", "unclassified-objects"),
        ],
    },
]

CAMPUS_LOCATIONS_DATA = [
    ("Central University Library - 2nd Floor Reading Room", "Central Library", "Study tables and silent reading corner"),
    ("Main Academic Block - Ground Floor Foyer", "Main Academic Block", "Near main reception and bulletin board"),
    ("Engineering Block A - Computer Lab 3", "Engineering Complex", "Workstations and coding lab area"),
    ("Campus Cafeteria & Food Court", "Student Amenities Center", "Dining tables and beverage counters"),
    ("Auditorium - Hall 1", "Convention Center", "Seats in row D and stage lobby"),
    ("Sports Complex - Indoor Badminton Court", "Athletics Pavilion", "Courtside benches and gear rack"),
    ("Hostel Block B - Common Lounge", "Residential Quad", "Recreation room and sofa area"),
    ("Science Block C - Chemistry Lab", "Science Complex", "Lab benches and apron rack"),
    ("Student Activity Center - Music Room", "Student Plaza", "Instrument stands and rehearsal corner"),
    ("North Campus Parking Lot - Sector 2", "North Gate", "Near bicycle racks and parking row B"),
    ("Management Studies Block - Seminar Room 204", "Management Wing", "Presentation hall second floor"),
    ("Hostel Dining Mess - Hall A", "Residential Quad", "Dining area tray return counter"),
    ("University Health Center - Waiting Area", "Medical Wing", "Visitor chairs and reception desk"),
    ("Central Lawn & Amphitheatre", "Campus Commons", "Open green lawn stairs"),
    ("Civil Engineering Workshop", "Engineering Complex", "Surveying lab bench"),
    ("Administrative Complex - Registrar Office Corridor", "Admin Building", "Hallway seating near inquiry desk"),
]

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Sneha", "Aditya", "Pooja", "Rahul", "Neha",
    "Siddharth", "Kavita", "Manish", "Divya", "Karan", "Tanvi", "Nikhil", "Meera", "Varun", "Isha",
    "Arjun", "Riya", "Gaurav", "Shreya", "Kunal", "Simran", "Deepak", "Anjali", "Harsh", "Swati",
    "Yash", "Bhavna", "Abhishek", "Sakshi", "Prateek", "Nandini", "Tarun", "Payal", "Amit", "Rashmi"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Mehta", "Singh", "Kumar", "Iyer", "Nair", "Reddy",
    "Joshi", "Chopra", "Bhat", "Rao", "Deshmukh", "Kulkarni", "Malhotra", "Kapoor", "Mishra", "Saxena"
]

DEPARTMENTS = [
    "Computer Science & Engineering",
    "Electronics & Communication",
    "Mechanical Engineering",
    "Business Administration",
    "Biotechnology",
    "Information Technology",
    "Civil Engineering",
    "Physics & Applied Sciences",
    "Commerce & Economics",
    "Design & Fine Arts",
]

DEMO_IMAGE_MAP = {
    "electronics": ["earpods_electronic.png", "headphones_electronic.png", "phone_electronic.png"],
    "bottles-drinkware": ["bottle_drinkware.png", "tumbler_drinkware.png"],
    "clothing-accessories": ["jacket_clothing.png", "umbrella_clothing.png"],
    "bags": ["backpack_bags.png", "wallet_bags.png"],
    "stationery": ["book_stationery.png"],
    "books-documents": ["idcard_documents.png", "book_stationery.png"],
    "keys-cards": ["keys_cards.png"],
    "sports-equipment": ["sports_equipment.png"],
    "personal-items": ["personal_items.png"],
    "miscellaneous": ["misc_item.png"],
}

SAMPLE_ITEMS = [
    # Electronics
    ("Apple AirPods Pro in White MagSafe Case", "Found on table 14 near the silent study section. Has a subtle transparent silicone cover.", "electronics", "earphones-airpods", "Good", 1),
    ("Sony WH-1000XM4 Noise Canceling Headphones", "Black over-ear headphones left on a desk in the computer lab. Still in working condition.", "electronics", "headphones", "Excellent", 1),
    ("Samsung Galaxy S22 Smartphone", "Black smartphone with navy blue case, screen locked, found on the cafeteria bench.", "electronics", "mobile-phones", "Good", 1),
    ("Dell 65W USB-C Laptop Charger", "Black oval power adapter with braided USB-C cable left in Lab 3 power strip.", "electronics", "chargers-cables", "Fair", 1),
    ("Anker 10000mAh Power Bank", "Matte black power bank with dual USB ports and battery indicator LEDs.", "electronics", "power-banks", "Good", 1),
    ("Casio FX-991EX Scientific Calculator", "Classwiz scientific calculator with slide-on protective cover and name sticker partially visible.", "electronics", "calculators", "Good", 1),
    ("SanDisk 64GB Ultra Dual USB Drive", "Silver metallic USB drive with both Type-A and Type-C retractable connectors.", "electronics", "usb-storage", "Good", 1),
    ("OnePlus Nord Wired Bullets Earphones", "Black wired earphones with red accent cable wrapped neatly in cafeteria.", "electronics", "earphones-airpods", "Fair", 1),

    # Bottles & Drinkware
    ("Milton Thermosteel 750ml Flask", "Silver stainless steel insulated flask with a small sticker of a mountain decal.", "bottles-drinkware", "thermal-flasks", "Good", 1),
    ("Hydro Flask 32oz Wide Mouth Bottle", "Olive green water bottle with flex cap, spotted on the bleachers after badminton practice.", "bottles-drinkware", "water-bottles", "Good", 1),
    ("Starbucks Stainless Steel Travel Mug", "Matte black tumbler with flip lid and siren logo, left on library 2nd floor desk.", "bottles-drinkware", "travel-tumblers", "Excellent", 1),
    ("Tupperware Aquasafe 1L Blue Water Bottle", "Translucent blue plastic water bottle found beside the amphitheatre lawn.", "bottles-drinkware", "water-bottles", "Good", 1),
    ("Ceramic Coffee Mug with 'Code & Coffee' Text", "White ceramic mug with blue interior, found near reception desk.", "bottles-drinkware", "coffee-mugs", "Fair", 1),

    # Clothing & Accessories
    ("Puma Navy Blue Windbreaker Jacket", "Size M athletic jacket with front zip and white stripes along sleeves. Clean condition.", "clothing-accessories", "jackets-hoodies", "Excellent", 1),
    ("Fastrack Sports Analog Watch", "Black silicone strap watch with neon orange minute markers, found near sports ground bench.", "clothing-accessories", "watches", "Good", 1),
    ("Ray-Ban Wayfarer Polarized Sunglasses", "Tortoise shell frame sunglasses inside a black faux-leather snap case.", "clothing-accessories", "sunglasses", "Excellent", 1),
    ("Large Automatic Black Golf Umbrella", "Sturdy umbrella with wooden curved handle and press-button open mechanism.", "clothing-accessories", "umbrellas", "Good", 1),
    ("Nike Black Aerobill Running Cap", "Breathable black sports cap with reflective swoosh on the front visor.", "clothing-accessories", "caps-hats", "Good", 1),
    ("Grey Fleece Zip-Up Hoodie", "Unbranded heather grey college hoodie with drawstrings, size L.", "clothing-accessories", "jackets-hoodies", "Fair", 1),

    # Bags
    ("Wildcraft 35L Laptop Backpack", "Dark grey and red accents with three zipped compartments and padded back support.", "bags", "backpacks", "Good", 1),
    ("Tommy Hilfiger Brown Leather Bifold Wallet", "Contained some loose change and campus bookstore loyalty card. Left at cashier counter.", "bags", "wallets", "Good", 1),
    ("Lenovo 15.6-inch Neoprene Laptop Sleeve", "Grey padded zippered sleeve for a medium sized laptop, found in seminar room 204.", "bags", "laptop-bags", "Excellent", 1),
    ("Canvas Zippered Pouch with Stationery", "Floral pattern canvas pouch containing colored pens and highlighters.", "bags", "pouches-slings", "Good", 1),
    ("Quechua 10L Compact Daypack", "Blue and yellow mini backpack left near the campus parking lot bicycle rack.", "bags", "backpacks", "Fair", 1),

    # Stationery
    ("Classmate Pulse Spiral Notebook (Unused)", "Hardcover single line spiral notebook with engineering graph paper inserted.", "stationery", "notebooks-registers", "Excellent", 1),
    ("Parker Vector Stainless Steel Fountain Pen", "Silver metallic pen with arrow clip and blue ink cartridge inside.", "stationery", "pens-pencils", "Good", 1),
    ("Camlin Kokuyo Scholar Geometry Box", "Metal tin geometry kit with compass, divider, set squares and 15cm ruler.", "stationery", "geometry-kits", "Good", 1),
    ("Hardbound Project Record File with Transparent Sheets", "Black binder containing mechanical drawing sample sheets.", "stationery", "files-folders", "Fair", 1),
    ("Leatherette Roll-Up Pencil Pouch", "Vintage brown leather pouch holding 12 technical drawing pencils.", "stationery", "pencil-cases", "Good", 1),

    # Books & Documents
    ("Data Structures and Algorithms in C++ Textbook", "Authored by Drozdek, 4th edition, has highlighted sections in chapter 3.", "books-documents", "academic-textbooks", "Good", 1),
    ("University RFID Student Identity Card", "Student ID card found near the auditorium entrance lobby.", "books-documents", "student-id-cards", "Good", 1),
    ("Campus Library Borrower Smart Card", "White magnetic strip card with barcode on the reverse side.", "books-documents", "access-cards", "Excellent", 1),
    ("Linear Algebra & Differential Equations Reference Guide", "Paperback academic book with yellow post-it notes marking formulas.", "books-documents", "academic-textbooks", "Fair", 1),
    ("Blue File Folder with Official University Bonafide Certificate", "Folder with student academic letters and fee receipts.", "books-documents", "certificates-folders", "Good", 1),

    # Keys & Cards
    ("Set of 3 Brass Keys on Marvel Spiderman Keychain", "Includes two Godrej locker keys and one cylinder padlock key.", "keys-cards", "room-keys", "Good", 3),
    ("Honda Activa Scooter Key with Blue Silicone Cover", "Key with magnetic shutter lock tool and small silver bell attached.", "keys-cards", "vehicle-keys", "Good", 1),
    ("Red University Lanyard with Magnetic Access Tag", "Woven fabric lanyard with brass swivel hook holding hostel room tag #312.", "keys-cards", "keychains-lanyards", "Good", 1),
    ("City Metro Smart Transit Card", "Rechargeable transit card with purple and white city metro design.", "keys-cards", "transit-cards", "Excellent", 1),

    # Sports Equipment
    ("Yonex Nanoray 10F Badminton Racket", "Yellow and black graphite badminton racket with neon green Yonex grip.", "sports-equipment", "badminton-rackets", "Good", 1),
    ("Spalding NBA Official Size 7 Basketball", "Classic orange composite leather basketball found courtside.", "sports-equipment", "sports-balls", "Fair", 1),
    ("Decathlon Resistance Bands Set (3 Pack)", "Set of three elastic workout loop bands in light, medium and heavy resistance.", "sports-equipment", "gym-accessories", "Excellent", 3),
    ("Nivia Football Shin Guards", "Pair of black hard-shell protective shin guards with velcro elastic straps.", "sports-equipment", "gym-accessories", "Good", 2),

    # Personal Items
    ("Titan Eyeplus Matte Metal Spectacles Case", "Contains blue anti-glare reading glasses with black acetate frames.", "personal-items", "spectacles-cases", "Excellent", 1),
    ("Borosil Stainless Steel 3-Tier Insulated Lunch Box", "Thermal carrier bag with three round containers inside, found in cafeteria.", "personal-items", "lunch-boxes", "Good", 1),
    ("Ray-Ban Hard Clamshell Glasses Case", "Black textured leatherette protective case with microfiber cleaning cloth.", "personal-items", "spectacles-cases", "Good", 1),

    # Miscellaneous
    ("White Full-Sleeve Laboratory Coat (Size M)", "Cotton lab apron with two deep front pockets, found in chemistry lab rack.", "miscellaneous", "lab-coats", "Good", 1),
    ("Vernier Digital Caliper 150mm with Case", "Stainless steel precision caliper in black plastic storage box.", "miscellaneous", "scientific-equipment", "Excellent", 1),
    ("Large Multicolored Windproof Umbrella", "Rainbow colored 16-rib umbrella found in the main foyer umbrella stand.", "miscellaneous", "unclassified-objects", "Good", 1),
]


def seed_database(reset: bool = False):
    db = SessionLocal()
    rng = random.Random(42)

    try:
        if reset:
            print("Resetting existing database records...")
            db.query(AdminAuditLog).delete()
            db.query(Notification).delete()
            db.query(ContactRequest).delete()
            db.query(ItemStatusHistory).delete()
            db.query(ItemImage).delete()
            db.query(FoundItem).delete()
            db.query(Subcategory).delete()
            db.query(Category).delete()
            db.query(CampusLocation).delete()
            db.query(User).delete()
            db.commit()
            print("Reset completed.")

        # 1. Seed or Verify Admin User
        admin_email = settings.ADMIN_EMAIL.lower()
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                full_name="Found It Administrator",
                email=admin_email,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                role="admin",
                phone="+91 9876543210",
                department="Campus Security & Admin Operations",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Created Admin account: {admin_email}")
        else:
            print(f"Admin account already exists: {admin_email}")

        # 2. Seed Categories & Subcategories
        category_map = {}
        subcategory_map = {}
        for cat_info in CATEGORIES_DATA:
            cat = db.query(Category).filter(Category.slug == cat_info["slug"]).first()
            if not cat:
                cat = Category(
                    name=cat_info["name"],
                    slug=cat_info["slug"],
                    description=cat_info["description"],
                    icon=cat_info["icon"],
                    is_active=True,
                )
                db.add(cat)
                db.commit()
                db.refresh(cat)
            category_map[cat.slug] = cat

            for sub_name, sub_slug in cat_info["subcategories"]:
                sub = (
                    db.query(Subcategory)
                    .filter(Subcategory.category_id == cat.id, Subcategory.name == sub_name)
                    .first()
                )
                if not sub:
                    sub = Subcategory(
                        category_id=cat.id,
                        name=sub_name,
                        slug=sub_slug,
                        is_active=True,
                    )
                    db.add(sub)
                    db.commit()
                    db.refresh(sub)
                subcategory_map[(cat.slug, sub_slug)] = sub

        print(f"Seeded {len(category_map)} Categories and {len(subcategory_map)} Subcategories.")

        # 3. Seed Campus Locations
        location_objs = []
        for name, building, desc in CAMPUS_LOCATIONS_DATA:
            loc = db.query(CampusLocation).filter(CampusLocation.name == name).first()
            if not loc:
                loc = CampusLocation(
                    name=name,
                    building_or_area=building,
                    description=desc,
                    is_active=True,
                )
                db.add(loc)
                db.commit()
                db.refresh(loc)
            location_objs.append(loc)
        print(f"Seeded {len(location_objs)} Campus Locations.")

        # 4. Seed Synthetic Users (120 users)
        existing_user_count = db.query(User).filter(User.role == "user").count()
        target_synthetic_users = 120
        created_users = []

        if existing_user_count < target_synthetic_users:
            default_pwd_hash = get_password_hash("CampusUser2026!")
            user_count = existing_user_count

            for i in range(1, target_synthetic_users + 1):
                if user_count >= target_synthetic_users:
                    break

                user_email = f"demo.user.{i:03d}@campus.university.edu"
                if db.query(User).filter(User.email == user_email).first():
                    continue

                fn = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
                ln = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
                user = User(
                    full_name=f"{fn} {ln}",
                    email=user_email,
                    password_hash=default_pwd_hash,
                    role="user",
                    phone=f"+91 {7000000000 + i}",
                    department=DEPARTMENTS[(i - 1) % len(DEPARTMENTS)],
                    is_active=True,
                )
                db.add(user)
                created_users.append(user)
                user_count += 1
            db.commit()
            print(f"Added {len(created_users)} synthetic users. Total users now: {db.query(User).count()}")

        all_users = db.query(User).filter(User.role == "user").all()

        # 5. Seed Found Items (target 210 listings)
        existing_items_count = db.query(FoundItem).count()
        target_items = 210

        if existing_items_count < target_items:
            needed_items = target_items - existing_items_count
            now = datetime.utcnow()
            ref_counter = existing_items_count + 1

            for i in range(needed_items):
                # Pick a template item
                tmpl = SAMPLE_ITEMS[i % len(SAMPLE_ITEMS)]
                title, desc, cat_slug, sub_slug, cond, qty = tmpl
                
                # Vary title slightly for duplicates
                variant_num = (i // len(SAMPLE_ITEMS)) + 1
                if variant_num > 1:
                    item_title = f"{title} (Found #{variant_num})"
                else:
                    item_title = title

                cat_obj = category_map[cat_slug]
                sub_obj = subcategory_map.get((cat_slug, sub_slug))
                loc_obj = rng.choice(location_objs)
                reporter = rng.choice(all_users)

                # Realistic timestamp within last 60 days
                days_ago = rng.randint(1, 60)
                hours_ago = rng.randint(1, 23)
                found_time = now - timedelta(days=days_ago, hours=hours_ago)

                # Status distribution: ~70% available, ~20% returned, ~10% removed
                status_roll = rng.random()
                if status_roll < 0.70:
                    status = "available"
                    resolved_time = None
                elif status_roll < 0.90:
                    status = "returned"
                    resolved_time = found_time + timedelta(days=rng.randint(1, 5))
                else:
                    status = "removed"
                    resolved_time = found_time + timedelta(days=rng.randint(1, 7))

                ref_code = f"FI-2026-{ref_counter:06d}"
                ref_counter += 1

                item = FoundItem(
                    reference_code=ref_code,
                    title=item_title,
                    description=desc,
                    category_id=cat_obj.id,
                    subcategory_id=sub_obj.id if sub_obj else None,
                    location_id=loc_obj.id,
                    reporter_id=reporter.id,
                    found_at=found_time,
                    quantity=qty,
                    condition=cond,
                    status=status,
                    created_at=found_time,
                    updated_at=resolved_time if resolved_time else found_time,
                    resolved_at=resolved_time,
                )
                db.add(item)
                db.flush()

                # Add Primary Image from demo assets
                demo_pool = DEMO_IMAGE_MAP.get(cat_slug, ["misc_item.png"])
                primary_img_file = demo_pool[0]
                img1 = ItemImage(
                    item_id=item.id,
                    image_path=f"demo/{primary_img_file}",
                    original_filename=primary_img_file,
                    is_primary=True,
                    uploaded_at=found_time,
                )
                db.add(img1)

                # If item has multiple images (for ~25% of items)
                if len(demo_pool) > 1 and rng.random() < 0.25:
                    second_img_file = demo_pool[1]
                    img2 = ItemImage(
                        item_id=item.id,
                        image_path=f"demo/{second_img_file}",
                        original_filename=second_img_file,
                        is_primary=False,
                        uploaded_at=found_time,
                    )
                    db.add(img2)

                # If resolved/removed, add status history entry
                if status != "available":
                    history = ItemStatusHistory(
                        item_id=item.id,
                        changed_by_user_id=reporter.id,
                        old_status="available",
                        new_status=status,
                        note="Item claim resolved with owner after in-person verification on campus."
                        if status == "returned"
                        else "Listing archived by reporter.",
                        created_at=resolved_time or now,
                    )
                    db.add(history)

            db.commit()
            print(f"Added {needed_items} found items. Total items: {db.query(FoundItem).count()}")

        # 6. Seed Contact Requests (target 75 requests)
        target_contact_requests = 75
        existing_contact_count = db.query(ContactRequest).count()
        sample_messages = [
            "Hello, I believe this belongs to me! I lost it during my morning lecture in that block. Could we meet to verify?",
            "Hi there, this matches the exact description of the item I misplaced yesterday. How can I collect it from you?",
            "Hey! Thank you so much for reporting this. I can provide the serial number / distinguishing mark to verify ownership.",
            "Greetings! I noticed your post. Could you let me know when you are available near the library to coordinate handover?",
            "Hi, I lost this on Tuesday afternoon. I have the purchase bill and receipt to confirm it is mine.",
        ]
        seeded_contact_count = 0
        needed_contacts = max(0, target_contact_requests - existing_contact_count)
        all_items = db.query(FoundItem).order_by(FoundItem.id).all()
        for index, item in enumerate(all_items):
            if seeded_contact_count >= needed_contacts:
                break
            if db.query(ContactRequest).filter(ContactRequest.item_id == item.id).first():
                continue

            reporter = db.query(User).filter(User.id == item.reporter_id).first()
            if not reporter:
                continue
            potential_senders = [user for user in all_users if user.id != reporter.id]
            if not potential_senders:
                continue

            sender = potential_senders[index % len(potential_senders)]
            c_status = ("new", "read", "closed")[index % 3]
            c_time = item.created_at + timedelta(hours=2 + (index % 24))
            req = ContactRequest(
                item_id=item.id,
                sender_id=sender.id,
                recipient_id=reporter.id,
                message=sample_messages[index % len(sample_messages)],
                status=c_status,
                created_at=c_time,
                updated_at=c_time,
            )
            db.add(req)
            db.flush()

            db.add(Notification(
                user_id=reporter.id,
                type="new_contact_request",
                title=f"New enquiry on '{item.title[:40]}...'",
                message=f"{sender.full_name} sent a contact request regarding your found item report ({item.reference_code}).",
                related_item_id=item.id,
                related_contact_request_id=req.id,
                is_read=(c_status != "new"),
                created_at=c_time,
            ))
            seeded_contact_count += 1

        db.commit()
        print(f"Seeded {seeded_contact_count} contact requests. Total now: {db.query(ContactRequest).count()}")

        # 7. Seed Admin Audit Logs
        sample_logs = [
            ("VIEW_DASHBOARD", "system_overview", "Global Statistics Check"),
            ("EXPLORE_TABLE", "table", "users"),
            ("EXPLORE_TABLE", "table", "found_items"),
            ("RUN_SQL_QUERY", "sql_explorer", "query_03_category_distribution"),
            ("RUN_SQL_QUERY", "sql_explorer", "query_04_location_distribution"),
            ("VIEW_SCHEMA", "database_schema", "information_schema"),
        ]
        for act, t_type, t_ref in sample_logs:
            exists = db.query(AdminAuditLog).filter_by(
                admin_user_id=admin_user.id,
                action=act,
                target_type=t_type,
                target_reference=t_ref,
            ).first()
            if not exists:
                audit = AdminAuditLog(
                    admin_user_id=admin_user.id,
                    action=act,
                    target_type=t_type,
                    target_reference=t_ref,
                    created_at=datetime.utcnow(),
                )
                db.add(audit)
        db.commit()

        print("=== Database Seeding Completed Successfully ===")
        print(f"Users: {db.query(User).count()} (Admin: {admin_email})")
        print(f"Categories: {db.query(Category).count()}")
        print(f"Subcategories: {db.query(Subcategory).count()}")
        print(f"Campus Locations: {db.query(CampusLocation).count()}")
        print(f"Found Items: {db.query(FoundItem).count()} (Available: {db.query(FoundItem).filter(FoundItem.status == 'available').count()})")
        print(f"Item Images: {db.query(ItemImage).count()}")
        print(f"Contact Requests: {db.query(ContactRequest).count()}")
        print(f"Notifications: {db.query(Notification).count()}")
        print(f"Item Status History: {db.query(ItemStatusHistory).count()}")
        print(f"Admin Audit Logs: {db.query(AdminAuditLog).count()}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Found It MySQL Database")
    parser.add_argument("--reset", action="store_true", help="Reset all tables before seeding")
    args = parser.parse_args()
    seed_database(reset=args.reset)
