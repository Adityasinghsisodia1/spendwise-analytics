"""Populate the database with a few months of realistic sample expenses.

Portfolio/demo helper only — generates synthetic data so the dashboard has
something to show. Not part of the app's runtime behavior.
"""

import random
from datetime import date

import db

random.seed(42)

SAMPLE_EXPENSES = {
    "Food": [("Grocery run", 35, 120), ("Restaurant dinner", 20, 60), ("Coffee shop", 4, 12)],
    "Transport": [("Gas fill-up", 30, 55), ("Rideshare", 10, 25), ("Bus pass", 40, 40)],
    "Utilities": [("Electricity bill", 60, 110), ("Internet bill", 45, 65), ("Water bill", 20, 40)],
    "Rent": [("Monthly rent", 850, 850)],
    "Entertainment": [("Movie tickets", 15, 35), ("Streaming subscription", 10, 18)],
    "Health": [("Pharmacy", 10, 45), ("Gym membership", 30, 30)],
    "Shopping": [("Clothing", 25, 90), ("Electronics accessory", 15, 60)],
    "Other": [("Miscellaneous", 5, 40)],
}


def random_day_in_month(year: int, month: int) -> date:
    day = random.randint(1, 28)
    return date(year, month, day)


def seed(months_back: int = 3) -> int:
    db.init_db()
    today = date.today()
    count = 0

    for offset in range(months_back, -1, -1):
        month_index = today.month - offset
        year = today.year
        while month_index <= 0:
            month_index += 12
            year -= 1

        for category, options in SAMPLE_EXPENSES.items():
            for description, low, high in options:
                if random.random() < 0.8:  # not every category has every item every month
                    amount = round(random.uniform(low, high), 2)
                    db.add_expense(random_day_in_month(year, month_index), category, description, amount)
                    count += 1

    return count


if __name__ == "__main__":
    inserted = seed()
    print(f"Inserted {inserted} sample expenses across the last few months.")
