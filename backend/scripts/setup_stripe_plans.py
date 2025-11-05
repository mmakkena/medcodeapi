"""
Script to automatically create Stripe products/prices and seed database plans.
Run this once to set up your billing structure.

Usage:
    python scripts/setup_stripe_plans.py
    python scripts/setup_stripe_plans.py --yes  # Skip confirmation
"""

import stripe
import sys
import os
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import SessionLocal
from app.models.plan import Plan
import uuid

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_product_and_price(name: str, description: str, price_cents: int):
    """Create a Stripe product and recurring price"""
    print(f"\nCreating Stripe product: {name}...")

    # Create product
    product = stripe.Product.create(
        name=name,
        description=description,
    )
    print(f"  ✓ Product created: {product.id}")

    # Create recurring price
    if price_cents > 0:
        price = stripe.Price.create(
            product=product.id,
            unit_amount=price_cents,
            currency="usd",
            recurring={"interval": "month"},
        )
        print(f"  ✓ Price created: {price.id} (${price_cents/100}/month)")
        return price.id
    else:
        print(f"  ✓ Free plan - no price created")
        return None


def seed_database_plans(plans_data):
    """Seed plans into database"""
    print("\n" + "="*60)
    print("Seeding database with plans...")
    print("="*60)

    db = SessionLocal()

    try:
        for plan_data in plans_data:
            existing = db.query(Plan).filter(Plan.name == plan_data["name"]).first()

            if existing:
                print(f"\n  Updating existing plan: {plan_data['name']}")
                for key, value in plan_data.items():
                    if key != "id":
                        setattr(existing, key, value)
            else:
                print(f"\n  Creating new plan: {plan_data['name']}")
                plan = Plan(**plan_data)
                db.add(plan)

            db.commit()
            print(f"    ✓ {plan_data['name']} - {plan_data['monthly_requests']} req/mo - ${plan_data['price_cents']/100}/mo")

        print("\n" + "="*60)
        print("✓ All plans seeded successfully!")
        print("="*60)

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding database: {e}")
        raise
    finally:
        db.close()


def main():
    """Main setup function"""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Set up Stripe billing plans')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("="*60)
    print("STRIPE BILLING SETUP")
    print("="*60)
    print(f"\nStripe Mode: {'TEST' if 'test' in settings.STRIPE_SECRET_KEY else 'LIVE'}")
    print(f"API Key: {settings.STRIPE_SECRET_KEY[:12]}...{settings.STRIPE_SECRET_KEY[-4:]}")

    # Confirm before proceeding
    if not args.yes:
        response = input("\nThis will create products in Stripe. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    # Define plans
    plans = [
        {
            "name": "Free",
            "description": "100 requests per month - Perfect for testing",
            "monthly_requests": 100,
            "price_cents": 0,
            "features": {
                "rate_limit": 60,
                "support": "community",
                "requests": 100
            }
        },
        {
            "name": "Developer",
            "description": "10,000 requests per month with email support",
            "monthly_requests": 10000,
            "price_cents": 4900,  # $49.00
            "features": {
                "rate_limit": 300,
                "support": "email",
                "requests": 10000,
                "analytics": True
            }
        },
        {
            "name": "Growth",
            "description": "100,000 requests per month with priority support and 99.9% SLA",
            "monthly_requests": 100000,
            "price_cents": 29900,  # $299.00
            "features": {
                "rate_limit": 1000,
                "support": "priority",
                "requests": 100000,
                "analytics": True,
                "sla": "99.9%"
            }
        },
        {
            "name": "Enterprise",
            "description": "Custom volume with dedicated support and 99.99% SLA",
            "monthly_requests": 1000000,
            "price_cents": 99900,  # $999.00 (placeholder)
            "features": {
                "rate_limit": "custom",
                "support": "dedicated",
                "requests": "custom",
                "analytics": True,
                "sla": "99.99%",
                "custom_contract": True
            }
        },
    ]

    # Create Stripe products and prices, then prepare DB data
    plans_data = []

    for plan in plans:
        # Create Stripe product/price
        stripe_price_id = create_stripe_product_and_price(
            name=plan["name"] + " Plan",
            description=plan["description"],
            price_cents=plan["price_cents"]
        )

        # Prepare database entry
        plans_data.append({
            "id": uuid.uuid4(),
            "name": plan["name"],
            "monthly_requests": plan["monthly_requests"],
            "price_cents": plan["price_cents"],
            "stripe_price_id": stripe_price_id,
            "features": plan["features"]
        })

    # Seed database
    seed_database_plans(plans_data)

    # Print summary
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("\nStripe Products Created:")
    for plan_data in plans_data:
        if plan_data["stripe_price_id"]:
            print(f"  • {plan_data['name']}: {plan_data['stripe_price_id']}")
        else:
            print(f"  • {plan_data['name']}: Free (no Stripe price)")

    print("\nNext Steps:")
    print("1. Verify products in Stripe Dashboard:")
    print("   https://dashboard.stripe.com/test/products")
    print("\n2. Test the upgrade flow in your application")
    print("   Use test card: 4242 4242 4242 4242")
    print("\n3. When ready for production, run this script with LIVE keys")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        sys.exit(1)
