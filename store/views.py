from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder

def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)



from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from . import checksum
from django.conf import settings

MERCHANT_KEY = "YOUR_PAYTM_MERCHANT_KEY"
MERCHANT_ID = "YOUR_PAYTM_MERCHANT_ID"
WEBSITE = "YOUR_WEBSITE"
INDUSTRY_TYPE_ID = "YOUR_INDUSTRY_TYPE"
CHANNEL_ID = "WEB"  # Usually 'WEB' or 'WAP'
CALLBACK_URL = "http://yourdomain.com/handle_payment/"  # Update with your callback URL

def initiate_payment(request):
    order_id = str(int(datetime.time.time()))  # A unique order id (use your logic)
    amount = request.session.get('order_total', '1')  # Total amount from session or other logic

    # Create the payment parameters
    paytm_params = {
        "MID": MERCHANT_ID,
        "ORDER_ID": order_id,
        "CUST_ID": "CUSTOMER_ID",  # You can use logged-in user's ID here
        "INDUSTRY_TYPE_ID": INDUSTRY_TYPE_ID,
        "CHANNEL_ID": CHANNEL_ID,
        "TXN_AMOUNT": amount,
        "WEBSITE": WEBSITE,
        "CALLBACK_URL": CALLBACK_URL,
    }

    # Generate checksum
    paytm_params['CHECKSUMHASH'] = checksum.generate_checksum(paytm_params, MERCHANT_KEY)

    # Render HTML form with Paytm parameters
    return render(request, 'store/paytm_redirect.html', {'paytm_params': paytm_params, 'payment_url': "https://securegw.paytm.in/order/process"})


@csrf_exempt
def handle_payment(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_checksum = received_data.pop('CHECKSUMHASH', [None])[0]
        verified = checksum.verify_checksum(received_data, paytm_checksum, MERCHANT_KEY)

        if verified:
            if received_data['RESPCODE'] == '01':
                # Payment success
                # Implement logic to update the order status, etc.
                return render(request, 'store/payment_success.html', {'response': received_data})
            else:
                # Payment failed
                return render(request, 'store/payment_failure.html', {'response': received_data})
        else:
            # Invalid checksum response
            return render(request, 'store/payment_failure.html', {'response': "Checksum Mismatch"})
