#!/bin/bash

###############################################################################
# Script to Recreate ElastiCache Serverless Redis Cluster
#
# This script recreates the medcode-redis cluster with the exact same
# configuration that was captured before deletion.
#
# Configuration captured on: 2025-11-20
# Original cluster created: 2025-11-04
#
# Usage:
#   ./scripts/redis-recreate.sh
#
###############################################################################

set -e

REGION="us-east-2"
CACHE_NAME="medcode-redis"
ENGINE="redis"
MAJOR_VERSION="7"
SECURITY_GROUP_ID="sg-00d94a19d50a936da"  # nuvii-redis-sg
SUBNET_IDS="subnet-052e86ae1eed57aa0 subnet-01040f05784d29041"
SNAPSHOT_RETENTION=1
SNAPSHOT_TIME="04:58"

echo "🚀 Redis Cluster Recreation Script"
echo "===================================="
echo ""
echo "Configuration:"
echo "  Name:              $CACHE_NAME"
echo "  Engine:            $ENGINE $MAJOR_VERSION"
echo "  Region:            $REGION"
echo "  Security Group:    $SECURITY_GROUP_ID"
echo "  Subnets:           $SUBNET_IDS"
echo "  Snapshot Retention: $SNAPSHOT_RETENTION days"
echo "  Snapshot Time:     $SNAPSHOT_TIME UTC"
echo ""

# Check if cluster already exists
echo "🔍 Checking if Redis cluster already exists..."
EXISTING=$(aws elasticache describe-serverless-caches \
  --serverless-cache-name $CACHE_NAME \
  --region $REGION \
  --query 'ServerlessCaches[0].Status' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$EXISTING" != "NOT_FOUND" ]; then
    echo "❌ Error: Redis cluster '$CACHE_NAME' already exists with status: $EXISTING"
    echo ""
    echo "To delete it first, run:"
    echo "  ./scripts/redis-delete.sh"
    exit 1
fi

echo "✅ No existing cluster found. Proceeding with creation..."
echo ""

# Create the serverless cache
echo "🔧 Creating ElastiCache Serverless Redis cluster..."
echo ""

aws elasticache create-serverless-cache \
  --serverless-cache-name $CACHE_NAME \
  --engine $ENGINE \
  --major-engine-version $MAJOR_VERSION \
  --description "Redis cache for rate limiting and session management" \
  --security-group-ids $SECURITY_GROUP_ID \
  --subnet-ids $SUBNET_IDS \
  --snapshot-retention-limit $SNAPSHOT_RETENTION \
  --daily-snapshot-time $SNAPSHOT_TIME \
  --region $REGION

echo ""
echo "✅ Redis cluster creation initiated!"
echo ""
echo "⏳ Cluster is being created (this takes 5-10 minutes)..."
echo ""

# Wait for cluster to become available
echo "Waiting for cluster to be available..."
aws elasticache wait serverless-cache-available \
  --serverless-cache-name $CACHE_NAME \
  --region $REGION

echo ""
echo "✅ Redis cluster is now available!"
echo ""

# Get the endpoint
ENDPOINT=$(aws elasticache describe-serverless-caches \
  --serverless-cache-name $CACHE_NAME \
  --region $REGION \
  --query 'ServerlessCaches[0].Endpoint.Address' \
  --output text)

PORT=$(aws elasticache describe-serverless-caches \
  --serverless-cache-name $CACHE_NAME \
  --region $REGION \
  --query 'ServerlessCaches[0].Endpoint.Port' \
  --output text)

echo "📋 Cluster Details:"
echo "  Endpoint: $ENDPOINT:$PORT"
echo "  REDIS_URL: redis://$ENDPOINT:$PORT/0"
echo ""

# Update task definition
echo "📝 Next Steps:"
echo "=============="
echo ""
echo "1. Update your ECS task definition with the new REDIS_URL:"
echo ""
echo "   REDIS_URL=redis://$ENDPOINT:$PORT/0"
echo ""
echo "2. Register new task definition revision and update service:"
echo ""
echo "   # Edit task definition to add/update REDIS_URL"
echo "   aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION"
echo ""
echo "   # Update service to use new task definition"
echo "   aws ecs update-service \\"
echo "     --cluster <your-cluster-name> \\"
echo "     --service <your-service-name> \\"
echo "     --task-definition <task-family> \\"
echo "     --force-new-deployment \\"
echo "     --region $REGION"
echo ""
echo "3. Monitor logs to verify Redis connection:"
echo ""
echo "   aws logs tail /ecs/nuvii-api --follow --region $REGION"
echo ""
echo "   Expected log message:"
echo "   INFO: Redis connection successful"
echo ""
echo "💰 Monthly Cost: ~\$90-150 (serverless pricing)"
echo ""
