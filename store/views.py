from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib import messages

import json
import datetime

from .models import *
from .utils import cookieCart, cartData, guestOrder
from .forms import CustomerCreationForm

# Create your views here.

def registerCustomer(request):

    form = CustomerCreationForm()

    if request.method == 'POST':

        form = CustomerCreationForm(request.POST)
        
        if form.is_valid():

            user = User.objects.create_user(
                username=form.cleaned_data['name'], 
                email=form.cleaned_data['email'], 
                password=form.cleaned_data['password1']
            )
            customer = Customer(
                user=user,
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'].lower()
            )
            customer.save()

            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)
            
            return redirect('store')

        else:
            messages.error(request, 'Form is not valid')

    return render(request, 'store/register_login.html', {'form':form})

def loginCustomer(request):

    page = 'login'

    if request.user.is_authenticated:
        return redirect('store')
    
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('store')
        else:
            messages.error(request, 'Email or Password is incorrect')

    return render(request, 'store/register_login.html', {'page':page})

def logoutCustomer(request):

    logout(request)
    
    return redirect('store')

def store(request):

    category = request.GET.get('category')
    
    if category == None:
        products = Product.objects.all()
    else:
        products = Product.objects.filter(category__name=category)

    categories = Category.objects.all()

    data = cartData(request)
    cartItems = data['cartItems']

    context = {
        'products':products, 
        'cartItems':cartItems,
        'categories':categories}
    
    return render(request, 'store/store.html', context)

def productPage(request, pk):

    product = get_object_or_404(Product, pk=pk)

    return render(request, 'store/product_page.html', {'product':product})

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

    return JsonResponse('Payment complete!', safe=False)