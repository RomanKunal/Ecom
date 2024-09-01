from django.urls import path

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),

	path('update_item/', views.updateItem, name="update_item"),
	# path('process_order/', views.processOrder, name="process_order"),
    path('initiate_payment/', views.initiate_payment, name='initiate_payment'),
    path('handle_payment/', views.handle_payment, name='handle_payment'),

]