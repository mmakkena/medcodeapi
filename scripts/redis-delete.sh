#!/bin/bash

###############################################################################
# Script to Delete ElastiCache Serverless Redis Cluster
#
# This script safely deletes the medcode-redis cluster with optional
# final snapshot for data backup.
#
# Usage:
#   ./scripts/redis-delete.sh [--no-snapshot]
#
# Options:
#   --no-snapshot    Skip creating a final snapshot (default: create snapshot)
#
# Estimated Savings: ~$90-150/month
#
###############################################################################

set -e

REGION="us-east-2"
CACHE_NAME="medcode-redis"
CREATE_SNAPSHOT=true

# Parse arguments
if [ "$1" == "--no-snapshot" ]; then
    CREATE_SNAPSHOT=false
fi

echo "🗑️  Redis Cluster Deletion Script"
echo "===================================="
echo ""

# Check if cluster exists
echo "🔍 Checking if Redis cluster exists..."
CLUSTER_STATUS=$(aws elasticache describe-serverless-caches \
  --serverless-cache-name $CACHE_NAME \
  --region $REGION \
  --query 'ServerlessCaches[0].Status' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$CLUSTER_STATUS" == "NOT_FOUND" ]; then
    echo "❌ Redis cluster '$CACHE_NAME' not found. Nothing to delete."
    exit 0
fi

echo "✅ Found Redis cluster: $CACHE_NAME (status: $CLUSTER_STATUS)"
echo ""

# Get current configuration
ENDPOINT=$(aws elasticache describe-serverless-caches \
  --serverless-cache-name $CACHE_NAME \
  --region $REGION \
  --query 'ServerlessCaches[0].Endpoint.Address' \
  --output text)

echo "📋 Current Configuration:"
aws elasticache describe-serverless-caches \
  --serverless-cache-name $CACHE_NAME \
  --region $REGION \
  --query 'ServerlessCaches[0].[ServerlessCacheName,Engine,MajorEngineVersion,Status,Endpoint.Address]' \
  --output table

echo ""
echo "⚠️  WARNING: This will delete the Redis cluster!"
echo ""
echo "  Cluster Name: $CACHE_NAME"
echo "  Endpoint:     $ENDPOINT"
echo "  Region:       $REGION"
if [ "$CREATE_SNAPSHOT" == true ]; then
    SNAPSHOT_NAME="${CACHE_NAME}-final-$(date +%Y%m%d-%H%M%S)"
    echo "  Final Snapshot: $SNAPSHOT_NAME (will be created)"
else
    echo "  Final Snapshot: NONE (--no-snapshot specified)"
fi
echo ""
echo "💰 Estimated Monthly Savings: \$90-150"
echo ""

# Confirm deletion
read -p "Are you sure you want to delete this Redis cluster? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Deletion cancelled."
    exit 0
fi

echo ""
echo "🗑️  Deleting Redis cluster..."
echo ""

# Delete with or without snapshot
if [ "$CREATE_SNAPSHOT" == true ]; then
    SNAPSHOT_NAME="${CACHE_NAME}-final-$(date +%Y%m%d-%H%M%S)"
    echo "Creating final snapshot: $SNAPSHOT_NAME"

    aws elasticache delete-serverless-cache \
      --serverless-cache-name $CACHE_NAME \
      --final-snapshot-name $SNAPSHOT_NAME \
      --region $REGION

    echo ""
    echo "✅ Deletion initiated with final snapshot: $SNAPSHOT_NAME"
else
    aws elasticache delete-serverless-cache \
      --serverless-cache-name $CACHE_NAME \
      --region $REGION

    echo ""
    echo "✅ Deletion initiated (no snapshot)"
fi

echo ""
echo "⏳ Cluster is being deleted (this takes 2-5 minutes)..."
echo ""
echo "You can check the deletion progress with:"
echo "  aws elasticache describe-serverless-caches --serverless-cache-name $CACHE_NAME --region $REGION"
echo ""

# Optional: Wait for deletion
read -p "Wait for deletion to complete? (yes/no): " WAIT_CONFIRM

if [ "$WAIT_CONFIRM" == "yes" ]; then
    echo ""
    echo "Waiting for cluster deletion..."

    # Poll until cluster is gone
    while true; do
        STATUS=$(aws elasticache describe-serverless-caches \
          --serverless-cache-name $CACHE_NAME \
          --region $REGION \
          --query 'ServerlessCaches[0].Status' \
          --output text 2>/dev/null || echo "DELETED")

        if [ "$STATUS" == "DELETED" ]; then
            break
        fi

        echo "  Current status: $STATUS"
        sleep 10
    done

    echo ""
    echo "✅ Redis cluster deleted successfully!"
fi

echo ""
echo "📝 Next Steps:"
echo "=============="
echo ""
echo "1. Your application will automatically fall back to in-memory rate limiting"
echo "   (no changes needed to task definition or code)"
echo ""
echo "2. Monitor logs to verify fallback:"
echo ""
echo "   aws logs tail /ecs/nuvii-api --follow --region $REGION"
echo ""
echo "   Expected log messages:"
echo "   ERROR: Failed to connect to Redis: ..."
echo "   INFO: Falling back to in-memory rate limiting"
echo ""
echo "3. (Optional) Remove REDIS_URL from task definition to clean up:"
echo ""
echo "   # Edit task definition to remove REDIS_URL environment variable"
echo "   # Then register new revision and update service"
echo ""
echo "4. To recreate the cluster later (if needed):"
echo ""
echo "   ./scripts/redis-recreate.sh"
echo ""
if [ "$CREATE_SNAPSHOT" == true ]; then
    echo "5. Manage final snapshot:"
    echo ""
    echo "   # List snapshots"
    echo "   aws elasticache describe-serverless-cache-snapshots --region $REGION"
    echo ""
    echo "   # Delete snapshot when no longer needed:"
    echo "   aws elasticache delete-serverless-cache-snapshot --serverless-cache-snapshot-name $SNAPSHOT_NAME --region $REGION"
    echo ""
    echo "   Note: Snapshots cost ~\$0.05/GB/month"
    echo ""
fi
echo "💰 You're now saving ~\$90-150/month!"
echo ""
