#!/usr/bin/env python3
"""
Fix subscription plan_id by fetching current data from Stripe
This script syncs the database with the actual Stripe subscription data
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.subscription import StripeSubscription
from app.models.plan import Plan
import stripe
from app.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def fix_subscriptions():
    """Fix all subscriptions by syncing with Stripe data"""
    db = SessionLocal()

    try:
        # Get all subscriptions from database
        subscriptions = db.query(StripeSubscription).all()

        print(f"Found {len(subscriptions)} subscriptions in database\n")

        for sub in subscriptions:
            print(f"Checking subscription: {sub.stripe_subscription_id}")
            print(f"  Current plan_id in DB: {sub.plan_id}")

            # Fetch subscription from Stripe
            try:
                stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)

                # Get the price ID from Stripe
                items = list(stripe_sub.get("items", {}).get("data", []))
                if not items:
                    print(f"  ⚠️  No items found in Stripe subscription")
                    continue

                stripe_price_id = items[0]["price"]["id"]
                print(f"  Stripe price_id: {stripe_price_id}")

                # Find the matching plan in our database
                correct_plan = db.query(Plan).filter(Plan.stripe_price_id == stripe_price_id).first()

                if not correct_plan:
                    print(f"  ❌ No plan found for price_id: {stripe_price_id}")
                    continue

                print(f"  Correct plan: {correct_plan.name} (id: {correct_plan.id})")

                # Check if we need to update
                if sub.plan_id != correct_plan.id:
                    old_plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
                    old_plan_name = old_plan.name if old_plan else "Unknown"

                    print(f"  ✅ Updating plan: {old_plan_name} → {correct_plan.name}")
                    sub.plan_id = correct_plan.id
                    db.commit()
                else:
                    print(f"  ✓ Plan is already correct")

            except stripe.error.StripeError as e:
                print(f"  ❌ Stripe error: {e}")
                continue

            print()

        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_subscriptions()
