from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from users.serializers import *
from users.utils import send_otp_2factor
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from users.models import Address
from users.serializers import AddressSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated,IsAdminUser
import random
# Create your views here.

class AdminLoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile_number = serializer.validated_data['mobile_number']
        password = serializer.validated_data['password']

        user = authenticate(request, mobile_number=mobile_number, password=password)

        if user is not None and user.is_staff:
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Successfully authenticated as admin.',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user_id': user.id,
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials or permission denied.'}, status=status.HTTP_401_UNAUTHORIZED)
   
#8075189800
#admin123

# from rest_framework.decorators import api_view,permission_classes

# @api_view(['POST'])
# @permission_classes([])
# def create_superuser_view(request):
    
#     if request.method == 'POST':
#         # Initialize the serializer with the data from the request
#         serializer = SuperuserSerializer(data=request.data)
        
#         if serializer.is_valid():
#             # Create the superuser
#             serializer.save()
#             return Response({'message': 'Superuser created successfully!'}, status=status.HTTP_201_CREATED)
        
#         # If validation fails, return the errors
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffLoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = StaffLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile_number = serializer.validated_data['mobile_number']
        password = serializer.validated_data['password']

        user = authenticate(request, mobile_number=mobile_number, password=password)

        if user is None:
            return Response({'detail': 'Invalid mobile number or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_staff:
            return Response({'detail': 'User does not have staff privileges.'}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)

        permissions = []
        if hasattr(user, 'permissions'):
            permissions = user.permissions if isinstance(user.permissions, list) else list(user.permissions)

        return Response({
            'message': 'Staff login successful.',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user_id': user.id,
            'mobile_number': user.mobile_number,
            'permissions': permissions
        }, status=status.HTTP_200_OK)

class RegisterView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data['mobile_number']
            otp = str(random.randint(100000, 999999))

            try:
                send_otp_2factor(mobile_number, otp)
                
                user, created = CustomUser.objects.update_or_create(
                    mobile_number=mobile_number,
                    defaults={'otp': otp}
                )

                if created:
                    UserRegNotification.objects.create(
                        user=user,
                        notification_type='registration',
                        message=f"New user registered with mobile: {mobile_number}"
                    )

                return Response({
                    "message": "OTP sent successfully",
                    "mobile_number": mobile_number,
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"message": f"Failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data['mobile_number']
            otp = serializer.validated_data['otp']

            try:
                user = CustomUser.objects.get(mobile_number=mobile_number)

                if user.otp == otp:
                    user.is_verified = True

                    user.otp = None  
                    user.save()

                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)

                    return Response({
                        "message": "Login successful",
                        "user": {
                            "mobile_number": user.mobile_number,
                            "name": user.name,
                            "is_verified": user.is_verified,
                            "user_id": user.id
                        },
                        "access_token": access_token,
                        # "refresh_token": str(refresh),
                    })

                else:
                    return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

            except CustomUser.DoesNotExist:
                return Response({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = OutstandingToken.objects.get(token=request.auth.token)
            BlacklistedToken.objects.create(token=token)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 
    
class AddressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  
        addresses = user.addresses.all()
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        return Address.objects.filter(user=self.request.user)

class UserUpdateView(APIView):
    
    def get(self, request):
        serializer = UserUpdateSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        # Pass the request context to the serializer to access 'request'
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "User details updated successfully",
                "user": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(generics.RetrieveDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserDetailSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return CustomUser.objects.all()
    
class UserListView(generics.ListAPIView):
    
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserListSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None
    def get_queryset(self):
        return CustomUser.objects.filter(is_staff=False, is_superuser=False)
    
class UserInfo(generics.RetrieveDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.all()
    
from django.shortcuts import get_object_or_404
class SetPrimaryAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, address_id):
        user = request.user
        address = get_object_or_404(Address, id=address_id, user=user)

        Address.objects.filter(user=user, is_primary=True).update(is_primary=False)
        address.is_primary = True
        address.save()
        return Response({'detail': 'Primary address set successfully.'}, status=status.HTTP_200_OK)


class UserLocationCreateView(generics.CreateAPIView):
    permission_classes=[]
    queryset = UserLocation.objects.all()
    serializer_class = UserLocationSerializer

class UserLocationUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes=[]
    queryset = UserLocation.objects.all()
    serializer_class = UserLocationSerializer
    lookup_field = 'pk'