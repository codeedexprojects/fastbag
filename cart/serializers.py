from rest_framework import serializers
from .models import Cart, CartItem
from fashion.models import Clothing
from foodproduct.models import Dish
from groceryproducts.models import GroceryProducts
from .models import Checkout, CheckoutItem
from cart.models import Cart, CartItem , Order ,OrderItem , Notification
import uuid
import razorpay
from django.conf import settings
from decimal import Decimal
from django.utils.timezone import now
from users.models import Coupon
from groceryproducts.models import GroceryCoupon
from foodproduct.models import FoodCoupon
from vendors.models import Vendor
from django.utils import timezone


class CartItemSerializer(serializers.ModelSerializer):
    product_details = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    selected_variant_details = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "cart", "vendor", "product_type", "product_id", "quantity", "variant", "price", "product_details", "total_amount", "selected_variant_details"]

    def get_product_details(self, obj):
        product_model = {
            "Fashion": Clothing,
            "Restaurent": Dish,
            "Grocery": GroceryProducts
        }.get(obj.product_type)

        product = product_model.objects.filter(id=obj.product_id).first() if product_model else None

        return {
            "name": product.name if product else "Unknown",
            "images": [self.context['request'].build_absolute_uri(img.image.url) for img in product.images.all()] if product and hasattr(product, "images") else [],
            "description": product.description if hasattr(product, "description") else "No description available"
        }

    def get_total_amount(self, obj):
        return obj.quantity * float(obj.price)

    def get_selected_variant_details(self, obj):
        product_model = {
            "Fashion": Clothing,
            "Restaurent": Dish,
            "Fashion": GroceryProducts
        }.get(obj.product_type)

        product = product_model.objects.filter(id=obj.product_id).first() if product_model else None

        if product:
            if obj.product_type == "Grocery":
                return {"selected_weight": obj.variant, "price_for_weight": product.get_price_for_weight(obj.variant)}
            elif obj.product_type == "Fashion":
                return {"selected_size": obj.variant, "price_for_size": product.get_price_for_size(obj.variant)}
            elif obj.product_type == "Restaurent":
                variant_details = next((v for v in product.variants if v["name"] == obj.variant), None)
                return variant_details if variant_details else {"selected_variant": obj.variant}

        return {"selected_variant": obj.variant}

    def get_selected_variant_details(self, obj):
        product_model = {
            "Fashion": Clothing,
            "Restaurent": Dish,
            "Grocery": GroceryProducts
        }.get(obj.product_type)

        product = product_model.objects.filter(id=obj.product_id).first() if product_model else None

        if product:
            if obj.product_type == "Grocery":
                return {"selected_weight": obj.variant, "price_for_weight": product.get_price_for_weight(obj.variant)}

            elif obj.product_type == "Fashion":
                # Extract color and size from the variant field
                variant_data = obj.variant.split(",")  # Assuming variant is stored as "Color,Size"
                color_name = variant_data[0].strip() if len(variant_data) > 0 else None
                size_name = variant_data[1].strip() if len(variant_data) > 1 else None

                # Find the matching color object
                selected_color = next((color for color in product.colors if color["color_name"] == color_name), None)
                if selected_color:
                    # Find the matching size object
                    selected_size = next((size for size in selected_color["sizes"] if size["size"] == size_name), None)
                    if selected_size:
                        return {
                            "selected_color": color_name,
                            "selected_size": size_name,
                            "price_for_size": selected_size["price"]
                        }

            elif obj.product_type == "Restaurent":
                variant_details = next((v for v in product.variants if v["name"] == obj.variant), None)
                return variant_details if variant_details else {"selected_variant": obj.variant}

        return {"selected_variant": obj.variant}



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items']


class CheckoutItemSerializer(serializers.ModelSerializer):
    product_details = serializers.SerializerMethodField()

    class Meta:
        model = CheckoutItem
        fields = '__all__'
        extra_fields = ['product_details']

    def get_product_details(self, obj):
        from .serializers import ClothingSerializer, DishSerializer, GrocerySerializer
        
        model_map = {
            'clothing': (Clothing, ClothingSerializer),
            'dish': (Dish, DishSerializer),
            'grocery': (GroceryProducts, GrocerySerializer)
        }
        
        if obj.product_type not in model_map:
            return None
            
        model, serializer = model_map[obj.product_type]
        
        try:
            product = model.objects.get(id=obj.product_id)
            return serializer(product, context=self.context).data
        except model.DoesNotExist:
            return None

class CheckoutSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    contact_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Checkout
        fields = '__all__'
        read_only_fields = ['order_id', 'total_amount', 'final_amount', 'coupon_discount']

    def validate(self, data):
        user = self.context['request'].user
        coupon_code = data.get('coupon_code')
        total_amount = 0
        discount_amount = 0
        applied_coupon = None

        # Fetch CartItems associated with the user's cart
        cart_items = CartItem.objects.filter(cart__user=user).select_related('vendor')

        if not cart_items.exists():
            raise serializers.ValidationError({"cart": "Your cart is empty."})

        # Calculate total amount
        total_amount = sum(item.price * item.quantity for item in cart_items)

        print(f"DEBUG: Total cart amount = {total_amount}")

        # Validate coupon if provided
        if coupon_code:
            now = timezone.now()
            try:
                # Check if the coupon exists, is active, and within the valid time range
                coupon = Coupon.objects.filter(
                    code=coupon_code,
                    valid_from__lte=now,
                    valid_to__gte=now
                ).first()

                if not coupon:
                    raise serializers.ValidationError({"coupon_code": "Invalid or expired coupon."})

                # Check if the total amount meets the minimum order amount
                if coupon.min_order_amount and total_amount < coupon.min_order_amount:
                    raise serializers.ValidationError({"coupon_code": f"Minimum order amount should be {coupon.min_order_amount}"})

                # Apply the coupon discount
                discount_amount = coupon.discount_value
                if coupon.discount_type == 'percentage':
                    discount_amount = (total_amount * coupon.discount_value) / 100
                    if coupon.max_discount and discount_amount > coupon.max_discount:
                        discount_amount = coupon.max_discount

                # Update coupon details in the checkout
                data['coupon_code'] = coupon.code
                data['coupon_discount'] = discount_amount
                print(f"DEBUG: Coupon applied - {coupon.code}, Discount = {discount_amount}")

            except Coupon.DoesNotExist:
                print(f"DEBUG: Coupon {coupon_code} does not exist or is inactive")
                raise serializers.ValidationError({"coupon_code": "Invalid or expired coupon."})

        else:
            data['coupon_code'] = None
            data['coupon_discount'] = 0.00
            print("DEBUG: No coupon applied")

        return data


    def create(self, validated_data):
        user = self.context['request'].user

        # Calculating final amount after applying coupon discount
        total_amount = validated_data['total_amount']
        coupon_discount = validated_data['coupon_discount']
        final_amount = total_amount - coupon_discount

        # Creating Checkout instance
        checkout = Checkout.objects.create(
            user=user,
            order_id=str(uuid.uuid4()),
            total_amount=total_amount,
            final_amount=final_amount,
            payment_method=validated_data.get('payment_method'),
            shipping_address=validated_data.get('shipping_address'),
            billing_address=validated_data.get('billing_address'),
            contact_number=validated_data.get('contact_number'),
            coupon_code=validated_data.get('coupon_code'),
            coupon_discount=coupon_discount
        )

        print(f"DEBUG: Checkout created - Order ID: {checkout.order_id}, Final amount: {final_amount}")

        # Create an Order instance linked to Checkout
        order = Order.objects.create(
            user=user,
            checkout=checkout,
            order_id=checkout.order_id,
            total_amount=checkout.total_amount,
            final_amount=checkout.final_amount,
            payment_method=checkout.payment_method,
            payment_status='pending',
            order_status='pending',
            shipping_address=checkout.shipping_address,
            contact_number=checkout.contact_number,
            coupon_code=checkout.coupon_code,
            coupon_discount=checkout.coupon_discount
        )

        print(f"DEBUG: Order created for Checkout ID: {checkout.id}, Order ID: {order.order_id}")

        # Clear the user's cart after checkout
        CartItem.objects.filter(cart__user=user).delete()

        return checkout



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_id',
            'product_name',
            'product_type',
            'quantity',
            'price_per_unit',
            'subtotal',
            'status',
            'variant',
            'cancel_reason',
            'cancelled_at',
        ]
        read_only_fields = ['id', 'cancelled_at']


class OrderSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    product_details = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'order_id',
            'user',
            'user_name',
            'total_amount',
            'payment_method',
            'payment_status',
            'order_status',
            'shipping_address',
            'contact_number',
            'created_at',
            'updated_at',
            'final_amount',
            'used_coupon',
            'product_details',
            'delivery_pin',
        ]

    def get_product_details(self, obj):
        ordered_items = []
        request = self.context.get('request')

        product_details = obj.product_details or []
        product_ids = [item.get('product_id') for item in product_details if item.get('product_id')]

        # Bulk fetch from all product types
        clothings = {str(c.id): c for c in Clothing.objects.filter(id__in=product_ids).prefetch_related('images')}
        groceries = {str(g.id): g for g in GroceryProducts.objects.filter(id__in=product_ids)}
        dishes = {str(d.id): d for d in Dish.objects.filter(id__in=product_ids)}

        for item in product_details:
            product_id = str(item.get('product_id'))
            quantity = item.get('quantity', 0) or 0
            product = clothings.get(product_id) or groceries.get(product_id) or dishes.get(product_id)
            product_name = getattr(product, 'name', '') or item.get('product_name', f'Product {product_id}')

            # Initialize product_info with all necessary fields from OrderItemSerializer
            product_info = {
                "id": item.get('id'),
                "product_id": product_id,
                "product_name": product_name,
                "product_type": None,
                "quantity": quantity,
                "price_per_unit": item.get('price_per_unit', 0),
                "subtotal": item.get('subtotal', 0),
                "status": item.get('status'),
                "variant": item.get('variant'),
                "cancel_reason": item.get('cancel_reason'),
                "cancelled_at": item.get('cancelled_at'),
                "product_image": "",
                "images": [],
                "selected_color": None,
                "selected_size": None,
                "available_colors": [],
                "selected_weight": None,
                "selected_variant": None,
                "available_variants": [],
            }

            if product:
                # Fallbacks for missing data
                if not product_info['product_name']:
                    product_info['product_name'] = getattr(product, 'name', '')

                if not product_info['price_per_unit']:
                    product_info['price_per_unit'] = getattr(product, 'price', 0)

                if not product_info['subtotal']:
                    product_info['subtotal'] = quantity * product_info['price_per_unit']

                # Handling images
                image_urls = []
                if hasattr(product, 'images'):
                    images = product.images.all()
                    image_urls = [request.build_absolute_uri(img.image.url) for img in images if img.image]

                product_info['images'] = image_urls
                product_info['product_image'] = image_urls[0] if image_urls else ''

                # Product-specific attribute handling
                if isinstance(product, Clothing):
                    product_info['product_type'] = 'clothing'
                    product_info['available_colors'] = product.colors or []

                    variant = item.get('variant')
                    if variant and '-' in variant:
                        color_part, size_part = variant.split('-', 1)
                        product_info['selected_color'] = color_part.strip()
                        product_info['selected_size'] = size_part.strip()
                    else:
                        product_info['selected_color'] = item.get('color')
                        product_info['selected_size'] = item.get('size')

                    # Cleanup irrelevant fields
                    product_info.pop('selected_weight', None)
                    product_info.pop('available_weights', None)
                    product_info.pop('selected_variant', None)
                    product_info.pop('available_variants', None)

                elif isinstance(product, GroceryProducts):
                    product_info['product_type'] = 'grocery'
                    weight = item.get('weight') or item.get('selected_weight')
                    if not weight:
                        variant = item.get('variant')
                        if variant and 'ml' in variant:
                            weight = variant.strip()
                    product_info['selected_weight'] = weight

                    # Cleanup irrelevant fields
                    product_info.pop('selected_color', None)
                    product_info.pop('selected_size', None)
                    product_info.pop('available_colors', None)
                    product_info.pop('selected_variant', None)
                    product_info.pop('available_variants', None)

                elif isinstance(product, Dish):
                    product_info['product_type'] = 'dish'
                    product_info['available_variants'] = product.variants or []
                    product_info['selected_variant'] = item.get('variant') or item.get('selected_variant')

                    # Cleanup irrelevant fields
                    product_info.pop('selected_color', None)
                    product_info.pop('selected_size', None)
                    product_info.pop('available_colors', None)
                    product_info.pop('selected_weight', None)
                    product_info.pop('available_weights', None)

            else:
                product_info['error'] = 'Product not found'

            ordered_items.append(product_info)

        return ordered_items
        
class CartCheckoutItemSerializer(serializers.ModelSerializer):
    product_details = serializers.SerializerMethodField

    class Meta:
        model = CheckoutItem
        fields = ['product_id', 'product_type', 'quantity', 'color', 'size', 'variant', 'price', 'subtotal', 'product_details']

    def get_product_details(self, obj):
        if obj.product_type == 'clothing':
            product = Clothing.objects.filter(id=obj.product_id).first()
        elif obj.product_type == 'dish':
            product = Dish.objects.filter(id=obj.product_id).first()
        elif obj.product_type == 'grocery':
            product = GroceryProducts.objects.filter(id=obj.product_id).first()
        else:
            return None

        if product:
            return {
                "name": product.name,
                "image": product.image.url if product.image else None,
                "description": product.description,
                "price": obj.price,
            }
        return None


class VendorCartSerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    vendor_logo = serializers.SerializerMethodField()
    total_items = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    items = CartItemSerializer(many=True)

    def get_vendor_logo(self, obj):
        return obj.get("vendor_logo")


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'created_at', 'order', 'user']
        read_only_fields = ['id', 'created_at', 'order', 'user']

