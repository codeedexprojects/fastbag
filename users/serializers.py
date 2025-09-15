from rest_framework import serializers
from .models import *
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from groceryproducts.models import *
from foodproduct.models import *

class AdminLoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        mobile_number = data.get('mobile_number')
        password = data.get('password')

        # Authenticate user using the mobile number and password
        user = authenticate(request=self.context.get('request'), mobile_number=mobile_number, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid credentials or not an admin user.")
        
        # Check if the user is an admin
        if not user.is_superuser:
            raise PermissionDenied("User is not an admin.")

        # Generate tokens for the user
        refresh = RefreshToken.for_user(user)

        data['user'] = user
        data['access_token'] = str(refresh.access_token)
        data['refresh_token'] = str(refresh)

        return data

    
class RegisterSerializer(serializers.ModelSerializer):
    mobile_number = serializers.CharField(max_length=15)

    class Meta:
        model = CustomUser
        fields = ['mobile_number']

class VerifyOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class AddressSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.name',read_only=True)
    email = serializers.CharField(source='user.email',read_only=True)
    class Meta:
        model = Address
        fields = [
            'id', 'username','email','address_line1', 'address_line2', 'city', 'state',
            'country', 'pincode', 'contact_number', 'is_primary','address_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CustomUserDetailSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'mobile_number', 'name', 'email', 
            'is_verified', 'is_active', 'is_staff', 
             'addresses','date_joined'
        ]
        def update(self, instance, validated_data):
            addresses_data = validated_data.pop('addresses', [])
            instance = super().update(instance, validated_data)

            for address_data in addresses_data:
                Address.objects.update_or_create(
                    user=instance,
                    id=address_data.get('id'),
                    defaults=address_data
                )
            return instance
        
class CustomUserListSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'mobile_number', 'name', 'email', 
            'is_verified', 'is_active', 'is_staff', 
            'date_joined', 'addresses'
        ]

CustomUser = get_user_model()
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser  
        fields = ['name', 'email','mobile_number']

    def validate_email(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email or mobile number is already associated with another account.")
        return value
    


class UnifiedProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    offer_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    discount = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    is_offer_product = serializers.BooleanField()
    is_popular_product = serializers.BooleanField()
    image = serializers.ImageField(required=False)
    category_name = serializers.CharField()
    sub_category_name = serializers.CharField(required=False)
    weight_measurement = serializers.CharField(required=False)
    price_for_selected_weight = serializers.SerializerMethodField()

    def get_price_for_selected_weight(self, obj):
        # If the object is an instance of GroceryProducts, calculate price based on selected weight
        if isinstance(obj, GroceryProducts):
            selected_weight = self.context.get('selected_weight')
            if selected_weight:
                return obj.get_price_for_weight(selected_weight)
            return obj.price
        return obj.offer_price if obj.offer_price else obj.price

    def to_representation(self, instance):
        # Handle both Dish and GroceryProduct model instances
        if isinstance(instance, Dish):
            return {
                'id': instance.id,
                'name': instance.name,
                'description': instance.description,
                'price': instance.price,
                'offer_price': instance.offer_price,
                'discount': instance.discount,
                'is_offer_product': instance.is_offer_product,
                'is_popular_product': instance.is_popular_product,
                'category_name': instance.category.name,
                'sub_category_name': instance.subcategory.name if instance.subcategory else '',
                'image': instance.images.first().image.url if instance.images.exists() else None
            }
        elif isinstance(instance, GroceryProducts):
            return {
                'id': instance.id,
                'name': instance.name,
                'description': instance.description,
                'price': instance.price,
                'offer_price': instance.offer_price,
                'discount': instance.discount,
                'is_offer_product': instance.is_offer_product,
                'is_popular_product': instance.is_popular_product,
                'category_name': instance.category.name,
                'sub_category_name': instance.sub_category.name if instance.sub_category else '',
                'weight_measurement': instance.weight_measurement,
                'price_for_selected_weight': self.get_price_for_selected_weight(instance),
                'image': instance.image.url if instance.image else None
            }
        return super().to_representation(instance)




class UnifiedCategoryListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category_type = serializers.CharField()  # 'food', 'grocery', or 'fashion'
    store_name = serializers.CharField(allow_null=True)
    subcategory_name = serializers.CharField(allow_null=True)
    subcategory_image = serializers.ImageField(allow_null=True)
    enable_category = serializers.BooleanField()
    enable_subcategory = serializers.BooleanField(allow_null=True)

    def to_representation(self, instance):
        category_mapping = {
            'food': 'food',
            'grocery': 'grocery',
            'fashion': 'fashion'
        }

        return {
            'id': instance.id,
            'name': instance.name,
            'category_type': category_mapping.get(instance.category_type, 'unknown'),  # Default to 'unknown' if missing
            'store_name': instance.store_type.name if instance.store_type else None,  # Handle None case
            'enable_category': getattr(instance, 'enable_category', True),  # Default to True if missing
        }

    
class CreateStaffUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['name', 'mobile_number', 'email', 'password','permissions','is_staff','is_superuser']
        read_only_fields= ['created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data, is_staff=True)

        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    
class AdminNotificationSerializer(serializers.ModelSerializer):
    user = CustomUserDetailSerializer(read_only=True)
    
    class Meta:
        model = UserRegNotification
        fields = '__all__'
        read_only_fields = ['created_at']

# class CouponSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Coupon
#         fields = '__all__'
#         read_only_fields = ['created_by', 'vendor']

#     def create(self, validated_data):
#         user = self.context['request'].user

#         # Check if the user is an admin (superuser)
#         if user.is_superuser:
#             return super().create(validated_data)

#         # If the user is a vendor, they can only create coupons for themselves
#         try:
#             vendor = Vendor.objects.get(user=user)  # Get the vendor linked to the user
#             validated_data['vendor'] = vendor  # Assign vendor to coupon
#             return super().create(validated_data)
#         except Vendor.DoesNotExist:
#             raise serializers.ValidationError("You do not have permission to create a coupon.")

class CouponSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value', 'min_order_amount',
            'max_discount', 'valid_from', 'valid_to', 'usage_limit',
            'is_new_customer', 'vendor', 'vendor_name', 'created_by',
        ]


        
class UnifiedWishlistSerializer(serializers.ModelSerializer):
    product_type = serializers.CharField(write_only=True)
    product_id = serializers.IntegerField(write_only=True)
    product_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UnifiedWishlist
        fields = ['id', 'product_type', 'product_id', 'added_at', 'product_detail']
        read_only_fields = ['added_at']

    def create(self, validated_data):
        product_type = validated_data.pop('product_type')
        product_id = validated_data.pop('product_id')
        user = self.context['request'].user

        try:
            content_type = ContentType.objects.get(model=product_type.lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({'product_type': 'Invalid product type.'})

        return UnifiedWishlist.objects.create(
            user=user,
            content_type=content_type,
            object_id=product_id
        )

    def get_product_detail(self, obj):
        product = obj.product
        model = obj.content_type.model

        if model == 'groceryproducts':
            from groceryproducts.serializers import GroceryProductSerializer
            return GroceryProductSerializer(product).data

        elif model == 'clothing':
            from fashion.serializers import ClothingSerializer
            return ClothingSerializer(product).data

        elif model == 'dish':
            from foodproduct.serializers import DishCreateSerializer
            return DishCreateSerializer(product).data

        return {"error": "Unknown product type"}

class FavoriteVendorSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    opening_time = serializers.CharField(source='vendor.opening_time', read_only=True)
    display_image = serializers.ImageField(source='vendor.display_image', read_only=True)
    is_favourite = serializers.CharField(source='vendor.is_favourite', read_only=True)
    closing_time = serializers.CharField(source='vendor.closing_time', read_only=True)

    class Meta:
        model = FavoriteVendor
        fields = ['id', 'vendor','business_name', 'opening_time', 'closing_time','display_image', 'is_favourite']

    def validate_vendor(self, value):
        user = self.context['request'].user
        if FavoriteVendor.objects.filter(user=user, vendor=value).exists():
            raise serializers.ValidationError("Vendor is already in your favourites.")
        return value
    

class BigBuyOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BigBuyOrderItem
        fields = ['id', 'food_item', 'quantity_in_kg']


class BigBuyOrderSerializer(serializers.ModelSerializer):
    order_items = BigBuyOrderItemSerializer(many=True, required=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    order_id = serializers.CharField(read_only=True)

    class Meta:
        model = BigBuyOrder
        fields = [
            'id',
            'order_id', 
            'order_items',
            'number_of_people',
            'status',
            'amount',
            'preferred_delivery_date',
            'special_occasion',
            'diet_category',
            'additional_notes',
            'created_at',
            'user',
            'user_name'
            'cancel_reason'
        ]
        read_only_fields = ['user', 'created_at', 'order_id']

    
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items')
        
        order = BigBuyOrder.objects.create(**validated_data)
        
        for item_data in order_items_data:
            BigBuyOrderItem.objects.create(order=order, **item_data)
            
        return order
    
    def update(self, instance, validated_data):
        if 'order_items' in validated_data:
            order_items_data = validated_data.pop('order_items')
            
            instance.order_items.all().delete()
            
            for item_data in order_items_data:
                BigBuyOrderItem.objects.create(order=instance, **item_data)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ['id', 'latitude', 'longitude']

class StaffLoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()
    password = serializers.CharField(write_only=True)