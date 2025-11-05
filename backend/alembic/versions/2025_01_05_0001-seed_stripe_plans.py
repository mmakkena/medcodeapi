"""seed stripe plans

Revision ID: 2025_01_05_0001
Revises: 2025_01_01_0001
Create Date: 2025-01-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
import json


# revision identifiers, used by Alembic.
revision = '2025_01_05_0001'
down_revision = '2025_01_01_0001'
branch_labels = None
depends_on = None


def upgrade():
    """Seed the plans table with pricing tiers including Stripe price IDs"""

    # Create a connection
    conn = op.get_bind()

    # Define plans data
    plans = [
        {
            'id': str(uuid.uuid4()),
            'name': 'Free',
            'monthly_requests': 100,
            'price_cents': 0,
            'stripe_price_id': None,
            'features': {
                'rate_limit': 60,
                'support': 'community',
                'requests': 100
            }
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Developer',
            'monthly_requests': 10000,
            'price_cents': 4900,
            'stripe_price_id': 'price_1SQDreLoE1yvarSwfhdcYpOd',
            'features': {
                'rate_limit': 300,
                'support': 'email',
                'requests': 10000,
                'analytics': True
            }
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Growth',
            'monthly_requests': 100000,
            'price_cents': 29900,
            'stripe_price_id': 'price_1SQDrfLoE1yvarSw1sWkBwZC',
            'features': {
                'rate_limit': 1000,
                'support': 'priority',
                'requests': 100000,
                'analytics': True,
                'sla': '99.9%'
            }
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'Enterprise',
            'monthly_requests': 1000000,
            'price_cents': 99900,
            'stripe_price_id': 'price_1SQDrfLoE1yvarSwaVXoZMol',
            'features': {
                'rate_limit': 'custom',
                'support': 'dedicated',
                'requests': 'custom',
                'analytics': True,
                'sla': '99.99%',
                'custom_contract': True
            }
        }
    ]

    # Insert plans with upsert logic
    for plan in plans:
        # Check if plan exists
        result = conn.execute(
            sa.text("SELECT id FROM plans WHERE name = :name"),
            {"name": plan['name']}
        ).fetchone()

        features_json = json.dumps(plan['features'])

        if result:
            # Update existing plan
            conn.execute(
                sa.text("""
                    UPDATE plans
                    SET monthly_requests = :monthly_requests,
                        price_cents = :price_cents,
                        stripe_price_id = :stripe_price_id,
                        features = :features::jsonb
                    WHERE name = :name
                """),
                {
                    "name": plan['name'],
                    "monthly_requests": plan['monthly_requests'],
                    "price_cents": plan['price_cents'],
                    "stripe_price_id": plan['stripe_price_id'],
                    "features": features_json
                }
            )
        else:
            # Insert new plan
            conn.execute(
                sa.text("""
                    INSERT INTO plans (id, name, monthly_requests, price_cents, stripe_price_id, features)
                    VALUES (:id::uuid, :name, :monthly_requests, :price_cents, :stripe_price_id, :features::jsonb)
                """),
                {
                    "id": plan['id'],
                    "name": plan['name'],
                    "monthly_requests": plan['monthly_requests'],
                    "price_cents": plan['price_cents'],
                    "stripe_price_id": plan['stripe_price_id'],
                    "features": features_json
                }
            )


def downgrade():
    """Remove seeded plans"""
    conn = op.get_bind()

    # Delete all plans that were seeded
    conn.execute(
        sa.text("DELETE FROM plans WHERE name IN ('Free', 'Developer', 'Growth', 'Enterprise')")
    )
