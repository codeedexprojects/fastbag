from django.shortcuts import render
from rest_framework import generics ,status ,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser
from django.core.mail import send_mail
import random
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from users.permissions import IsAdminOrSuperuser
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.authentication import JWTAuthentication
from users.permissions import IsVendor
from rest_framework.permissions import BasePermission
from vendors.models import Vendor
from vendors.authentication import VendorJWTAuthentication
from groceryproducts.serializers import GroceryProductSerializer
from foodproduct.serializers import DishCreateSerializer
from fashion.serializers import ClothingSerializer
from groceryproducts.models import GroceryProducts
from fashion.models import Clothing
from foodproduct.models import Dish
from rest_framework.exceptions import PermissionDenied
from vendors.pagination import CustomPageNumberPagination
from rest_framework import generics, filters
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal,InvalidOperation
from geopy.distance import distance as geopy_distance
from geopy.distance import geodesic

class IsVendor(BasePermission):
    """
    Custom permission class to check if the authenticated user is a vendor.
    """

    def has_permission(self, request, view):
        user = request.user
        # Check if the user is authenticated and is an instance of Vendor
        if user and user.is_authenticated:
            return isinstance(user, Vendor)
        return False


#for creating and displaying stores
class StoreTypeListCreateView(generics.ListCreateAPIView):
    pagination_class = None
    permission_classes = [IsAuthenticated,IsAdminUser]
    queryset = StoreType.objects.all().order_by('-created_at')
    serializer_class = StoreTypeSerializer
    

class StoreTypeListView(generics.ListAPIView):
    permission_classes = []
    queryset = StoreType.objects.all().order_by('-created_at')
    serializer_class = StoreTypeSerializer

class StoreDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = StoreType.objects.all()
    serializer_class = StoreTypeSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"message": "Store details retrieved successfully.", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"message": "Store details updated successfully.", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Store deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

# for creating and displaying vendors
class VendorListCreateView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]  # Add parsers for file handling
    
    def post(self, request, *args, **kwargs):
        data = request.data

        # Convert '10:00 PM' to 24-hour format
        if 'opening_time' in data:
            try:
                data['opening_time'] = datetime.strptime(data['opening_time'], '%I:%M %p').time()
            except ValueError:
                return Response({"error": "Invalid time format for opening_time"}, status=400)
        
        if 'closing_time' in data:
            try:
                data['closing_time'] = datetime.strptime(data['closing_time'], '%I:%M %p').time()
            except ValueError:
                return Response({"error": "Invalid time format for closing_time"}, status=400)

        # Pass both data and files to the serializer
        serializer = VendorCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            vendor = serializer.save()

            if 'store_logo' in request.FILES:
                vendor.store_logo = request.FILES['store_logo']
            if 'fssai_certificate' in request.FILES:
                vendor.fssai_certificate = request.FILES['fssai_certificate']
            if 'display_image' in request.FILES:
                vendor.display_image = request.FILES['display_image']
            if 'license' in request.FILES:
                vendor.license = request.FILES['license']

            vendor.save()

            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

class VendorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Vendor.objects.all()
    serializer_class = VendorHomePageSerializer
    pagination_class = CustomPageNumberPagination

    def get_serializer_context(self):
        return {'request': self.request}


class VendorListViewAdmin(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Vendor.objects.all()
    serializer_class = VendorCreateSerializer
    pagination_class = None

class VendorDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [VendorJWTAuthentication]
    permission_classes = [IsAuthenticated,IsVendor]
    # queryset = Vendor.objects.all().order_by('-created_at')
    serializer_class = VendorDetailSerializer
    def get_queryset(self):
            return Vendor.objects.filter(id=self.request.user.id).order_by('-created_at')

class VendorPendingDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = VendorPendingDetailSerializer
    def get_queryset(self):
        return Vendor.objects.all()

    def get_object(self):
        vendor_id = self.kwargs.get("pk")
        try:
            return Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Vendor not found.")

class VendorDetailViewAdmin(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = VendorDetailSerializer
    pagination_class = None

    def get_queryset(self):
        return Vendor.objects.all()

    def get_object(self):
        vendor_id = self.kwargs.get("pk")
        try:
            return Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Vendor not found.")

 
#for accept - reject stores
class VendorAdminAcceptReject(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    queryset = Vendor.objects.all()
    serializer_class = VendorDetailSerializer

    def update(self, request, *args, **kwargs):
        vendor = self.get_object()
        approval_status = request.data.get('is_approved', None)   
        if approval_status is not None:
            if approval_status not in [True, False]:
                return Response({'error': 'Invalid status. Must be a boolean (True/False).'}, status=status.HTTP_400_BAD_REQUEST)
            vendor.is_approved = approval_status
            vendor.save()
            if approval_status:
                return Response({'status': 'Vendor registration approved.'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'Vendor registration rejected.'}, status=status.HTTP_200_OK)
        return Response({'error': 'Missing approval status.'}, status=status.HTTP_400_BAD_REQUEST)

#for enable or disable vendors-Admin
class VendorEnableDisableView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Vendor.objects.all()
    serializer_class = VendorDetailSerializer

    def update(self, request, *args, **kwargs):
        vendor = self.get_object()
        enable_status = request.data.get('is_active')  # Handle the `is_active` field
        if isinstance(enable_status, str):
            enable_status = enable_status.lower() in ["true", "1"]
        if enable_status not in [True, False]:
            return Response({'error': 'Invalid status. Must be a boolean (True/False).'}, status=status.HTTP_400_BAD_REQUEST)
        vendor.is_active = enable_status
        vendor.save()
        message = 'Vendor status enabled.' if enable_status else 'Vendor status disabled.'
        return Response({'status': message}, status=status.HTTP_200_OK)

#favourite vendor
class VendorFavouriteView(generics.UpdateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorDetailSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        vendor = self.get_object()
        favourite = request.data.get('is_favourite')
        
        if isinstance(favourite, str):
            favourite = favourite.lower() in ["true", "1"]
        
        if favourite not in [True, False]:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        if favourite:
            user.favourite_vendors.add(vendor)
            message = 'Vendor added to favourite'
        else:
            user.favourite_vendors.remove(vendor)
            message = 'Vendor removed from favourite'
        
        return Response({'status': message, 'vendor_id': vendor.id}, status=status.HTTP_200_OK)

class UserFavouriteVendorsView(generics.ListAPIView):
    serializer_class = VendorfavSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        return self.request.user.favourite_vendors.all() 
            

#for filtering rejected and accepted vendors
class VendorFilterListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Vendor.objects.all()
    serializer_class = VendorDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)  

        if status:
            queryset = queryset.filter(is_approved=status)
        
        return queryset
    
#for viewing vendor by store category 
class StoresByTypeView(generics.ListAPIView):
    serializer_class = VendorNameSerializer
    permission_classes=[]

    def get_queryset(self):
        store_type_id = self.kwargs.get('store_type_id')
        return Vendor.objects.filter(store_type_id=store_type_id, is_approved='True')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
# class VendorByCategoryListView(generics.ListAPIView):
#     serializer_class = VendorSerializer

#     def get_queryset(self):
#         category_name = self.kwargs.get('category_name')  
#         return Vendor.objects.filter(category__name=category_name)

def generate_and_send_otp(vendor_admin):
    otp = f"{random.randint(1000, 9999)}"
    vendor_admin.otp = otp
    vendor_admin.save()
    
    # Send OTP to the delivery boy's email
    send_mail(
        'Your Login OTP',
        f'Your OTP for login is {otp}.',
        'noreply@yourapp.com',  
        [vendor_admin.email],
        fail_silently=False,
    )

class VendorLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VendorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            vendor_admin = Vendor.objects.get(email=email)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)

        if not vendor_admin.is_approved:
            return Response({"error": "Your account has not been approved yet. Please contact support."}, 
                            status=status.HTTP_403_FORBIDDEN)

        generate_and_send_otp(vendor_admin)
        return Response({"message": "OTP sent to email","otp":vendor_admin.otp}, status=status.HTTP_200_OK)

class VendorOTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VendorOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            vendor_admin = Vendor.objects.get(email=email, otp=otp)
        except Vendor.DoesNotExist:
            return Response({"error": "Invalid OTP or email"}, status=status.HTTP_400_BAD_REQUEST)

        vendor_admin.otp = None
        vendor_admin.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(vendor_admin)  
        refresh["user_id"] = vendor_admin.id
        store = StoreType.objects.filter(vendor=vendor_admin).first()
        return Response({
            "message": "Login successful",
            "Vendor-Admin": vendor_admin.id,
            "store":store.name,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "is_approved": vendor_admin.is_approved
        }, status=status.HTTP_200_OK)


from rest_framework_simplejwt.views import TokenRefreshView
class VendorTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
class VendorApprovalStatusView(APIView):
    permission_classes = []  
    def get(self, request, id):
        try:
            vendor = Vendor.objects.get(id=id)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = VendorApprovalStatusSerializer(vendor)
        return Response(serializer.data, status=status.HTTP_200_OK)


def send_otp_to_email(email, otp):
    subject = "Your OTP for Login"
    message = f"Your OTP is {otp}. It is valid for 10 minutes."
    from_email = "noreply@yourdomain.com"
    send_mail(subject, message, from_email, [email])


from django.utils.timezone import now, timedelta
class ForgotEmailSendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        alternate_email = request.data.get('alternate_email')

        if not alternate_email:
            return Response({"error": "Alternate email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vendor = Vendor.objects.get(alternate_email=alternate_email)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor with this alternate email not found."}, status=status.HTTP_404_NOT_FOUND)

        # Generate OTP
        otp = str(random.randint(1000, 9999))
        vendor.otp = otp
        vendor.otp_expiry = now() + timedelta(minutes=10)
        vendor.save()

        # Send OTP (replace with actual email service)
        send_otp_to_email(alternate_email, otp)

        return Response({"message": "OTP sent to alternate email."}, status=status.HTTP_200_OK)

class ForgotEmailVerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        alternate_email = request.data.get('alternate_email')
        otp = request.data.get('otp')

        if not alternate_email or not otp:
            return Response({"error": "Both alternate email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vendor = Vendor.objects.get(alternate_email=alternate_email)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor with this alternate email not found."}, status=status.HTTP_404_NOT_FOUND)


        if vendor.otp != otp or now() > vendor.otp_expiry:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        vendor.otp = None
        vendor.otp_expiry = None
        vendor.save()

        user = authenticate(request, username=vendor.email)  

        if not user:
            return Response({"error": "Authentication failed."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "OTP verified successfully. Logged in.",
            "id": user.id, 
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class=CustomPageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend
class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    pagination_class = None

    def get_queryset(self):
        queryset = Category.objects.all()
        store_type_name = self.request.query_params.get('store_type_name')
        name = self.request.query_params.get('name')

        if store_type_name:
            queryset = queryset.filter(store_type__name__iexact=store_type_name)
        
        if name:
            queryset = queryset.filter(name__icontains=name)  # partial match, case-insensitive

        return queryset

    
class ApproveVendorUpdateView(APIView):
    def post(self, request, pk, *args, **kwargs):
        try:
            vendor = Vendor.objects.get(pk=pk)

            vendor.contact_number = vendor.pending_contact_number or vendor.contact_number
            vendor.fssai_certificate = vendor.pending_fssai_certificate or vendor.fssai_certificate
            vendor.license = vendor.pending_license or vendor.license

            vendor.pending_contact_number = None
            vendor.pending_fssai_certificate = None
            vendor.pending_license = None
            vendor.is_pending_update_approval = False
            vendor.save()

            return Response(
                {"message": "Vendor updates approved successfully."},
                status=status.HTTP_200_OK
            )
        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class SubCategoryListView(APIView):
    def get(self, request):
        clothing_subcategories = ClothingSubCategory.objects.filter(is_active=True)
        grocery_subcategories = GrocerySubCategories.objects.filter(enable_subcategory=True)
        food_subcategories = FoodSubCategories.objects.filter(enable_subcategory=True)

        clothing_serializer = ClothingSubCategorySerializerlist(clothing_subcategories, many=True, context={'request': request})
        grocery_serializer = GrocerySubCategorySerializerlist(grocery_subcategories, many=True, context={'request': request})
        food_serializer = FoodSubCategorySerializerlist(food_subcategories, many=True, context={'request': request})

        data = {
            "clothing_subcategories": clothing_serializer.data,
            "grocery_subcategories": grocery_serializer.data,
            "food_subcategories": food_serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)

class VendorProductListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = CustomPageNumberPagination

    def get_paginated_response(self, queryset, request, serializer_class):
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        if paginated_queryset is not None:
            return paginator.get_paginated_response(serializer_class(paginated_queryset, many=True, context={'request': request}).data)
        return Response(serializer_class(queryset, many=True, context={'request': request}).data)

    def get(self, request, vendor_id):
        if Clothing.objects.filter(vendor_id=vendor_id).exists():
            clothing_products = Clothing.objects.filter(
                vendor_id=vendor_id,
                is_active=True,
                subcategory__is_active=True  
            )
            return self.get_paginated_response(clothing_products, request, ClothingSerializer)

        # Check for vendor in Dish
        elif Dish.objects.filter(vendor_id=vendor_id).exists():
            dish_products = Dish.objects.filter(
                vendor_id=vendor_id,
                is_available=True,
                subcategory__is_active=True  
            )
            return self.get_paginated_response(dish_products, request, DishCreateSerializer)

        # Check for vendor in Grocery
        elif GroceryProducts.objects.filter(vendor_id=vendor_id).exists():
            grocery_products = GroceryProducts.objects.filter(
                vendor_id=vendor_id,
                is_available=True,
                subcategory__is_active=True  
            )
            return self.get_paginated_response(grocery_products, request, GroceryProductSerializer)

        # If no match found
        return Response(
            {"detail": "No products found for the given vendor ID."},
            status=status.HTTP_404_NOT_FOUND
        )
    
class ProductCreateAPIView(APIView):
    permission_classes= [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save()
            return Response({"message": "Product created successfully!", "product_id": product.id}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorProductsCountView(APIView):
    authentication_classes = [VendorJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, vendor_id):
        authenticated_vendor = request.user  
        
        
        if authenticated_vendor.id != vendor_id:
            raise PermissionDenied("You are not authorized to access this vendor's data.")

        vendor = authenticated_vendor  

        
        vendor_type = None
        product_count = 0

        if GroceryProducts.objects.filter(vendor=vendor).exists():
            vendor_type = "Grocery"
            product_count = GroceryProducts.objects.filter(vendor=vendor).count()
        elif Clothing.objects.filter(vendor=vendor).exists():
            vendor_type = "Clothing"
            product_count = Clothing.objects.filter(vendor=vendor).count()
        elif Dish.objects.filter(vendor=vendor).exists():
            vendor_type = "Dishes"
            product_count = Dish.objects.filter(vendor=vendor).count()

        if vendor_type:
            return Response({"vendor_type": vendor_type, "product_count": product_count})
        
        return Response({"error": "Vendor type not found"}, status=404)
    

class VendorAvailableProductsCountView(APIView):
    authentication_classes = [VendorJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, vendor_id):
        authenticated_vendor = request.user  # Vendor from token

        # Ensure the token's vendor ID matches the requested vendor_id
        if authenticated_vendor.id != vendor_id:
            raise PermissionDenied("You are not authorized to access this vendor's data.")

        vendor = authenticated_vendor  # Vendor is already fetched from token

        # Get counts of available products per category
        grocery_count = GroceryProducts.objects.filter(vendor=vendor, is_available=True).count()
        clothing_count = Clothing.objects.filter(vendor=vendor, is_available=True).count()
        dishes_count = Dish.objects.filter(vendor=vendor, is_available=True).count()

        total_count = grocery_count + clothing_count + dishes_count

        return Response({
            "vendor_id":vendor.id,
            "available_product_count": total_count
        })


def get_vendor_out_of_stock_counts(vendor_id):
    try:
        vendor = Vendor.objects.get(id=vendor_id)
    except Vendor.DoesNotExist:
        return {
            'error': 'Vendor not found'
        }
    
    # Initialize counts
    counts = {
        'clothing': 0,
        'grocery': 0,
        'food': 0,
        'total': 0
    }
    
    clothing_items = Clothing.objects.filter(vendor=vendor, is_active=True)
    for item in clothing_items:
        all_variants_out_of_stock = True
        
        for color in item.colors:
            for size in color.get('sizes', []):
                if size.get('stock', 0) > 0:
                    all_variants_out_of_stock = False
                    break
            if not all_variants_out_of_stock:
                break
                
        if all_variants_out_of_stock:
            counts['clothing'] += 1
    
    grocery_items = GroceryProducts.objects.filter(vendor=vendor, is_available=True)
    for item in grocery_items:
        all_weights_out_of_stock = True
        
        if isinstance(item.weights, dict):
            for weight_data in item.weights.values():
                if weight_data.get('is_in_stock', False):
                    all_weights_out_of_stock = False
                    break
        elif isinstance(item.weights, list):
            for weight_data in item.weights:
                if weight_data.get('is_in_stock', False):
                    all_weights_out_of_stock = False
                    break
                 
        if all_weights_out_of_stock:
            counts['grocery'] += 1
    
    # Count out-of-stock food dishes
    dish_items = Dish.objects.filter(vendor=vendor, is_available=True)
    for item in dish_items:
        all_variants_out_of_stock = True
        
        if isinstance(item.variants, dict):
            # Dictionary format
            for variant_data in item.variants.values():
                if variant_data.get('is_in_stock', False):
                    all_variants_out_of_stock = False
                    break
        elif isinstance(item.variants, list):
            # List format
            for variant_data in item.variants:
                if variant_data.get('is_in_stock', False):
                    all_variants_out_of_stock = False
                    break
                
        if all_variants_out_of_stock:
            counts['food'] += 1
    
    # Calculate total
    counts['total'] = counts['clothing'] + counts['grocery'] + counts['food']
    
    return counts

class VendorOutOfStockDetailView(APIView):
    authentication_classes = [VendorJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, vendor_id):
        authenticated_vendor = request.user
        
        if not (authenticated_vendor.id == vendor_id or authenticated_vendor.is_staff):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this vendor\'s data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Vendor not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        vendor_types = []
        if Dish.objects.filter(vendor=vendor).exists():
            vendor_types.append('food')
        if Clothing.objects.filter(vendor=vendor).exists():
            vendor_types.append('clothing')
        if GroceryProducts.objects.filter(vendor=vendor).exists():
            vendor_types.append('grocery')
        
        counts = get_vendor_out_of_stock_counts(vendor.id)
        
        filtered_counts = {
            product_type: count 
            for product_type, count in counts.items() 
            if product_type in vendor_types or product_type == 'total'
        }
        
        return Response({
            'status': 'success',
            'data': {
                'vendor_name': vendor.business_name,
                'vendor_id': vendor.id,
                'vendor_types': vendor_types,
                'out_of_stock_counts': filtered_counts
            }
        }, status=status.HTTP_200_OK)
    
class VendorAnalyticsView(APIView):
    authentication_classes = [VendorJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_vendor_out_of_stock_counts(self, vendor):
        counts = {
            'clothing': 0,
            'grocery': 0,
            'food': 0,
            'total': 0
        }

        # Clothing out-of-stock count
        clothing_items = Clothing.objects.filter(vendor=vendor, is_active=True)
        for item in clothing_items:
            all_variants_out_of_stock = all(
                all(size.get('stock', 0) == 0 for size in color.get('sizes', []))
                for color in item.colors
            )
            if all_variants_out_of_stock:
                counts['clothing'] += 1

        # Grocery out-of-stock count
        grocery_items = GroceryProducts.objects.filter(vendor=vendor, is_available=True)
        for item in grocery_items:
            all_weights_out_of_stock = all(
                weight_data.get('is_in_stock', False) is False
                for weight_data in (item.weights if isinstance(item.weights, list) else item.weights.values())
            )
            if all_weights_out_of_stock:
                counts['grocery'] += 1

        # Dish out-of-stock count
        dish_items = Dish.objects.filter(vendor=vendor, is_available=True)
        for item in dish_items:
            all_variants_out_of_stock = all(
                variant_data.get('is_in_stock', False) is False
                for variant_data in (item.variants if isinstance(item.variants, list) else item.variants.values())
            )
            if all_variants_out_of_stock:
                counts['food'] += 1

        # Total out-of-stock count
        counts['total'] = counts['clothing'] + counts['grocery'] + counts['food']
        return counts

    def get(self, request, vendor_id):
        authenticated_vendor = request.user

        if authenticated_vendor.id != vendor_id:
            raise PermissionDenied("You are not authorized to access this vendor's data.")

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)

        # Determine vendor type(s)
        vendor_types = []
        if Dish.objects.filter(vendor=vendor).exists():
            vendor_types.append('food')
        if Clothing.objects.filter(vendor=vendor).exists():
            vendor_types.append('clothing')
        if GroceryProducts.objects.filter(vendor=vendor).exists():
            vendor_types.append('grocery')

        # Get total product count
        total_product_count = (
            GroceryProducts.objects.filter(vendor=vendor).count() +
            Clothing.objects.filter(vendor=vendor).count() +
            Dish.objects.filter(vendor=vendor).count()
        )

        # Get available product count
        available_product_count = (
            GroceryProducts.objects.filter(vendor=vendor, is_available=True).count() +
            Clothing.objects.filter(vendor=vendor, is_available=True).count() +
            Dish.objects.filter(vendor=vendor, is_available=True).count()
        )

        # Get out-of-stock product counts
        out_of_stock_counts = self.get_vendor_out_of_stock_counts(vendor)

        return Response({
            "vendor_id": vendor.id,
            "vendor_name": vendor.business_name,
            "vendor_types": vendor_types,
            "total_product_count": total_product_count,
            "available_product_count": available_product_count,
            "out_of_stock_counts": out_of_stock_counts
        }, status=status.HTTP_200_OK)

class CategorySearchAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'store_type__name']
    permission_classes=[AllowAny]


class SubCategoryListView(generics.ListAPIView):
    queryset = SubCategory.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = SubCategorySerializer
    pagination_class = None

# Create subcategory (admin only)
class SubCategoryCreateView(generics.CreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsAdminUser]

# Update/Delete subcategory (admin only)
class SubCategoryUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [IsAdminUser]

#subcategories request
class SubCategoryRequestCreateView(generics.CreateAPIView):
    queryset = SubCategoryRequest.objects.all()
    serializer_class = SubCategoryRequestSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [VendorJWTAuthentication]

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)

class SubCategoryRequestListView(generics.ListAPIView):
    serializer_class = SubCategoryRequestSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SubCategoryRequest.objects.all().order_by('-created_at')


class VendorSubCategoryRequestListView(generics.ListAPIView):
    serializer_class = SubCategoryRequestSerializer
    authentication_classes = [VendorJWTAuthentication]

    def get_queryset(self):
        return SubCategoryRequest.objects.filter(vendor=self.request.user).order_by('-created_at')

class ApproveSubCategoryRequestView(APIView):
    permission_classes = [IsAdminUser]  

    def post(self, request, request_id):
        try:
            subcategory_request = SubCategoryRequest.objects.get(id=request_id)

            action = request.data.get("action")  

            if action == "approve":
                SubCategory.objects.create(
                    category=subcategory_request.category,
                    name=subcategory_request.name,
                    sub_category_image=subcategory_request.sub_category_image
                )
                subcategory_request.is_approved = True
                subcategory_request.save()
                return Response({"message": "SubCategory approved and created."}, status=status.HTTP_200_OK)

            elif action == "reject":
                subcategory_request.is_approved = False
                subcategory_request.save()
                return Response({"message": "SubCategory request rejected."}, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        except SubCategoryRequest.DoesNotExist:
            return Response({"error": "SubCategoryRequest not found."}, status=status.HTTP_404_NOT_FOUND)



class SubCategoryListByCategory(generics.ListAPIView):
    serializer_class = SubCategorySerializer
    pagination_class = CustomPageNumberPagination
    authentication_classes = [VendorJWTAuthentication]

    def get_queryset(self):
        category_id = self.kwargs['category_id']

        
        if not Category.objects.filter(id=category_id).exists():
            raise PermissionDenied("Category does not exist.")

        
        return SubCategory.objects.filter(
            category_id=category_id,
        )
    
class VendorSearchView(generics.ListAPIView):
    queryset = Vendor.objects.filter(is_active=True, is_approved=True)
    serializer_class = VendorSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['business_name', 'owner_name', 'city', 'store_id', 'business_location']

class NearbyVendorsAPIView(generics.ListAPIView):
    serializer_class = VendorDetailSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = []

    def get_queryset(self):
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')

        if not latitude or not longitude:
            return Vendor.objects.none()  

        try:
            user_lat = Decimal(latitude)
            user_long = Decimal(longitude)
        except InvalidOperation:
            return Vendor.objects.none()

        user_location = (user_lat, user_long)

        nearby_vendors = []
        for vendor in Vendor.objects.filter(latitude__isnull=False, longitude__isnull=False, is_approved=True):
            vendor_location = (vendor.latitude, vendor.longitude)
            dist = geopy_distance(user_location, vendor_location).km
            if dist <= 20:
                nearby_vendors.append(vendor.id)

        return Vendor.objects.filter(id__in=nearby_vendors)

    def list(self, request, *args, **kwargs):
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')

        if not latitude or not longitude:
            return Response(
                {"error": "Both latitude and longitude query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            Decimal(latitude)
            Decimal(longitude)
        except InvalidOperation:
            return Response(
                {"error": "Invalid latitude or longitude values."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().list(request, *args, **kwargs)
    

class NearbyVendorCategoriesOnlyAPIView(generics.ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')

        if not latitude or not longitude:
            return Category.objects.none()

        user_location = (float(latitude), float(longitude))

        nearby_vendors = []
        for vendor in Vendor.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            vendor_location = (float(vendor.latitude), float(vendor.longitude))
            distance_km = geodesic(user_location, vendor_location).km
            if distance_km <= 10:
                nearby_vendors.append(vendor.id)

        grocery_cats = GroceryProducts.objects.filter(vendor_id__in=nearby_vendors).values_list('category_id', flat=True)
        dish_cats = Dish.objects.filter(vendor_id__in=nearby_vendors).values_list('category_id', flat=True)
        clothing_cats = Clothing.objects.filter(vendor_id__in=nearby_vendors).values_list('category_id', flat=True)

        all_category_ids = set(grocery_cats) | set(dish_cats) | set(clothing_cats)

        return Category.objects.filter(id__in=all_category_ids).distinct()

    def list(self, request, *args, **kwargs):
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')

        if not latitude or not longitude:
            return Response({"error": "Latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)

            # Modify the image field manually
            for item in serializer.data:
                category = queryset.get(id=item['id'])
                item['image'] = request.build_absolute_uri(category.category_image.url) if category.category_image else None

            return self.get_paginated_response(serializer.data)

        # Fallback: no pagination
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

from cart.models import CheckoutItem,Order
class VendorOrderAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, vendor_id=None):
        vendors = Vendor.objects.filter(id=vendor_id) if vendor_id else Vendor.objects.all()
        analytics = []

        for vendor in vendors:
            items = CheckoutItem.objects.filter(vendor=vendor).select_related('checkout')
            order_ids = items.values_list('checkout_id', flat=True).distinct()
            orders = Order.objects.filter(checkout_id__in=order_ids)

            analytics.append({
                'vendor_id': vendor.id,
                'vendor_name': vendor.business_name,
                'total_orders': orders.count(),
                'pending_orders': orders.filter(order_status='pending').count(),
                'delivered_orders': orders.filter(order_status='delivered').count(),
                'cancelled_orders': orders.filter(order_status='cancelled').count(),
                # 'total_revenue': orders.aggregate(total=Sum('final_amount'))['total'] or 0.00,
                # 'paid_orders': orders.filter(payment_status='paid').count(),
                # 'online_payments': orders.filter(payment_method='online').count(),
                # 'cod_payments': orders.filter(payment_method='cod').count(),
            })

        if vendor_id:
            return Response(analytics[0] if analytics else {"error": "No data found"}, status=200)
        return Response({'vendor_analytics': analytics}, status=200)
    
# List & Create
class AppCarouselListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = AppCarousel.objects.all()
    serializer_class = AppCarouselSerializer

    def get_queryset(self):
        vendor_id = self.request.query_params.get('vendor_id')
        if vendor_id:
            return self.queryset.filter(vendor_id=vendor_id)
        return self.queryset

# Retrieve, Update, Delete
class AppCarouselDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = AppCarousel.objects.all()
    serializer_class = AppCarouselSerializer