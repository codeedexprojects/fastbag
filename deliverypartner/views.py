from django.shortcuts import render
from rest_framework import generics
from .models import DeliveryBoy
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from vendors.authentication import VendorJWTAuthentication


class DeliveryBoyListCreateView(generics.ListCreateAPIView):
    queryset = DeliveryBoy.objects.all()
    serializer_class = DeliveryBoySerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save()

class DeliveryBoyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DeliveryBoy.objects.all()
    serializer_class = DeliveryBoySerializer
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(delivery_boy):
    otp = generate_otp()
    delivery_boy.otp = otp
    delivery_boy.otp_expiration = timezone.now() + timedelta(minutes=5)  # OTP expires in 5 minutes
    delivery_boy.save()

    send_mail(
        'Your OTP for Login',
        f'Your OTP is {otp}. It will expire in 5 minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [delivery_boy.email],
    )

from rest_framework.views import APIView
# ---- Request OTP View ----
class RequestOTPView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                delivery_boy = DeliveryBoy.objects.get(email=email)
            except DeliveryBoy.DoesNotExist:
                return Response({"message": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)

            # Send OTP to the delivery boy's email
            send_otp_email(delivery_boy)

            return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ---- Login with OTP View ----

class LoginWithOTPView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = OTPLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']

            try:
                delivery_boy = DeliveryBoy.objects.get(email=email)
            except DeliveryBoy.DoesNotExist:
                return Response({"message": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)

            if not delivery_boy.is_otp_valid():
                return Response({"message": "OTP is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            if delivery_boy.otp != otp:
                return Response({"message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": "Login successful!",
                "delivery_boy_id": delivery_boy.id,
                "email": delivery_boy.email,
                "name": delivery_boy.name  # if you have a 'name' field
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DeliveryBoyDetailViewUser(generics.RetrieveUpdateDestroyAPIView):
    queryset = DeliveryBoy.objects.all()
    serializer_class = DeliveryBoySerializer
    permission_classes = []

    def get_object(self):
        delivery_boy_id = self.kwargs.get('delivery_boy_id')
        return DeliveryBoy.objects.get(id=delivery_boy_id)
    
# View for creating an order assignment
class OrderAssignCreateView(generics.CreateAPIView):
    queryset = OrderAssign.objects.all()
    serializer_class = OrderAssignSerializer
    permission_classes = [IsAdminUser]  

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
#assigned order list
class DeliveryBoyAssignedOrdersView(generics.ListAPIView):
    serializer_class = OrderAssignSerializer

    def get_queryset(self):
        delivery_boy_id = self.kwargs['delivery_boy_id']
        return OrderAssign.objects.filter(delivery_boy_id=delivery_boy_id)
    
#order assign status-update
class OrderAssignStatusUpdateView(generics.UpdateAPIView):
    queryset = OrderAssign.objects.all()
    serializer_class = OrderAssignSerializer
    permission_classes = [IsAdminUser]  

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    

class OrderAssignStatusFilterView(generics.ListAPIView):
    serializer_class = OrderAssignSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        status = self.request.query_params.get('status')
        queryset = OrderAssign.objects.all()
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
class DeliveryBoyNotificationListView(APIView):
    permission_classes = [IsAuthenticated]  # You can customize this

    def get(self, request, delivery_boy_id):
        try:
            delivery_boy = DeliveryBoy.objects.get(id=delivery_boy_id)
        except DeliveryBoy.DoesNotExist:
            return Response({'error': 'Delivery boy not found'}, status=status.HTTP_404_NOT_FOUND)

        notifications = DeliveryNotification.objects.filter(delivery_boy=delivery_boy).order_by('-created_at')
        serializer = DeliveryNotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class MarkNotificationAsReadView(generics.UpdateAPIView):
    queryset = DeliveryNotification.objects.all()
    serializer_class = DeliveryNotificationSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        try:
            notification = self.get_object()
            notification.is_read = True
            notification.save()
            return Response({'message': 'Marked as read'}, status=status.HTTP_200_OK)
        except DeliveryNotification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

from django.shortcuts import get_object_or_404
class AcceptOrderView(generics.UpdateAPIView):
    def update(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        delivery_boy_id = kwargs.get('delivery_boy_id')

        try:
            order_assignment = OrderAssign.objects.get(order__id=order_id, delivery_boy_id=delivery_boy_id)
        except OrderAssign.DoesNotExist:
            return Response({"detail": "No OrderAssign matches the given query."}, status=status.HTTP_404_NOT_FOUND)

        if OrderAssign.objects.filter(order__id=order_id, is_accepted=True).exists():
            return Response({"detail": "This order has already been accepted by another delivery boy."}, status=status.HTTP_400_BAD_REQUEST)

        order_assignment.is_accepted = True
        order_assignment.accepted_by_id = delivery_boy_id
        order_assignment.status = 'PICKED'
        order_assignment.save()

        delivery_boy = DeliveryBoy.objects.get(id=delivery_boy_id)

        return Response({
            "message": "Order accepted successfully.",
            "delivery_boy_id": delivery_boy.id,
            "delivery_boy_name": delivery_boy.name
        }, status=status.HTTP_200_OK)

class AcceptedOrdersListView(generics.ListAPIView):
    serializer_class = AcceptedOrderSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return OrderAssign.objects.filter(is_accepted=True).select_related('order', 'accepted_by')

class AcceptedOrdersByVendorListView(generics.ListAPIView):
    serializer_class = AcceptedOrderSerializer
    authentication_classes = [VendorJWTAuthentication]
    def get_queryset(self):
        delivery_boy_id = self.kwargs.get('delivery_boy_id')  

        orders = OrderAssign.objects.filter(
            is_accepted=True,
            accepted_by__id=delivery_boy_id
        ).select_related('order', 'order__checkout', 'accepted_by')

        return orders

class UpdateOrderStatusView(generics.UpdateAPIView):
    queryset = OrderAssign.objects.all()
    serializer_class = OrderAssignStatusUpdateSerializer
    permission_classes = []

    def update(self, request, *args, **kwargs):
        delivery_boy_id = kwargs.get('delivery_boy_id')
        order_id = kwargs.get('order_id')
        new_status = request.data.get('status')

        try:
            order_assign = OrderAssign.objects.get(
                order__id=order_id,
                accepted_by__id=delivery_boy_id,
                is_accepted=True
            )
        except OrderAssign.DoesNotExist:
            return Response({"detail": "Assigned order not found or not accepted by this delivery boy."},
                            status=status.HTTP_404_NOT_FOUND)

        if new_status not in dict(OrderAssign._meta.get_field('status').choices):
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        order_assign.status = new_status
        order_assign.save()

        return Response({
            "message": f"Order status updated to {new_status}.",
            "delivery_boy_id": delivery_boy_id,
            "order_id": order_id
        }, status=status.HTTP_200_OK)
