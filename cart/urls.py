from django.urls import path
from cart.views import *

urlpatterns = [
    path('view/', CartDetailView.as_view(), name='cart-detail'), #view
    path('add/', AddToCartView.as_view(), name='add-to-cart'), #add to cart
    path('remove/<int:pk>/', RemoveFromCartView.as_view(), name='remove-from-cart'), #cart details
    #filter cart by product type
    path('grocery-cart/', GroceryCartView.as_view(), name='cart-grocery'),
    path('dishes-cart/', DishCartView.as_view(), name='cart-dishes'),
    path('fashion-cart/', ClothingCartView.as_view(), name='cart-clothing'),
    #checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'), #checkout
    path('orders/', CheckoutListView.as_view(), name='order-list'), #view orders
    path('orders/<int:pk>/', CheckoutDetailView.as_view(), name='order-detail'), #Order details
    path('orders/<int:pk>/cancel/', CancelOrderView.as_view(), name='cancel-order'), #order delete
    #orders
    path('orders/admin/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),  # Admin can update & delete order
    path('user/orders/', UserOrderListView.as_view(), name='user-orders'),  # Get orders of logged-in user
    path('orders/<str:order_id>/', UserOrderDetailView.as_view(), name='user-order-detail'),#user order details
    path('orders/update-status/<str:order_id>/', UpdateOrderStatusView.as_view(), name='update-order-status'),  # Admin can update order status
    path('order-list-admin/', AllorderviewAdmin.as_view(), name='0rder-list-admin'), #list all orders
    #orders by vendors
    path('vendor/orders/', VendorOrderListView.as_view(), name='vendor-orders'),
    path('vendor/orders/<str:order_id>/', VendorOrderDetailView.as_view(), name='vendor-order-detail'),#vendor order detail
    # cart group
    path('cart/grouped/', GroupedCartView.as_view(), name='grouped-cart'),
    #single vendor cart
    path('cart/vendor/<int:vendor_id>/', VendorCartItemsView.as_view(), name='vendor-cart-items'),
    path('checkout/<int:pk>/', VendorCheckoutView.as_view(), name='vendor-checkout'), #check out
    #order cancel 
    path('order/cancel/<str:order_id>/', UpdateOrderStatusViewUser.as_view(), name='update-order-status'),  

]



