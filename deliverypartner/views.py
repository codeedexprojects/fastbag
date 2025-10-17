from .models import DeliveryBoy
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
import random
from django.conf import settings
from datetime import timedelta
from rest_framework import status
from rest_framework.response import Response
from vendors.authentication import VendorJWTAuthentication
from rest_framework.views import APIView
from users.utils import send_otp_2factor
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from deliverypartner.models import OrderAssign, DeliveryBoy
from cart.models import Order
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


# ---- Request OTP View ----
class RequestOTPView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data['mobile_number']

            try:
                delivery_boy = DeliveryBoy.objects.get(mobile_number=mobile_number)
            except DeliveryBoy.DoesNotExist:
                return Response({"message": "No account found with this mobile number."},
                                status=status.HTTP_404_NOT_FOUND)

            otp = str(random.randint(100000, 999999))
            delivery_boy.otp = otp
            delivery_boy.otp_created_at = timezone.now()
            delivery_boy.save()

            try:
                send_otp_2factor(mobile_number, otp)
            except Exception as e:
                return Response({"message": f"Failed to send OTP: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ---- Login with OTP View ----

class LoginWithOTPView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = OTPLoginSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data['mobile_number']
            otp = serializer.validated_data['otp']

            try:
                delivery_boy = DeliveryBoy.objects.get(mobile_number=mobile_number)
            except DeliveryBoy.DoesNotExist:
                return Response({"message": "No account found with this mobile number."},
                                status=status.HTTP_404_NOT_FOUND)

            if delivery_boy.otp != otp:
                return Response({"message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

            delivery_boy.otp = None
            delivery_boy.otp_created_at = None
            delivery_boy.save()

            return Response({
                "message": "Login successful!",
                "delivery_boy_id": delivery_boy.id,
                "mobile_number": delivery_boy.mobile_number,
                "name": delivery_boy.name
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
    permission_classes= []

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
    permission_classes = []  

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


class AcceptOrderView(generics.UpdateAPIView):
    authentication_classes = []
    permission_classes = []

    def update(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        delivery_boy_id = kwargs.get('delivery_boy_id')


        order = get_object_or_404(Order, id=order_id)


        if OrderAssign.objects.filter(order=order, is_accepted=True).exists():
            return Response({"detail": "This order has already been accepted by another delivery boy."},
                            status=status.HTTP_400_BAD_REQUEST)


        delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id)


        order.order_status = 'Picked'
        order.save()


        order_assign = OrderAssign.objects.create(
            order=order,
            delivery_boy=delivery_boy,
            is_accepted=True,
            accepted_by=delivery_boy,
            status='PICKED',
            assigned_at=timezone.now()
        )

        return Response({
            "message": "Order accepted successfully.",
            "order_id": order.id,
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

class DeliveryBoyOrderListView(generics.ListAPIView):
    serializer_class = DeliveryNotificationSerializer
    permission_classes = []  

    def get_queryset(self):
        delivery_boy_id = self.kwargs['delivery_boy_id']
        return DeliveryNotification.objects.filter(delivery_boy_id=delivery_boy_id).select_related('order')
    
class AcceptedOrderListView(generics.ListAPIView):
    serializer_class = AcceptedOrderSerializer
    permission_classes = []

    def get_queryset(self):
        delivery_boy_id = self.kwargs.get('delivery_boy_id')
        return OrderAssign.objects.filter(
            is_accepted=True,
            accepted_by_id=delivery_boy_id
        ).select_related('order', 'accepted_by', 'order__checkout', 'order__user')
    
class RejecteddOrderListView(generics.ListAPIView):
    serializer_class = AcceptedOrderSerializer 
    permission_classes = []

    def get_queryset(self):
        delivery_boy_id = self.kwargs.get('delivery_boy_id')
        return OrderAssign.objects.filter(
            is_rejected=True,
            delivery_boy_id=delivery_boy_id
        ).select_related('order', 'delivery_boy', 'order__checkout', 'order__user')


class RejectOrderView(generics.UpdateAPIView):
    permission_classes = []

    def update(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        delivery_boy_id = kwargs.get('delivery_boy_id')

        order = get_object_or_404(Order, id=order_id)
        delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id)

        order_assignment = (
            OrderAssign.objects.filter(order=order, delivery_boy=delivery_boy)
            .order_by('-assigned_at')
            .first()
        )

        if not order_assignment:
            order_assignment = OrderAssign.objects.create(
                order=order,
                delivery_boy=delivery_boy,
                assigned_at=timezone.now(),
                status='REJECTED',
                is_rejected=True
            )
        else:
            if order_assignment.is_accepted:
                return Response(
                    {"detail": "This order is already accepted and cannot be rejected."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if order_assignment.is_rejected:
                return Response(
                    {"detail": "This order is already marked as rejected by this delivery boy."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order_assignment.is_rejected = True
            order_assignment.status = 'REJECTED'
            order_assignment.save()

        return Response({
            "message": "Order rejected successfully.",
            "order_id": order.id,
            "delivery_boy_id": delivery_boy.id,
            "delivery_boy_name": delivery_boy.name,
            "status": order_assignment.status
        }, status=status.HTTP_200_OK)
    
