import os
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "multivendor.settings")
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import VendorProfile
from products.models import Category, Product, Review

User = get_user_model()


def seed_database():
    print("Starting database seeding with 50 general products...")

    Review.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    VendorProfile.objects.all().delete()

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword123",
            first_name="Store",
            last_name="Admin",
        )
        print("Created admin user: admin / adminpassword123")

    customers = []
    for index in range(1, 6):
        username = f"customer{index}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@example.com",
                "first_name": "Customer",
                "last_name": str(index),
                "is_customer": True,
            },
        )
        if created:
            user.set_password("customerpassword123")
            user.save()
        customers.append(user)

    categories_data = [
        {
            "name": "Electronics",
            "description": "Phones, headphones, speakers, chargers, and useful everyday gadgets.",
            "image_url": "https://images.unsplash.com/photo-1550009158-9ebf69173e03?auto=format&fit=crop&w=500&q=80",
        },
        {
            "name": "Groceries",
            "description": "Rice, oil, flour, snacks, tea, coffee, spices, and daily kitchen essentials.",
            "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=500&q=80",
        },
        {
            "name": "Toys",
            "description": "Board games, building blocks, dolls, puzzles, cars, and safe toys for kids.",
            "image_url": "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?auto=format&fit=crop&w=500&q=80",
        },
        {
            "name": "Men's Clothing",
            "description": "Shirts, jeans, t-shirts, jackets, trousers, and everyday menswear.",
            "image_url": "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=500&q=80",
        },
        {
            "name": "Women's Clothing",
            "description": "Kurtis, dresses, sarees, tops, jeans, leggings, and daily women's wear.",
            "image_url": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=500&q=80",
        },
    ]

    categories = {}
    for item in categories_data:
        category = Category.objects.create(**item)
        categories[item["name"]] = category
        print(f"Created category: {category.name}")

    vendors_data = [
        {
            "username": "electronics_hub",
            "email": "sales@electronicshub.example.com",
            "store_name": "Electronics Hub",
            "description": "Trusted seller for phones, accessories, audio products, and home electronics.",
            "logo_url": "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?auto=format&fit=crop&w=150&h=150&q=80",
        },
        {
            "username": "fresh_grocery_mart",
            "email": "orders@freshgrocerymart.example.com",
            "store_name": "Fresh Grocery Mart",
            "description": "Daily grocery essentials, pantry staples, snacks, and household food items.",
            "logo_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=150&h=150&q=80",
        },
        {
            "username": "toy_world",
            "email": "hello@toyworld.example.com",
            "store_name": "Toy World",
            "description": "Fun and safe toys, puzzles, games, and activity kits for children.",
            "logo_url": "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?auto=format&fit=crop&w=150&h=150&q=80",
        },
        {
            "username": "mens_fashion_store",
            "email": "support@mensfashionstore.example.com",
            "store_name": "Men's Fashion Store",
            "description": "Simple and comfortable clothing for men, from casual wear to office basics.",
            "logo_url": "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=150&h=150&q=80",
        },
        {
            "username": "womens_fashion_boutique",
            "email": "care@womensfashionboutique.example.com",
            "store_name": "Women's Fashion Boutique",
            "description": "Everyday women's clothing, ethnic wear, western wear, and comfortable basics.",
            "logo_url": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=150&h=150&q=80",
        },
    ]

    vendors = {}
    for item in vendors_data:
        User.objects.filter(username=item["username"]).delete()
        user = User.objects.create(
            username=item["username"],
            email=item["email"],
            is_vendor=True,
            is_customer=False,
        )
        user.set_password("vendorpassword123")
        user.save()
        profile = VendorProfile.objects.create(
            user=user,
            store_name=item["store_name"],
            description=item["description"],
            logo_url=item["logo_url"],
            status="APPROVED",
            balance=Decimal("25000.00"),
        )
        vendors[item["store_name"]] = profile
        print(f"Created vendor: {profile.store_name}")

    products_data = [
        # Electronics
        ("Electronics Hub", "Electronics", "Wireless Bluetooth Headphones", "Comfortable wireless headphones with clear sound, soft ear cushions, and long battery life for music, calls, and travel.", "1499.00", 35, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "Smartphone 128GB", "A reliable 128GB smartphone with a bright display, good camera, fast charging, and enough storage for everyday apps and photos.", "15999.00", 22, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "Portable Bluetooth Speaker", "Compact speaker with loud sound, deep bass, water-resistant body, and easy Bluetooth pairing for home or outdoor use.", "1999.00", 40, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "USB-C Fast Charger", "Fast wall charger with USB-C output, safety protection, and compact size for phones, tablets, and compatible accessories.", "699.00", 75, "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "Power Bank 10000mAh", "Slim 10000mAh power bank with dual output ports, LED battery indicator, and dependable backup charging for daily use.", "1299.00", 55, "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "Laptop Backpack", "Padded laptop backpack with separate compartments, bottle holder, strong zippers, and comfortable shoulder straps.", "999.00", 60, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "LED Desk Lamp", "Adjustable LED desk lamp with three brightness levels, touch controls, and soft light for reading, studying, or work.", "849.00", 38, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "Wireless Mouse", "Lightweight wireless mouse with smooth tracking, quiet clicks, and a comfortable shape for office and home computers.", "499.00", 90, "https://images.unsplash.com/photo-1527814050087-3793815479db?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "Fitness Smart Watch", "Easy-to-use smart watch with step tracking, heart rate monitor, notifications, sleep tracking, and a clear color display.", "2499.00", 28, "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?auto=format&fit=crop&w=500&q=80"),
        ("Electronics Hub", "Electronics", "HD Webcam", "HD webcam with built-in microphone, clear video quality, and simple plug-and-play setup for calls and online classes.", "1199.00", 32, "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&w=500&q=80"),
        # Groceries
        ("Fresh Grocery Mart", "Groceries", "Basmati Rice 5kg", "Long-grain basmati rice with a pleasant aroma, ideal for biryani, pulao, fried rice, and daily family meals.", "799.00", 85, "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Whole Wheat Flour 5kg", "Fresh whole wheat flour suitable for soft chapatis, parathas, puris, and regular home cooking.", "299.00", 110, "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Sunflower Cooking Oil 1L", "Light sunflower cooking oil for frying, sauteing, and everyday cooking with a neutral taste.", "165.00", 140, "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Toor Dal 1kg", "Good quality toor dal for making dal fry, sambar, rasam, and other traditional meals.", "189.00", 95, "https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Mixed Masala Pack", "A useful spice pack with common kitchen masalas for curries, vegetables, rice dishes, and snacks.", "249.00", 70, "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Tea Powder 500g", "Strong and refreshing tea powder for making regular milk tea with rich color and good flavor.", "235.00", 80, "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Instant Coffee 200g", "Smooth instant coffee that dissolves quickly and works well for hot coffee, cold coffee, and office breaks.", "399.00", 64, "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Sugar 2kg", "Clean white sugar for tea, coffee, desserts, baking, and daily kitchen use.", "115.00", 130, "https://images.unsplash.com/photo-1581441363689-1f3c3c414635?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Salt 1kg", "Iodized table salt for regular cooking, seasoning, and food preparation.", "28.00", 200, "https://images.unsplash.com/photo-1518110925495-5fe2fda0442c?auto=format&fit=crop&w=500&q=80"),
        ("Fresh Grocery Mart", "Groceries", "Assorted Biscuits Pack", "Family pack of assorted biscuits with sweet and savory options for tea time and quick snacks.", "149.00", 100, "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=500&q=80"),
        # Toys
        ("Toy World", "Toys", "Building Blocks Set", "Colorful building blocks that help children create houses, vehicles, towers, and simple models while improving creativity.", "899.00", 42, "https://images.unsplash.com/photo-1587654780291-39c9404d746b?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Remote Control Car", "Rechargeable remote control car with easy controls, durable body, and smooth movement for indoor and outdoor play.", "1299.00", 30, "https://images.unsplash.com/photo-1594787318286-3d835c1d207f?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Soft Teddy Bear", "Soft teddy bear made with plush fabric, safe stitching, and a cuddly design for kids and gifting.", "499.00", 65, "https://images.unsplash.com/photo-1559454403-b8fb88521f11?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Wooden Puzzle Board", "Simple wooden puzzle board with bright pieces that helps children learn shapes, colors, and hand-eye coordination.", "349.00", 48, "https://images.unsplash.com/photo-1618842676088-c4d48a6a7c9d?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Kids Cricket Bat Set", "Lightweight cricket bat and ball set for children to enjoy casual play in the park, street, or backyard.", "599.00", 36, "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Doll House Set", "Doll house play set with rooms, small furniture pieces, and accessories for pretend play.", "1499.00", 18, "https://images.unsplash.com/photo-1602734846297-9299fc2d4703?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Board Game Set", "Family board game set with simple rules, dice, tokens, and a foldable board for group play.", "699.00", 44, "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Toy Train Set", "Battery-operated toy train set with tracks, engine, and coaches for enjoyable play at home.", "999.00", 25, "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Art and Craft Kit", "Craft kit with colored paper, glue, crayons, stickers, and basic supplies for creative activities.", "399.00", 58, "https://images.unsplash.com/photo-1513364776144-60967b0f800f?auto=format&fit=crop&w=500&q=80"),
        ("Toy World", "Toys", "Baby Rattle Set", "Lightweight rattle set with safe rounded edges, soft colors, and easy grip for babies.", "299.00", 72, "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?auto=format&fit=crop&w=500&q=80"),
        # Men's Clothing
        ("Men's Fashion Store", "Men's Clothing", "Men's Cotton T-Shirt", "Soft cotton t-shirt with a regular fit, round neck, and comfortable fabric for daily casual wear.", "399.00", 100, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Casual Shirt", "Regular-fit casual shirt with button closure, breathable fabric, and a neat look for office or outings.", "899.00", 55, "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Slim Fit Jeans", "Comfortable slim fit jeans with stretch fabric, five pockets, and a clean everyday style.", "1299.00", 46, "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Formal Trousers", "Plain formal trousers with a smart fit, belt loops, and smooth fabric for office and formal occasions.", "1199.00", 40, "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Denim Jacket", "Classic denim jacket with front buttons, side pockets, and a sturdy casual look.", "1999.00", 20, "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Hoodie", "Warm pullover hoodie with kangaroo pocket, drawstring hood, and soft fleece lining.", "999.00", 34, "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Track Pants", "Comfortable track pants with elastic waistband, side pockets, and flexible fabric for workouts or lounging.", "699.00", 62, "https://images.unsplash.com/photo-1562157873-818bc0726f68?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Polo Shirt", "Polo shirt with collar, short sleeves, and soft fabric for casual and semi-formal wear.", "599.00", 74, "https://images.unsplash.com/photo-1586363104862-3a5e2ab60d99?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Cotton Shorts", "Casual cotton shorts with pockets, elastic waist, and breathable fabric for summer comfort.", "499.00", 68, "https://images.unsplash.com/photo-1565084888279-aca607ecce0c?auto=format&fit=crop&w=500&q=80"),
        ("Men's Fashion Store", "Men's Clothing", "Men's Winter Sweater", "Warm knitted sweater with ribbed cuffs and a comfortable regular fit for cool weather.", "1099.00", 26, "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=500&q=80"),
        # Women's Clothing
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Cotton Kurti", "Comfortable cotton kurti with a simple printed design, straight fit, and soft fabric for daily wear.", "699.00", 70, "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Casual Top", "Regular-fit casual top with soft fabric, easy styling, and a comfortable feel for everyday outfits.", "499.00", 82, "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Blue Jeans", "Comfortable blue jeans with stretch fabric, five pockets, and a clean fit for daily wear.", "1199.00", 45, "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Summer Dress", "Light summer dress with soft fabric, easy fit, and a simple design for casual outings.", "999.00", 32, "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Saree", "Elegant saree with a simple border, smooth drape, and matching blouse piece for family events and festivals.", "1499.00", 24, "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Leggings Pack", "Pack of two stretchable leggings with a comfortable waistband for daily ethnic and casual wear.", "599.00", 90, "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Cardigan", "Soft cardigan with front buttons, ribbed edges, and a relaxed fit for light winter layering.", "1099.00", 28, "https://images.unsplash.com/photo-1543076447-215ad9ba6923?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Palazzo Pants", "Comfortable palazzo pants with wide legs, elastic waistband, and breathable fabric for daily wear.", "799.00", 52, "https://images.unsplash.com/photo-1551803091-e20673f15770?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Office Shirt", "Simple office shirt with button closure, neat collar, and smooth fabric for workwear.", "899.00", 38, "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=500&q=80"),
        ("Women's Fashion Boutique", "Women's Clothing", "Women's Night Suit", "Soft cotton night suit with a relaxed fit, comfortable waistband, and breathable fabric for sleepwear.", "899.00", 44, "https://images.unsplash.com/photo-1568252542512-9fe8fe9c87bb?auto=format&fit=crop&w=500&q=80"),
    ]

    ratings = [5, 4, 4, 5, 3]
    for index, item in enumerate(products_data):
        vendor_name, category_name, name, description, price, stock, image_url = item
        product = Product.objects.create(
            vendor=vendors[vendor_name],
            category=categories[category_name],
            name=name,
            description=description,
            price=Decimal(price),
            stock=stock,
            image_url=image_url,
            is_active=True,
        )
        reviewer = customers[index % len(customers)]
        Review.objects.create(
            product=product,
            user=reviewer,
            rating=ratings[index % len(ratings)],
            comment=f"Good quality {category_name.lower()} product for daily use.",
        )
        print(f"Created product: {product.name}")

    print("\nDatabase seeding completed successfully.")
    print("Created 5 categories, 5 approved vendors, and 50 products.")
    print("Admin: admin / adminpassword123")
    print("Vendor password for all vendors: vendorpassword123")


if __name__ == "__main__":
    seed_database()
