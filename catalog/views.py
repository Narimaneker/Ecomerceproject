from django.conf import settings
from django.urls import reverse
from django.utils import timezone  
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
import stripe

from .models import Item, Order, OrderItem


# Page d'accueil
class HomeView(ListView):
    model = Item
    template_name = 'homepage.html'

# Détails du produit
class ProductDetail(DetailView):
    model = Item
    template_name = 'product.html'

# Affichage de tous les produits
def product_view(request):
    products = Item.objects.all()
    return render(request, 'products.html', {'products': products})

# Page de checkout
from django.shortcuts import render, get_object_or_404
from .models import Order

def checkout(request):
    order = Order.objects.filter(user=request.user, ordered=False).first()
    return render(request, 'checkout.html', {'order': order})


# Ajouter un produit au panier
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import OrderItem, Order
from django.contrib import messages

from django.http import JsonResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Order
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY  


def get_cart_total(request):
    order = None
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, ordered=False).first()

    # Check if the correct method exists
    if order:
        if hasattr(order, "get_total_price"):  # If `get_total_price` exists
            total = order.get_total_price()
        elif hasattr(order, "get_total_item_price"):  # If `get_total_item_price` exists
            total = order.get_total_item_price()
        else:
            total = 0  # If neither exists
    else:
        total = 0

    return JsonResponse({"total": total})


def create_checkout_session(request):
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'Produit Test'},
                        'unit_amount': 2000,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('checkout_success')),
                cancel_url=request.build_absolute_uri(reverse('checkout_cancel')),
            )
            return JsonResponse({'sessionId': session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


from django.views.decorators.csrf import csrf_exempt
import json

import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import Item, OrderItem, Order

import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import Item, OrderItem, Order

def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_quantity = int(data.get("quantity", 1))  # Get quantity from request
        except (json.JSONDecodeError, ValueError):
            new_quantity = 1  # Default to 1 if invalid input
    else:
        new_quantity = 1  # Default for non-POST requests

    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )

    # ✅ Increase the quantity each time the button is clicked
    order_item.quantity += new_quantity  # Add the new quantity
    order_item.save()

    # Ensure order exists
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs.first()
        if not order.items.filter(item__slug=item.slug).exists():
            order.items.add(order_item)
    else:
        order = Order.objects.create(user=request.user)
        order.items.add(order_item)

    # Return updated cart data for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "quantity": order_item.quantity,
            "total_price": order.get_total_price()
        })

    return redirect("order_summary")

 
def decrease_quantity(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, user=request.user, ordered=False)

    if order_item.quantity > 1:
        order_item.quantity -= 1
        order_item.save()
    else:
        order_item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # AJAX request
        return JsonResponse({"quantity": order_item.quantity if order_item.quantity > 0 else 0, "price": float(order_item.item.price)})

    return redirect("order_summary")

# Supprimer un produit du panier
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if not order_qs.exists():
        messages.info(request, "You do not have an active order.")
        return redirect('product_detail', slug=slug)

    order = order_qs.first()

    if not order.items.filter(item__slug=item.slug).exists():
        messages.info(request, f"{item.title} was not in your cart.")
        return redirect('product_detail', slug=slug)

    # Remove item completely instead of decreasing quantity
    order_item = order.items.get(item__slug=item.slug)
    order.items.remove(order_item)  # Remove from order
    order_item.delete()  # Delete the order item completely

    messages.info(request, f"{item.title} was completely removed from your cart.")
    return redirect('order_summary')

# Récapitulatif de la commande
def order_summary(request):
    order = Order.objects.filter(user=request.user, ordered=False).first()
    return render(request, 'order_summary.html', {'order': order})

from django.shortcuts import render

def checkout_success(request):
    order = Order.objects.filter(user=request.user, ordered=True).last()
    return render(request, 'checkout_success.html', {'order': order})

def checkout_cancel(request):
    return render(request, 'checkout_cancel.html')

class PayementView(View):
    def get(self, *args, **kwargs):
        return render(self.request, 'payment.html')

    def post(self, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY  # Ensure your Stripe secret key is set

        token = self.request.POST.get('stripeToken')  # Get the token from the form
        order = Order.objects.filter(user=self.request.user, ordered=False).first()

        if not order:
            messages.error(self.request, "No active order found.")
            return redirect("order_summary")

        try:
            # Create a customer in Stripe
            customer = stripe.Customer.create(
                email=self.request.user.email,
                name=self.request.user.username,
                source=token
            )

            # Create a charge on the customer's card
            charge = stripe.Charge.create(
                customer=customer.id,
                amount=int(order.get_total_price() * 100),  # Convert to cents
                currency="usd",
                description=f"Charge for {self.request.user.email}"
            )

            # If payment is successful, mark the order as completed
            order.ordered = True
            order.ordered_date = timezone.now()
            order.save()

            messages.success(self.request, "Your payment was successful!")
            return redirect("checkout_success")

        except stripe.error.CardError as e:
            messages.error(self.request, f"Card error: {e.error.message}")
        except stripe.error.RateLimitError:
            messages.error(self.request, "Rate limit error, try again later.")
        except stripe.error.InvalidRequestError:
            messages.error(self.request, "Invalid payment request.")
        except stripe.error.AuthenticationError:
            messages.error(self.request, "Authentication error, check Stripe credentials.")
        except stripe.error.APIConnectionError:
            messages.error(self.request, "Network error, please try again.")
        except stripe.error.StripeError:
            messages.error(self.request, "Payment failed, please try again.")

        return redirect("payment", payment_option="stripe")


import stripe
from django.http import JsonResponse
from django.conf import settings
import json

def create_checkout_session(request):
    if request.method == "POST":
        data = json.loads(request.body)
        
        # Store billing details (Optional: Save them in the database)
        name = data.get("name")
        family_name = data.get("family_name")
        address = data.get("address")
        zip_code = data.get("zip")
        phone = data.get("phone")

        stripe.api_key = settings.STRIPE_SECRET_KEY

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Order Payment'},
                    'unit_amount': int(request.user.order.get_total_price() * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=settings.SITE_URL + "/success/",
            cancel_url=settings.SITE_URL + "/cancel/"
        )

        return JsonResponse({'id': session.id})

    return JsonResponse({'error': 'Invalid request'}, status=400)



from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from django.shortcuts import get_object_or_404
from .models import Order

def generate_facture(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, ordered=True)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    # Create a PDF canvas
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "INVOICE")

    # Order details
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Order ID: {order.id}")
    p.drawString(50, height - 100, f"Customer: {order.user.username}")
    p.drawString(50, height - 120, f"Date: {order.ordered_date.strftime('%Y-%m-%d')}")

    # Table Data (Headers)
    data = [["Product", "Quantity", "Price", "Total"]]

    # Add items to the table
    for item in order.items.all():
        data.append([
            item.item.title,  # Product Name
            str(item.quantity),  # Quantity
            f"${item.item.price}",  # Price per item
            f"${item.get_total_item_price()}"  # Total price per item
        ])

    # Add total row
    data.append(["", "", "Total:", f"${order.get_total_price()}"])

    # Create table
    table = Table(data, colWidths=[200, 100, 100, 100])

    # Add styles (Borders, Colors, Alignment)
    style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Borders for all cells
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align all columns except first
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold headers
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Padding for headers
    ])
    table.setStyle(style)

    # Draw the table on the PDF
    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height - 300)  # Position the table

    # Save and return the response
    p.showPage()
    p.save()
    return response
