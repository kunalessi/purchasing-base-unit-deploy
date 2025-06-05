import sqlite3

conn = sqlite3.connect("Server/database.sqlite")
c = conn.cursor()

# Count total products
c.execute("SELECT COUNT(*) FROM products")
total_products = c.fetchone()[0]
print(f"Total products in database: {total_products}")

# Fetch a few products to inspect
c.execute("SELECT company, name, product_type, specs FROM products LIMIT 5")
products = c.fetchall()
for i, product in enumerate(products, 1):
    print(f"\nProduct {i}:")
    print(f"Company: {product[0]}")
    print(f"Name: {product[1]}")
    print(f"Product Type: {product[2]}")
    print(f"Specs: {product[3][:200]}...")  # First 200 chars of specs

conn.close()