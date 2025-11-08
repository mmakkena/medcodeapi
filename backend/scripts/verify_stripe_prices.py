#!/usr/bin/env python3
"""
Verify Stripe price IDs from database against actual Stripe prices
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stripe
from app.config import settings

# Stripe key from settings
stripe.api_key = settings.STRIPE_SECRET_KEY

# Price IDs from database
db_plans = {
    "Free": None,
    "Developer": "price_1SQDreLoE1yvarSwfhdcYpOd",
    "Growth": "price_1SQDrfLoE1yvarSw1sWkBwZC",
    "Enterprise": "price_1SQDrfLoE1yvarSwaVXoZMol"
}

print("=" * 70)
print("VERIFYING STRIPE PRICE IDs FROM DATABASE")
print("=" * 70)

for plan_name, price_id in db_plans.items():
    print(f"\n{plan_name} Plan:")
    print(f"  DB price_id: {price_id}")

    if price_id:
        try:
            price = stripe.Price.retrieve(price_id)
            print(f"  ✓ Stripe price exists!")
            print(f"    Amount: ${price.unit_amount / 100}/month")
            print(f"    Product: {price.product}")
            print(f"    Active: {price.active}")
        except stripe.error.InvalidRequestError as e:
            print(f"  ✗ ERROR: {e}")
    else:
        print(f"  (Free plan - no Stripe price)")

print("\n" + "=" * 70)
print("ALL STRIPE PRODUCTS & PRICES")
print("=" * 70)

# List all products
products = stripe.Product.list(limit=10)
for product in products.data:
    print(f"\nProduct: {product.name}")
    print(f"  ID: {product.id}")

    # List prices for this product
    prices = stripe.Price.list(product=product.id)
    for price in prices.data:
        print(f"  Price ID: {price.id}")
        print(f"    Amount: ${price.unit_amount / 100 if price.unit_amount else 0}")
        print(f"    Active: {price.active}")

        # Check if this matches our DB
        matches = [name for name, pid in db_plans.items() if pid == price.id]
        if matches:
            print(f"    ✓ Matches DB plan: {', '.join(matches)}")
        else:
            print(f"    ⚠ NOT in database!")
