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
    path('vendor/order-update/<str:order_id>/', VendorOrderUpdateDetailView.as_view(), name='vendor-order-detail'),


    # cart group
    path('cart/grouped/', GroupedCartView.as_view(), name='grouped-cart'),#avoid
    #single vendor cart
    path('cart/vendor/<int:vendor_id>/', VendorCartItemsView.as_view(), name='vendor-cart-items'),
    path('checkout/<int:pk>/', VendorCheckoutView.as_view(), name='vendor-checkout'), #check out
    #order cancel 
    path('order-item/cancel/', CancelOrderItemView.as_view(), name='cancel-order-item'),
    path('order-item/return/', ReturnOrderItemView.as_view(), name='return-order-item'),
    path('delete-all-orders/', DeleteAllOrdersView.as_view(), name='delete-all-orders'),#delete all orders
    path('orders/<str:order_id>/cancel/',CancelOrderItemView.as_view(),name='cancel-order'),#cancel whole order
    # URL for cancelling a specific item within an order
    path('orders/<str:order_id>/items/<int:item_id>/cancel/',CancelOrderItemView.as_view(),name='cancel-order-item'),
    path('orders/<str:order_id>/items/',OrderItemsByOrderIDView.as_view(),name='order-items-by-id'),
    #notifications
    path('notifications/', UserNotificationListView.as_view(), name='user-notifications'),
    path('notifications/read/<int:notification_id>/', MarkNotificationAsReadView.as_view(), name='mark-notification-read'),
    #for return
    path('orders/<str:order_id>/return/', ReturnOrderItemView.as_view(), name='return-order'),
    path('orders/<str:order_id>/items/<int:item_id>/return/', ReturnOrderItemView.as_view(), name='return-order-item'),

    path('orders/<str:order_id>/items/<int:item_id>/update-status/',UpdateOrderItemStatusView.as_view(),name='update-order-item-status'),
    path('vendor/notifications/', VendorNotificationListView.as_view(), name='vendor-notifications'), #vendor notification list

]



