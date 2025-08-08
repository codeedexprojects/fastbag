from rest_framework import serializers
from .models import *
from datetime import datetime
from django.conf import settings
from foodproduct.models import *
from fashion.models import *
from groceryproducts.models import *

class StoreTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreType
        fields = ['id', 'name', 'description']

class VendorCreateSerializer(serializers.ModelSerializer):
    fssai_certificate = serializers.ImageField(required=True)
    store_logo = serializers.ImageField(required=True)
    display_image = serializers.ImageField(required=True)
    license = serializers.ImageField(required=True)
    store_type_name = serializers.CharField(source='store_type.name', read_only=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    class Meta:
        model = Vendor
        fields = [
            'id', 'store_id', 'owner_name', 'email', 'business_name', 'business_location',
            'business_landmark', 'contact_number', 'address', 'city', 'state', 'pincode',
            'fssai_no', 'fssai_certificate', 'store_logo', 'display_image', 'store_description',
            'store_type','store_type_name', 'opening_time', 'closing_time', 'license', 'is_approved', 
            'is_active', 'created_at', 'is_restaurent', 'is_Grocery','alternate_email','since','longitude','latitude','is_closed','id_proof'
        ]
        

    def get_file_url(self, file_field):
        request = self.context.get('request')
        if file_field and request:
            return request.build_absolute_uri(file_field.url)
        return None

    def get_fssai_certificate(self, obj):
        return self.get_file_url(obj.fssai_certificate)

    def get_store_logo(self, obj):
        return self.get_file_url(obj.store_logo)

    def get_display_image(self, obj):
        return self.get_file_url(obj.display_image)

    def get_license(self, obj):
        return self.get_file_url(obj.license)


class VendorNameSerializer(serializers.ModelSerializer):
    opening_time = serializers.SerializerMethodField()
    closing_time = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ['business_name', 'opening_time', 'closing_time','is_favourite','is_closed']

    def get_opening_time(self, obj):
        return obj.get_opening_time_str()  

    def get_closing_time(self, obj):
        return obj.get_closing_time_str()

class VendorDetailSerializer(serializers.ModelSerializer):
    fssai_certificate = serializers.ImageField()
    store_logo = serializers.ImageField()
    display_image = serializers.ImageField()
    license = serializers.ImageField()
    store_type_name = serializers.CharField(source='store_type.name',read_only=True)
    class Meta:
        model = Vendor
        fields = [
            'id', 'store_id', 'owner_name', 'email', 'business_name', 'business_location',
            'business_landmark', 'contact_number', 'address', 'city', 'state', 'pincode',
            'fssai_no', 'fssai_certificate', 'store_logo', 'display_image', 'store_description',
            'store_type','store_type_name', 'opening_time', 'closing_time', 'license', 'is_approved', 
            'is_active', 'created_at', 'is_restaurent', 'is_Grocery','alternate_email','since','longitude','latitude','is_closed','is_favourite','id_proof'
        ]

    def get_fssai_certificate(self, obj):
        if obj.fssai_certificate:
            return self.context['request'].build_absolute_uri(obj.fssai_certificate.url)
        return None

    def get_store_logo(self, obj):
        if obj.store_logo:
            return self.context['request'].build_absolute_uri(obj.store_logo.url)
        return None

    def get_display_image(self, obj):
        if obj.display_image:
            return self.context['request'].build_absolute_uri(obj.display_image.url)
        return None

    def get_license(self, obj):
        if obj.license:
            return self.context['request'].build_absolute_uri(obj.license.url)
        return None
    def update(self, instance, validated_data):
    # Store updates in pending fields
        if 'contact_number' in validated_data:
            instance.pending_contact_number = validated_data.pop('contact_number')
        if 'fssai_certificate' in validated_data:
            instance.pending_fssai_certificate = validated_data.pop('fssai_certificate')
        if 'license' in validated_data:
            instance.pending_license = validated_data.pop('license')

        # Update other fields directly if needed
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Mark the instance as pending approval
        instance.is_pending_update_approval = True
        instance.save()
        return instance
    
    def get_is_closed_now(self, obj):
        return obj.is_closed_now 

class VendorfavSerializer(serializers.ModelSerializer):
    opening_time = serializers.SerializerMethodField()
    closing_time = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ['business_name', 'opening_time','display_image', 'closing_time']

    def get_opening_time(self, obj):
        return obj.get_opening_time_str()  

    def get_closing_time(self, obj):
        return obj.get_closing_time_str()

class VendorPendingDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Vendor
        fields = ['id','pending_fssai_certificate','pending_license','pending_contact_number']
    


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id','business_name','','longitude','opening_time','display_image','is_closed']

class VendorHomePageSerializer(serializers.ModelSerializer):
    is_favourite = serializers.SerializerMethodField()
    store_type = serializers.CharField(source='store_type.name',read_only=True)

    class Meta:
        model = Vendor
        fields = ['id', 'business_name', 'opening_time','closing_time','display_image', 'is_favourite','store_type','store_logo','business_location','is_closed']

    def get_is_favourite(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return FavoriteVendor.objects.filter(user=user, vendor=obj).exists()
        return False

class VendorLoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)


class VendorOTPVerifySerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class VendorApprovalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'is_approved']

class CategorySerializer(serializers.ModelSerializer):
    StoreType_name = serializers.CharField(source='store_type.name',read_only=True)
    class Meta:
        model = Category
        fields = ['id','name','created_at','category_image','store_type','StoreType_name']



class ClothingSubCategorySerializerlist(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source = 'vendor.business_name',read_only=True)
    category_name = serializers.CharField(source = 'category.name',read_only=True)
    class Meta:
        model = ClothingSubCategory
        fields = ['id','vendor','vendor_name','category','category_name','name','enable_subcategory','subcategory_image',
                  'created_at']
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  
        if instance.subcategory_image and request:
            representation['subcategory_image'] = request.build_absolute_uri(instance.subcategory_image.url)
        return representation

class GrocerySubCategorySerializerlist(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source = 'vendor.business_name',read_only=True)
    category_name = serializers.CharField(source = 'category.name',read_only=True)
    class Meta:
        model = GrocerySubCategories
        fields = ['id','vendor','vendor_name','category','category_name','name','enable_subcategory','subcategory_image',
                  'created_at']
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  
        if instance.subcategory_image and request:
            representation['subcategory_image'] = request.build_absolute_uri(instance.subcategory_image.url)
        return representation

class FoodSubCategorySerializerlist(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source = 'vendor.business_name',read_only=True)
    category_name = serializers.CharField(source = 'category.name',read_only=True)
    class Meta:
        model = FoodSubCategories
        fields = ['id','vendor','vendor_name','category','category_name','name','enable_subcategory','subcategory_image',
                  'created_at']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')  
        if instance.subcategory_image and request:
            representation['subcategory_image'] = request.build_absolute_uri(instance.subcategory_image.url)
        return representation
    
class ProductSerializer(serializers.Serializer):
    product_type = serializers.ChoiceField(choices=['dish', 'grocery', 'clothing'])
    vendor = serializers.IntegerField()  # Accepts vendor ID from request
    category = serializers.IntegerField()  # Accepts category ID from request
    subcategory = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    wholesale_price = serializers.DecimalField(default=0, max_digits=10, decimal_places=2)
    offer_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    discount = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    is_offer_product = serializers.BooleanField(default=False)
    is_popular_product = serializers.BooleanField(default=False)
    
    # Additional fields for different product types
    variants = serializers.JSONField(required=False, default=list)  # Dish
    weights = serializers.JSONField(required=False, default=dict)  # Grocery
    weight_measurement = serializers.CharField(max_length=100, required=False, allow_blank=True)  # Grocery
    gender = serializers.CharField(max_length=1, required=False, allow_blank=True)  # Clothing
    colors = serializers.JSONField(required=False, default=list)  # Clothing

    def create(self, validated_data):
        product_type = validated_data.pop('product_type')
        
        # Fetch the vendor instance using the ID
        vendor_id = validated_data.pop('vendor')
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            raise serializers.ValidationError({"vendor": "Vendor not found."})
        
        # Fetch the category instance using the ID
        category_id = validated_data.pop('category')
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise serializers.ValidationError({"category": "Category not found."})

        validated_data['vendor'] = vendor  # Assign vendor instance
        validated_data['category'] = category  # Assign category instance

        if product_type == 'dish':
            return Dish.objects.create(**validated_data)
        elif product_type == 'grocery':
            return GroceryProducts.objects.create(**validated_data)
        elif product_type == 'clothing':
            return Clothing.objects.create(**validated_data)
        else:
            raise serializers.ValidationError("Invalid product type.")
        
class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    store_type = serializers.CharField(source='category.store_type.name',read_only=True)

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'category_name','store_type', 'sub_category_image', 'is_active', 'created_at']

class SubCategoryRequestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)

    class Meta:
        model = SubCategoryRequest
        fields = [
            'id', 'vendor', 'vendor_name', 'category', 'category_name', 'name',
            'sub_category_image', 'status', 'admin_remark', 'created_at'
        ]
        read_only_fields = ['status', 'admin_remark', 'created_at', 'vendor']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'vendor'):
            validated_data['vendor'] = request.user.vendor
        return super().create(validated_data)
    

class AppCarouselSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.business_name',read_only=True)
    class Meta:
        model = AppCarousel
        fields = ['id','vendor','vendor_name','title','ads_image','created_at']