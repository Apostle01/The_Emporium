from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from haven.models import Product, Profile

# from paypal.standard.forms import PayPalPaymentsForm
# import uuid

from django.http import JsonResponse

def process_order(request):
    if request.POST:
        # Get the cart
        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()

        # Get Billing Info from the last page
        payment_form = PaymentForm(request.POST or None)

        # Get Shipping Session Data
        my_shipping = request.session.get('my_shipping')

        # Gather Order Info
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']

        # Create Shipping Address from session info
        shipping_address = (
            f"{my_shipping['shipping_address1']}\n"
            f"{my_shipping['shipping_address2']}\n"
            f"{my_shipping['shipping_city']}\n"
            f"{my_shipping['shipping_state']}\n"
            f"{my_shipping['shipping_zipcode']}\n"
            f"{my_shipping['shipping_country']}"
        )
        amount_paid = totals

        # Create an Order
        if request.user.is_authenticated:
            # Logged-in user
            user = request.user
            create_order = Order(
                user=user, 
                full_name=full_name, 
                email=email, 
                shipping_address=shipping_address, 
                amount_paid=amount_paid
            )
            create_order.save()

            # Add order items
            # Get order ID
            order_id = create_order.pk
            # Get product ID
            for product in cart_products():
                product_id = product.id
                # Get product price
                price = product.sale_price if product.is_sale else product.price
                # Get quantity
                for key, value in quantities().items():
                    if int(key) == product.id:
                        # Create order item
                        create_order_item = OrderItem(
                            order_id=order_id, 
                            product_id=product_id, 
                            user=user, 
                            quantity=value, 
                            price=price
                        )
                        create_order_item.save()

            # Delete cart session
            for key in list(request.session.keys()):
                if key == "session_key":
                    del request.session[key]

            # Delete old cart from Profile
            Profile.objects.filter(user__id=request.user.id).update(old_cart="")

            messages.success(request, "Order Placed!")
            return redirect('home')

        else:
            # Guest user
            create_order = Order(
                full_name=full_name, 
                email=email, 
                shipping_address=shipping_address, 
                amount_paid=amount_paid
            )
            create_order.save()

            # Add order items
            order_id = create_order.pk
            for product in cart_products():
                product_id = product.id
                price = product.sale_price if product.is_sale else product.price
                for key, value in quantities().items():
                    if int(key) == product.id:
                        create_order_item = OrderItem(
                            order_id=order_id, 
                            product_id=product_id, 
                            quantity=value, 
                            price=price
                        )
                        create_order_item.save()

            # Delete cart session
            for key in list(request.session.keys()):
                if key == "session_key":
                    del request.session[key]

            messages.success(request, "Order Placed!")
            return redirect('home')

    else:
        messages.success(request, "Access Denied")
        return redirect('home')

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
