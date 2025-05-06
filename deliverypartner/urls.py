from django.urls import path
from deliverypartner.views import *


urlpatterns =[

    path('delivery_boys/', DeliveryBoyListCreateView.as_view(), name='delivery_boy_list_create'), #create
    path('delivery_boys/<int:pk>/', DeliveryBoyDetailView.as_view(), name='delivery_boy_detail'), #delivery boy details admin
    path('delivery_boys/user/<int:pk>/', DeliveryBoyDetailViewUser.as_view(), name='delivery_boy_detail_user'), #delivery boy details

    #login
    path('request-otp/', request_otp, name='request_otp'),
    path('login-with-otp/', login_with_otp, name='login_with_otp'),
    
]