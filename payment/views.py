from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from haven.models import Product, Profile
import datetime

# from paypal.standard.forms import PayPalPaymentsForm
# import uuid

from django.http import JsonResponse

def orders(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        # Get the order
        order = Order.objects.get(id=pk)
        # Get the order items
        items = OrderItem.objects.filter(order=pk)
        
        if request.POST:
            status = request.POST['shipping_status']
            # Check if true or false
            if status == "true":
                # Get the order
                order = Order.objects.filter(id=pk)
                # Update the status
                now = datetime.datetime.now()
                order.update(shipped=True, date_shipped=now)
            else:
                 # Get the order
                order = Order.objects.filter(id=pk)
                # Update the status
                order.update(shipped=False)
            messages.success(request, "Shipping Status Updated")
            return redirect('home')
        
        return render(request, 'payment/orders.html', {"order":order, "items":items})
    else:
        messages.success(request, "Access Denied")
        return redirect('home')

def not_shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        # Fetch orders that have not been shipped
        orders = Order.objects.filter(shipped=False)
        
        if request.method == 'POST':
            # Get shipping status and order ID from the POST request
            status = request.POST.get('shipping_status')
            num = request.POST.get('num')
            
            # Check if 'num' is valid
            if not num or not num.isdigit():
                messages.error(request, "Invalid Order ID.")
                return redirect('not_shipped_dash')
            
            # Get the order and update its shipping status
            order = Order.objects.filter(id=num).first()
            if order:
                now = datetime.datetime.now()
                order.shipped = True
                order.date_shipped = now
                order.save()
                messages.success(request, f"Shipping status for Order {num} updated successfully.")
            else:
                messages.error(request, f"Order with ID {num} does not exist.")
            
            return redirect('not_shipped_dash')
        
        # Render the dashboard page with the unshipped orders
        return render(request, 'payment/not_shipped_dash.html', {"orders": orders})
    
    else:
        # Redirect non-superuser or unauthenticated users
        messages.error(request, "Access Denied.")
        return redirect('home')


def shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=True)
        if request.POST:
            status = request.POST['shipping_status']
            num = request.POST['num']
            # Get the order
            order = Order.objects.filter(id=num)
            # grab Date and Time
            now = datetime.datetime.now()
            # update order
            order.update(shipped=False)
            # redirect
            messages.success(request, "Shipping Status Updated")
            return redirect('home')
        
        return render(request, "payment/shipped_dash.html", {"orders":orders})
    else:
        messages.success(request, "Access Denied")
        return redirect('home')

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
                    # Delete the key
                    del request.session[key]

            # Delete old cart from Profile(Database)
            current_user = Profile.objects.filter(user__id=request.user.id)
            # Delete shopping cart in database
            current_user.update(old_cart="")

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
