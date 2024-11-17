from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress
from django.contrib import messages
# from paypal.standard.forms import PayPalPaymentsForm
# import uuid

from django.http import JsonResponse

def process_order(request):
    # Placeholder logic for order processing
    return JsonResponse({'message': 'Order processed successfully!'})

def billing_info(request):
    if request.POST:
        # Get the cart
        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()

        # Create a session with Shipping Info
        my_shipping = request.POST
        request.session['my_shipping'] = my_shipping

        # # Get the host
        # host = request.get_host()

        # # Create Paypal Form Dictionary
        # paypal_dict = {
        #     'business': settings.PAYPAL_RECEIVER_EMAIL,
        #     'amount': totals,
        #     'item_name': 'Book Order',
        #     'no_shipping': '2',
        #     'invoice': str(uuid.uuid4()),
        #     'currency_code': 'USD',  # EUR for Euros
        #     'notify_url': f'https://{host}{reverse("paypal-ipn")}',
        #     'return_url': f'https://{host}{reverse("payment_success")}',
        #     'cancel_return': f'https://{host}{reverse("payment_failed")}',
        # }

        # # Create actual PayPal button
        # paypal_form = PayPalPaymentsForm(initial=paypal_dict)

        # Check to see if user is logged in
        if request.user.is_authenticated:
            # Get The Billing Form
            billing_form = PaymentForm()
            return render(request, "payment/billing_info.html", {
                "cart_products": cart_products,
                "quantities": quantities,
                "totals": totals,
                "shipping_info": request.POST,
                "billing_form": billing_form,
            })
        else:
            # Not logged in
            billing_form = PaymentForm()
            return render(request, "payment/billing_info.html", {
                "cart_products": cart_products,
                "quantities": quantities,
                "totals": totals,
                "shipping_info": request.POST,
                "billing_form": billing_form,
            })
    else:
        messages.success(request, "Access Denied")
        return redirect('home')


def update_shipping(request):
    shipping_info = ShippingAddress.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = ShippingForm(request.POST, instance=shipping_info)
        if form.is_valid():
            form.save()
            return redirect('billing_info')  # Redirect to the billing info page
        else:
            return redirect('billing_info')
    else:
        return redirect('login')  # Redirect to login if not authenticated


def checkout(request):
    # Get the cart
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()

    if request.user.is_authenticated:
        # Check as logged-in user
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        return render(request, "payment/checkout.html", {
            "cart_products": cart_products,
            "quantities": quantities,
            "totals": totals,
            "shipping_form": shipping_form,
        })
    else:
        # Check as guest
        shipping_form = ShippingForm(request.POST or None)
        return render(request, "payment/checkout.html", {
            "cart_products": cart_products,
            "quantities": quantities,
            "totals": totals,
            "shipping_form": shipping_form,
        })


def payment_success(request):
    return render(request, "payment/payment_success.html", {})


def payment_failed(request):
    return render(request, "payment/payment_failed.html", {})
