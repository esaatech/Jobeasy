# Stripe Live Mode Setup for Cloud Deployment

## Overview
This document explains how to set up Stripe live mode for cloud deployment.

## Environment Variables Required

### Stripe API Keys (Live Mode)
```bash
MYAPP_STRIPE_SECRET_KEY=sk_live_your_live_secret_key_here
MYAPP_STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key_here
```

### Stripe Price IDs (Live Mode)
```bash
STRIPE_PLUS_MONTHLY_PRICE_ID=price_live_plus_monthly_id_here
STRIPE_PLUS_ANNUAL_PRICE_ID=price_live_plus_annual_id_here
STRIPE_ULTIMATE_MONTHLY_PRICE_ID=price_live_ultimate_monthly_id_here
STRIPE_ULTIMATE_ANNUAL_PRICE_ID=price_live_ultimate_annual_id_here
```

## Cloud Deployment Setup

### 1. Set Environment Variables
In your cloud platform (Railway, Heroku, etc.), set these environment variables:

**Required:**
- `MYAPP_STRIPE_SECRET_KEY` - Your live Stripe secret key
- `MYAPP_STRIPE_PUBLISHABLE_KEY` - Your live Stripe publishable key

**Optional (for automatic Price ID updates):**
- `STRIPE_PLUS_MONTHLY_PRICE_ID` - Live Price ID for Plus Monthly
- `STRIPE_PLUS_ANNUAL_PRICE_ID` - Live Price ID for Plus Annual
- `STRIPE_ULTIMATE_MONTHLY_PRICE_ID` - Live Price ID for Ultimate Monthly
- `STRIPE_ULTIMATE_ANNUAL_PRICE_ID` - Live Price ID for Ultimate Annual

### 2. Automatic Setup
The `entrypoint.sh` script will automatically:
1. Run database migrations
2. Set up subscription plans
3. Update Stripe Price IDs (if environment variables are provided)
4. Start the server

### 3. Manual Price ID Update (if needed)
If you prefer to update Price IDs manually after deployment:

```bash
python manage.py update_stripe_prices \
  --plus-monthly-id "price_live_plus_monthly_id" \
  --plus-annual-id "price_live_plus_annual_id" \
  --ultimate-monthly-id "price_live_ultimate_monthly_id" \
  --ultimate-annual-id "price_live_ultimate_annual_id"
```

## Getting Live Price IDs

1. **Go to Stripe Dashboard** → Live Mode
2. **Navigate to Products** → "Jobeas Subscription Plans"
3. **Click on each price** to get the Price ID
4. **Copy the Price IDs** (they start with `price_live_`)

## Testing Live Mode

### ⚠️ Important Warnings:
- **Real money** - Any successful payment will charge real money
- **No test cards** - Test cards will be rejected
- **Start small** - Test with the smallest subscription amount first

### Test Cards (for live mode):
- Use real credit cards only
- Start with small amounts ($1-5) for testing
- Monitor Stripe Dashboard for successful charges

## Verification

After deployment, verify live mode is working:

1. **Check environment variables** are set correctly
2. **Verify Price IDs** are updated in database
3. **Test with real card** (small amount)
4. **Check Stripe Dashboard** for live transactions

## Rollback to Test Mode

If you need to rollback to test mode:

1. **Update environment variables** to test keys
2. **Update Price IDs** to test Price IDs
3. **Redeploy** the application

## Security Notes

- **Never commit** live Stripe keys to version control
- **Use environment variables** for all sensitive data
- **Monitor** Stripe Dashboard for unusual activity
- **Set up webhooks** for production monitoring 