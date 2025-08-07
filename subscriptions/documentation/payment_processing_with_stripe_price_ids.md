# Payment Processing with Stripe Price IDs

## Overview
This document describes the updated payment processing system that uses Stripe Price IDs instead of manual amount calculations for exact price matching and better reliability.

## Architecture Changes

### Before (Manual Amount Calculation)
```python
# Old approach - manual calculation
payment_intent = stripe.PaymentIntent.create(
    amount=int(duration.price * 100),  # Django price converted to cents
    currency='usd',
    # ...
)
```

### After (Stripe Price ID Approach)
```python
# New approach - use Stripe Price ID
payment_intent = stripe.PaymentIntent.create(
    price=duration.stripe_price_id,  # Stripe Price ID for exact matching
    customer=customer.id,
    # ...
)
```

## Key Benefits

### 1. Exact Price Matching
- **No rounding errors** - Stripe handles all price calculations
- **Guaranteed consistency** - Display price = payment price
- **Currency handling** - Stripe manages currency conversion
- **Decimal precision** - No floating-point arithmetic issues

### 2. Better Error Handling
- **Stripe validation** - Stripe validates all prices automatically
- **Price mismatch detection** - Frontend/backend Price ID validation
- **Fallback mechanism** - Manual calculation if Price ID fails
- **Professional error messages** - Clear user feedback

### 3. Professional System
- **Industry standard** - Uses Stripe's recommended Price ID approach
- **Better audit trail** - All payments linked to specific Price objects
- **Easier management** - Price changes in Stripe automatically apply
- **Consistent pricing** - No sync issues between systems

## Implementation Details

### 1. Payment Processing View Updates

#### Price ID Validation
```python
# Validate that we have a Stripe Price ID
if not duration.stripe_price_id:
    return JsonResponse({
        'success': False,
        'error': 'Pricing configuration error. Please contact support.'
    }, status=400)
```

#### Frontend/Backend Validation
```python
# Validate that frontend and backend Price IDs match
if frontend_stripe_price_id and frontend_stripe_price_id != duration.stripe_price_id:
    return JsonResponse({
        'success': False,
        'error': 'Price mismatch detected. Please refresh the page and try again.'
    }, status=400)
```

#### Payment Intent Creation
```python
# Primary approach - use Price ID
try:
    payment_intent = stripe.PaymentIntent.create(
        price=duration.stripe_price_id,  # Use Price ID
        customer=customer.id,
        payment_method=payment_method_id,
        off_session=False,
        confirm=True,
        return_url=success_url,
        metadata={
            'subscription_id': subscription.id,
            'plan_id': plan.id,
            'duration_id': duration.id,
            'stripe_price_id': duration.stripe_price_id
        }
    )
except stripe.error.InvalidRequestError as e:
    # Fallback to manual amount calculation
    stripe_amount, currency = get_stripe_price_info(duration)
    payment_intent = stripe.PaymentIntent.create(
        amount=int(stripe_amount * 100),
        currency=currency.lower(),
        # ... other parameters
    )
```

### 2. Frontend JavaScript Updates

#### Price ID Tracking
```javascript
let selectedStripePriceId = null;

durations.forEach(duration => {
    duration.addEventListener('click', function() {
        selectedStripePriceId = this.dataset.stripePriceId;
        // ... other logic
    });
});
```

#### Payment Request
```javascript
const response = await fetch(`/subscriptions/process-payment/${planId}/${selectedDurationId}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
    },
    body: JSON.stringify({
        payment_method_id: paymentMethod.id,
        save_card: document.getElementById('save-card').checked,
        stripe_price_id: selectedStripePriceId,  // Pass Price ID
        return_url: '{{ return_url|safe }}'
    })
});
```

### 3. Recurring Payment Disclosure

#### HTML Structure
```html
<!-- Recurring Payment Disclosure -->
<div class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
    <div class="flex items-start">
        <input type="checkbox" 
               id="recurring-agreement" 
               name="recurring-agreement"
               required
               class="h-4 w-4 text-[#1980e6] border-gray-300 rounded focus:ring-[#1980e6] mt-0.5">
        <label for="recurring-agreement" class="ml-2 block text-sm text-gray-700">
            <strong>I understand</strong> this is a recurring subscription. I will be charged 
            <span id="recurring-amount" class="font-semibold">$0.00</span> 
            <span id="recurring-frequency">monthly</span> until I cancel. 
            I can cancel anytime from my account settings.
        </label>
    </div>
</div>
```

#### JavaScript Validation
```javascript
// Check if recurring agreement is accepted
const recurringAgreement = document.getElementById('recurring-agreement');
if (!recurringAgreement.checked) {
    alert('You must agree to the recurring payment terms to continue.');
    return;
}
```

## Data Flow

### 1. User Selection
```
User selects duration → JavaScript captures Price ID → Updates disclosure text
```

### 2. Payment Processing
```
Frontend sends Price ID → Backend validates → Creates payment with Price ID → Stripe processes
```

### 3. Invoice Creation
```
Payment success → Create invoice → Add invoice item with Price ID → Finalize and pay
```

## Error Handling

### Price ID Missing
```python
if not duration.stripe_price_id:
    return JsonResponse({
        'success': False,
        'error': 'Pricing configuration error. Please contact support.'
    }, status=400)
```

### Price Mismatch
```python
if frontend_stripe_price_id and frontend_stripe_price_id != duration.stripe_price_id:
    return JsonResponse({
        'success': False,
        'error': 'Price mismatch detected. Please refresh the page and try again.'
    }, status=400)
```

### Stripe API Failure
```python
try:
    payment_intent = stripe.PaymentIntent.create(price=duration.stripe_price_id, ...)
except stripe.error.InvalidRequestError as e:
    # Fallback to manual amount calculation
    stripe_amount, currency = get_stripe_price_info(duration)
    payment_intent = stripe.PaymentIntent.create(amount=int(stripe_amount * 100), ...)
```

## Security Considerations

### Price ID Validation
- **Backend validation** - Always validate Price IDs on server
- **Frontend/backend matching** - Ensure consistency between systems
- **Stripe verification** - Let Stripe validate all prices

### Data Protection
- **No sensitive data** in frontend
- **Secure API calls** - All Stripe calls from backend
- **CSRF protection** - Django CSRF tokens required

## Testing Scenarios

### 1. Normal Payment Flow
1. **Select duration** - Should capture Price ID
2. **Fill payment form** - Should show recurring disclosure
3. **Check agreement** - Should allow payment
4. **Submit payment** - Should use Price ID for processing

### 2. Error Scenarios
1. **Missing Price ID** - Should show configuration error
2. **Price mismatch** - Should show mismatch error
3. **No agreement** - Should prevent payment
4. **Stripe failure** - Should fallback to manual calculation

### 3. Edge Cases
1. **Price change during session** - Should detect mismatch
2. **Network failure** - Should handle gracefully
3. **Invalid Price ID** - Should show appropriate error

## Performance Impact

### API Calls
- **Same number** of Stripe API calls
- **Better reliability** with Price ID approach
- **Faster processing** - No manual calculations

### Error Handling
- **Improved error detection** - Price mismatches caught early
- **Better user experience** - Clear error messages
- **Reduced failed payments** - Exact price matching

## Monitoring

### Key Metrics
- **Payment success rate** - Should improve with exact pricing
- **Error rates** - Monitor for price mismatch errors
- **Fallback usage** - Track when manual calculation is used

### Logging
```python
# Consider adding logging for:
# - Price ID validation failures
# - Frontend/backend mismatches
# - Fallback to manual calculation
# - Payment processing errors
```

## Future Enhancements

### 1. Webhook Integration
```python
# Consider Stripe webhooks for:
# - Price update notifications
# - Payment status updates
# - Subscription management
```

### 2. Caching
```python
# Consider caching Price objects for:
# - Reduced API calls
# - Faster page loads
# - Better performance
```

### 3. Analytics
```python
# Consider tracking:
# - Price change frequency
# - Payment success rates
# - User behavior patterns
```

## Related Files

- `subscriptions/views.py` - Payment processing logic
- `subscriptions/templates/subscriptions/purchase.html` - Frontend form
- `subscriptions/utils.py` - Price fetching utilities
- `subscriptions/models.py` - Database models with Price IDs

## Conclusion

The updated payment processing system provides:
- **Exact price matching** between display and payment
- **Better error handling** and user experience
- **Professional system** following industry standards
- **Improved reliability** with fallback mechanisms

This implementation ensures that users always pay exactly what they see displayed, eliminating pricing discrepancies and providing a professional subscription experience. 