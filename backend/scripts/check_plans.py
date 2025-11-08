#!/usr/bin/env python3
"""
Check plans in database and compare with Stripe
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.plan import Plan
from app.models.subscription import StripeSubscription
from app.models.user import User
import stripe
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def check_plans():
    """Check all plans and their Stripe price IDs"""
    db = SessionLocal()

    try:
        print("=" * 70)
        print("DATABASE PLANS")
        print("=" * 70)

        plans = db.query(Plan).all()
        for plan in plans:
            print(f"\n{plan.name} Plan:")
            print(f"  ID: {plan.id}")
            print(f"  stripe_price_id: {plan.stripe_price_id}")
            print(f"  Price: ${plan.price_cents / 100}")
            print(f"  Requests: {plan.monthly_requests}")

            # Check if this price exists in Stripe
            if plan.stripe_price_id:
                try:
                    stripe_price = stripe.Price.retrieve(plan.stripe_price_id)
                    print(f"  ✓ Stripe price exists: {stripe_price.id}")
                    print(f"    Product: {stripe_price.product}")
                    print(f"    Amount: ${stripe_price.unit_amount / 100}")
                except Exception as e:
                    print(f"  ✗ ERROR fetching from Stripe: {e}")
            else:
                print(f"  (No Stripe price - Free plan)")

        print("\n" + "=" * 70)
        print("SUBSCRIPTIONS")
        print("=" * 70)

        subs = db.query(StripeSubscription).all()
        for sub in subs:
            user = db.query(User).filter(User.id == sub.user_id).first()
            plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()

            print(f"\nUser: {user.email if user else 'Unknown'}")
            print(f"  DB Plan: {plan.name if plan else 'Unknown'}")
            print(f"  DB plan_id: {sub.plan_id}")
            print(f"  Stripe Subscription ID: {sub.stripe_subscription_id}")
            print(f"  Status: {sub.status}")

            # Fetch from Stripe
            try:
                stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
                items = list(stripe_sub.get("items", {}).get("data", []))
                if items:
                    stripe_price_id = items[0]["price"]["id"]
                    print(f"  Stripe price_id: {stripe_price_id}")

                    # Find matching plan
                    correct_plan = db.query(Plan).filter(Plan.stripe_price_id == stripe_price_id).first()
                    if correct_plan:
                        if correct_plan.id == sub.plan_id:
                            print(f"  ✓ MATCH: DB and Stripe agree on '{correct_plan.name}'")
                        else:
                            print(f"  ✗ MISMATCH!")
                            print(f"    DB says: {plan.name if plan else 'Unknown'}")
                            print(f"    Stripe says: {correct_plan.name}")
                    else:
                        print(f"  ✗ ERROR: No plan found in DB for Stripe price_id: {stripe_price_id}")
            except Exception as e:
                print(f"  ✗ ERROR fetching from Stripe: {e}")

        print("\n" + "=" * 70)
        print("ALL STRIPE PRODUCTS & PRICES")
        print("=" * 70)

        products = stripe.Product.list(limit=10)
        for product in products.data:
            print(f"\nProduct: {product.name}")
            print(f"  ID: {product.id}")

            prices = stripe.Price.list(product=product.id)
            for price in prices.data:
                print(f"  Price ID: {price.id}")
                print(f"    Amount: ${price.unit_amount / 100}/month" if price.unit_amount else "    Free")

                # Check if this price is in our database
                db_plan = db.query(Plan).filter(Plan.stripe_price_id == price.id).first()
                if db_plan:
                    print(f"    ✓ Linked to DB plan: {db_plan.name}")
                else:
                    print(f"    ✗ NOT in database!")

    finally:
        db.close()

if __name__ == "__main__":
    check_plans()
