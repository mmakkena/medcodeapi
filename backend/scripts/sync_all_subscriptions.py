#!/usr/bin/env python3
"""
Sync all subscriptions with Stripe - fix status and plan mismatches
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.subscription import StripeSubscription
from app.models.plan import Plan
import stripe
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def sync_subscriptions():
    """Sync all subscriptions with Stripe"""
    db = SessionLocal()

    try:
        # Get all subscriptions from database
        subscriptions = db.query(StripeSubscription).all()

        print(f"Found {len(subscriptions)} subscriptions in database\n")
        print("=" * 80)

        for sub in subscriptions:
            print(f"\nChecking: {sub.stripe_subscription_id}")
            print(f"  Current DB status: {sub.status}")

            # Fetch subscription from Stripe
            try:
                stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
                stripe_status = stripe_sub.get("status")

                print(f"  Stripe status: {stripe_status}")

                # Get the price ID from Stripe
                items = list(stripe_sub.get("items", {}).get("data", []))
                if items:
                    stripe_price_id = items[0]["price"]["id"]

                    # Find the matching plan in our database
                    correct_plan = db.query(Plan).filter(Plan.stripe_price_id == stripe_price_id).first()

                    if correct_plan:
                        current_plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()

                        changes = []

                        # Check status
                        if sub.status != stripe_status:
                            changes.append(f"status: {sub.status} → {stripe_status}")
                            sub.status = stripe_status

                        # Check plan
                        if sub.plan_id != correct_plan.id:
                            changes.append(f"plan: {current_plan.name} → {correct_plan.name}")
                            sub.plan_id = correct_plan.id

                        if changes:
                            print(f"  ✅ UPDATING: {', '.join(changes)}")
                            db.commit()
                        else:
                            print(f"  ✓ Already correct")
                    else:
                        print(f"  ❌ No plan found for price_id: {stripe_price_id}")
                else:
                    print(f"  ⚠️  No items in subscription")

            except stripe.error.StripeError as e:
                print(f"  ❌ Stripe error: {e}")
                continue

        print("\n" + "=" * 80)
        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_subscriptions()
