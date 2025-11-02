#!/bin/bash
# Script to set up Pub/Sub push subscription with public webhook URL

PROJECT_ID="articulate-fort-472520-p2"
TOPIC_NAME="gmail-notifications"
SUBSCRIPTION_NAME="gmail-notifications-push"

# Replace with your public webhook URL
# Examples:
#   - ngrok: https://abc123.ngrok.io/api/pubsub/webhook
#   - cloudflared: https://random-subdomain.trycloudflare.com/api/pubsub/webhook
#   - Deployed API: https://your-api-domain.com/api/pubsub/webhook

WEBHOOK_URL="${1}"

if [ -z "$WEBHOOK_URL" ]; then
    echo "Usage: $0 <public-webhook-url>"
    echo ""
    echo "Example with ngrok:"
    echo "  1. Start ngrok: ngrok http 5050"
    echo "  2. Run: $0 https://abc123.ngrok.io/api/pubsub/webhook"
    echo ""
    echo "Example with cloudflared:"
    echo "  1. Start cloudflared: cloudflared tunnel --url http://localhost:5050"
    echo "  2. Run: $0 https://random-subdomain.trycloudflare.com/api/pubsub/webhook"
    exit 1
fi

echo "Setting up push subscription..."
echo "Topic: $TOPIC_NAME"
echo "Webhook URL: $WEBHOOK_URL"
echo ""

# Delete existing pull subscription if it exists
echo "Checking for existing subscription..."
if gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "Deleting existing subscription..."
    gcloud pubsub subscriptions delete "$SUBSCRIPTION_NAME" --project="$PROJECT_ID"
fi

# Create push subscription
echo "Creating push subscription..."
gcloud pubsub subscriptions create "$SUBSCRIPTION_NAME" \
    --topic="$TOPIC_NAME" \
    --push-endpoint="$WEBHOOK_URL" \
    --project="$PROJECT_ID"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Push subscription created successfully!"
    echo ""
    echo "Subscription details:"
    gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" --project="$PROJECT_ID" | grep -A 5 pushConfig
else
    echo "✗ Failed to create push subscription"
    exit 1
fi

