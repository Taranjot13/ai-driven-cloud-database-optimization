import random
from datetime import datetime, timedelta

from faker import Faker
import psycopg2


# -----------------------------
# Configuration
# -----------------------------
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "cloud_optimizer",
    "user": "postgres",
    "password": "123456t", 
    # YOUR_POSTGRES_PASSWORD ^^
}

CUSTOMERS = 10_000
PRODUCTS = 5_000
ORDERS = 50_000
ORDER_ITEMS = 150_000
PAYMENTS = 50_000

fake = Faker()


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def generate_customers(cursor):
    print("Generating customers...")

    for _ in range(CUSTOMERS):
        cursor.execute(
            """
            INSERT INTO customers
            (first_name, last_name, email, city, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                fake.first_name(),
                fake.last_name(),
                fake.unique.email(),
                fake.city(),
                fake.date_time_between(
                    start_date="-2y",
                    end_date="now"
                ),
            ),
        )


def generate_products(cursor):
    print("Generating products...")

    categories = [
        "Electronics",
        "Computers",
        "Mobiles",
        "Accessories",
        "Home",
        "Gaming",
        "Office",
    ]

    for _ in range(PRODUCTS):
        cursor.execute(
            """
            INSERT INTO products
            (product_name, category, price, stock_quantity, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                fake.catch_phrase(),
                random.choice(categories),
                round(random.uniform(10, 5000), 2),
                random.randint(0, 1000),
                fake.date_time_between(
                    start_date="-2y",
                    end_date="now"
                ),
            ),
        )


def generate_orders(cursor):
    print("Generating orders...")

    for _ in range(ORDERS):
        cursor.execute(
            """
            INSERT INTO orders
            (customer_id, order_date, status, total_amount)
            VALUES (%s, %s, %s, %s)
            """,
            (
                random.randint(1, CUSTOMERS),
                fake.date_time_between(
                    start_date="-1y",
                    end_date="now"
                ),
                random.choice(
                    ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
                ),
                round(random.uniform(20, 10000), 2),
            ),
        )


def generate_order_items(cursor):
    print("Generating order items...")

    for _ in range(ORDER_ITEMS):
        cursor.execute(
            """
            INSERT INTO order_items
            (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
            """,
            (
                random.randint(1, ORDERS),
                random.randint(1, PRODUCTS),
                random.randint(1, 5),
                round(random.uniform(10, 5000), 2),
            ),
        )


def generate_payments(cursor):
    print("Generating payments...")

    for order_id in range(1, PAYMENTS + 1):
        cursor.execute(
            """
            INSERT INTO payments
            (order_id, payment_date, payment_method, amount, payment_status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                order_id,
                fake.date_time_between(
                    start_date="-1y",
                    end_date="now"
                ),
                random.choice(
                    ["Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet"]
                ),
                round(random.uniform(20, 10000), 2),
                random.choice(["Success", "Failed", "Pending"]),
            ),
        )


def main():
    print("Connecting to PostgreSQL...")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        generate_customers(cursor)
        generate_products(cursor)
        generate_orders(cursor)
        generate_order_items(cursor)
        generate_payments(cursor)

        connection.commit()

        print("\nData generation completed successfully.")

    except Exception as error:
        connection.rollback()
        print(f"\nError: {error}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()