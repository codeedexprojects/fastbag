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

# ---- Request OTP View ----
from rest_framework.views import APIView

class request_otp(APIView):
    permission_classes = []
    authentication_classes=[]
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

class login_with_otp(APIView):
    permission_classes = []
    authentication_classes=[]

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

            # Generate JWT tokens
            refresh = RefreshToken.for_user(delivery_boy)
            access_token = str(refresh.access_token)

            return Response({
                "message": "Login successful!",
                "access_token": access_token,
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeliveryBoyDetailViewUser(generics.RetrieveUpdateDestroyAPIView):
    queryset = DeliveryBoy.objects.all()
    serializer_class = DeliveryBoySerializer
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)