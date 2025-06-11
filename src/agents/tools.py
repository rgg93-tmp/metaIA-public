import pandas as pd
from ydata_profiling import ProfileReport
import random
from datetime import datetime, timedelta


def invent_data(filename_data: str) -> str:
    """Generate and save a basic data profile markdown report."""
    # Sample data
    products = [
        {"Product": "Laptop", "Category": "Electronics", "Price": 1000},
        {"Product": "Headphones", "Category": "Electronics", "Price": 200},
        {"Product": "Coffee Maker", "Category": "Home Appliance", "Price": 80},
        {"Product": "Desk Chair", "Category": "Furniture", "Price": 150},
        {"Product": "Notebook", "Category": "Stationery", "Price": 5},
    ]

    # Generate sample sales records
    num_records = 100
    sales_data = []

    for _ in range(num_records):
        product = random.choice(products)
        quantity = random.randint(1, 5)
        price = product["Price"]
        total = quantity * price
        record = {
            "Date": (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d"),
            "CustomerID": random.randint(1000, 1100),
            "Product": product["Product"],
            "Category": product["Category"],
            "Quantity": quantity,
            "Price": price,
            "Total": total,
        }
        sales_data.append(record)

    # Create DataFrame
    df = pd.DataFrame(sales_data)

    # Save to CSV
    df.to_csv(f"./data/{filename_data}", index=False)

    print("Sample sales dataset created as {filename_data}")


def profile_data(filename_data: str) -> str:
    """Generate and save a basic data profile markdown report."""
    # Step 1: Read the dataset
    df = pd.read_csv(f"./data/{filename_data}")

    # Step 2: Generate the profile report
    profile = ProfileReport(df, title="Sales Data Profile", explorative=True)

    # Step 3: Save the profile to an HTML file
    profile.to_file(f"./data/{filename_data}_profile.html")
