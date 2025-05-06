from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import *
from groceryproducts.models import *
from foodproduct.models import *
from fashion.models import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.conf import settings
import razorpay
from vendors.authentication import VendorJWTAuthentication
from users.models import Coupon

class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        cart_items = CartItem.objects.filter(cart__user=request.user)        
        serializer = CartItemSerializer(cart_items, many=True, context={'request': request})
        total_cart_amount = sum(item['total_amount'] for item in serializer.data)

        response_data = {
            "count": len(serializer.data),
            "results": serializer.data,
            "total_cart_amount": total_cart_amount
        }

        return Response(response_data)


#add to cart
from rest_framework import generics, status
from rest_framework.response import Response

# class AddToCartView(generics.CreateAPIView):
#     def create(self, request, *args, **kwargs):
#         data = request.data

#         product_type = data.get("product_type")
#         product_id = data.get("product_id")
#         vendor = data.get("vendor")
#         quantity = int(data.get("quantity", 1))
#         variant = data.get("variant")  # Used for grocery (weight) and dish (size)
#         color = data.get("color")  # Used for clothing
#         size = data.get("size")  # Used for clothing

#         # Map product_type to models
#         product_model = {
#             "clothing": Clothing,
#             "dish": Dish,
#             "grocery": GroceryProducts
#         }.get(product_type)

#         if not product_model:
#             return Response({"error": "Invalid product type"}, status=status.HTTP_400_BAD_REQUEST)

#         product = product_model.objects.filter(id=product_id).first()
#         if not product:
#             return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

#         # Handle product-specific variant selection
#         if product_type == "clothing":
#             if not color or not size:
#                 return Response({"error": "Color and size are required for clothing"}, status=status.HTTP_400_BAD_REQUEST)
            
#             selected_color = next((c for c in product.colors if c["color_name"] == color), None)
#             if not selected_color:
#                 return Response({"error": f"Color '{color}' not available"}, status=status.HTTP_400_BAD_REQUEST)
            
#             selected_size = next((s for s in selected_color["sizes"] if s["size"] == size), None)
#             if not selected_size:
#                 return Response({"error": f"Size '{size}' not available in color '{color}'"}, status=status.HTTP_400_BAD_REQUEST)

#             if selected_size["stock"] < quantity:
#                 return Response({"error": "Insufficient stock"}, status=status.HTTP_400_BAD_REQUEST)

#             price = selected_size["price"]
#             variant = f"{color} - {size}"

#         elif product_type == "grocery" and variant:
#             price = product.get_price_for_variant(variant)
#         elif product_type == "dish" and variant:
#             price = product.get_price_for_variant(variant)
#         else:
#             price = product.offer_price if product.offer_price else product.price

#         # Get or create cart
#         cart, created = Cart.objects.get_or_create(user=request.user)

#         # # ** Restrict grocery and dish items from different vendors **
#         # if product_type in ["grocery", "dish"]:
#         #     existing_items = CartItem.objects.filter(cart=cart)
#         #     if existing_items.exists():
#         #         existing_vendor = existing_items.first().vendor_id
#         #         if existing_vendor != vendor:
#         #             return Response({"error": "You can only add grocery or food items from a single vendor at a time."}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if the product is already in the cart
#         cart_item = CartItem.objects.filter(
#             cart=cart, 
#             vendor_id=vendor, 
#             product_type=product_type, 
#             product_id=product_id, 
#             variant=variant
#         ).first()

#         if cart_item:
#             cart_item.quantity += quantity
#             cart_item.save()
#             message = "Product quantity updated in cart"
#         else:
#             cart_item = CartItem.objects.create(
#                 cart=cart,
#                 vendor_id=vendor,
#                 product_type=product_type,
#                 product_id=product_id,
#                 quantity=quantity,
#                 variant=variant,  # Color and size stored as variant
#                 price=price
#             )
#             message = "Product added to cart"
            

#         return Response(
#             {
#                 "message": message, 
#                 "cart_item": {
#                     "id": cart_item.id, 
#                     "quantity": cart_item.quantity, 
#                     "variant": variant
#                 }
#             }, 
#             status=status.HTTP_201_CREATED
#         )
from django.shortcuts import get_object_or_404

class AddToCartView(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        data = request.data

        product_type = data.get("product_type")
        product_id = data.get("product_id")
        vendor_id = data.get("vendor")
        quantity = int(data.get("quantity", 1))
        variant = data.get("variant")  # Used for grocery and dish
        color = data.get("color")      # Used for clothing
        size = data.get("size")        # Used for clothing

        # Product model mapping
        model_map = {
            "Fashion": Clothing,
            "Restaurent": Dish,
            "Grocery": GroceryProducts
        }

        product_model = model_map.get(product_type)
        if not product_model:
            return Response({"error": "Invalid product type."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(product_model, id=product_id)

        # Clothing logic
        if product_type == "Fashion":
            if not color or not size:
                return Response({"error": "Color and size are required for clothing."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                selected_color = ClothingColor.objects.get(clothing=product, color_name__iexact=color)
            except ClothingColor.DoesNotExist:
                return Response({"error": f"Color '{color}' not available."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                selected_size = ClothingSize.objects.get(color=selected_color, size__iexact=size)
            except ClothingSize.DoesNotExist:
                return Response({"error": f"Size '{size}' not available for color '{color}'."}, status=status.HTTP_400_BAD_REQUEST)

            if selected_size.stock < quantity:
                return Response({"error": "Insufficient stock available."}, status=status.HTTP_400_BAD_REQUEST)

            price = float(selected_size.offer_price or selected_size.price)
            variant = f"{color} - {size}"

        # Dish or Grocery logic
        elif product_type in ["Restaurent", "Grocery"]:
            if not variant:
                return Response({"error": f"{product_type.capitalize()} variant is required."}, status=status.HTTP_400_BAD_REQUEST)

            price = product.get_price_for_variant(variant) if product_type == "Restaurent" else product.get_price_for_weight(variant)

            try:
                price = float(price)
            except (ValueError, TypeError):
                return Response({"error": f"Invalid price value '{price}' for variant '{variant}'."}, status=status.HTTP_400_BAD_REQUEST)

            # Quantity deduction for grocery
            if product_type == "grocery":
                if isinstance(product.weights, list):
                    for weight_data in product.weights:
                        if weight_data.get("weight") == variant:
                            available_qty = weight_data.get("quantity", 0)
                            if available_qty < quantity:
                                return Response({"error": f"Only {available_qty} units available for '{variant}'."}, status=status.HTTP_400_BAD_REQUEST)
                            weight_data["quantity"] = available_qty - quantity
                            break
                elif isinstance(product.weights, dict):
                    if variant in product.weights:
                        available_qty = product.weights[variant].get("quantity", 0)
                        if available_qty < quantity:
                            return Response({"error": f"Only {available_qty} units available for '{variant}'."}, status=status.HTTP_400_BAD_REQUEST)
                        product.weights[variant]["quantity"] = available_qty - quantity

                product.save()

        # General fallback (if needed)
        else:
            price = float(product.offer_price or product.price)

        # Get or create cart
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Check if the item is already in cart
        cart_item = CartItem.objects.filter(
            cart=cart,
            product_type=product_type,
            product_id=product_id,
            vendor_id=vendor_id,
            variant=variant
        ).first()

        if cart_item:
            cart_item.quantity += quantity
            cart_item.save()
            message = "Cart item updated successfully."
        else:
            cart_item = CartItem.objects.create(
                cart=cart,
                vendor_id=vendor_id,
                product_type=product_type,
                product_id=product_id,
                quantity=quantity,
                variant=variant,
                price=price
            )
            message = "Item added to cart successfully."

        return Response({
            "message": message,
            "cart_item": {
                "id": cart_item.id,
                "product_type": product_type,
                "product_id": product_id,
                "variant": variant,
                "quantity": cart_item.quantity,
                "price": float(price),
                "total_price": float(cart_item.quantity * price)
            }
        }, status=status.HTTP_201_CREATED)



class RemoveFromCartView(generics.GenericAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        cart_item_id = kwargs.get("pk")
        quantity_to_set = int(request.data.get("quantity", 1))  

        cart_item = CartItem.objects.filter(id=cart_item_id, cart__user=request.user).first()

        if not cart_item:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        if quantity_to_set > cart_item.quantity:
            cart_item.quantity = quantity_to_set  
            message = "Item quantity updated"
        elif quantity_to_set < cart_item.quantity:
            cart_item.quantity -= (cart_item.quantity - quantity_to_set)  
            message = "Item quantity updated"
        else:
            return Response({"message": "No change in quantity"}, status=status.HTTP_200_OK)

        cart_item.save()

        return Response(
            {"message": message, "cart_item": {"id": cart_item_id, "quantity": cart_item.quantity}},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        cart_item_id = kwargs.get("pk")
        cart_item = CartItem.objects.filter(id=cart_item_id, cart__user=request.user).first()

        if cart_item:
            cart_item.delete()
            return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)

        return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)


class GroceryCartView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart, product_type="grocery")

        grocery_items = []
        total_amount = 0  

        for item in cart_items:
            product = GroceryProducts.objects.filter(id=item.product_id).first()
            if product:
                item_total = item.price * item.quantity  
                total_amount += item_total  

                grocery_items.append({
                    "id": item.product_id,
                    "vendor_id": item.vendor_id,
                    "name": product.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "variant": item.variant,
                    "images": [
                        request.build_absolute_uri(img.image.url) for img in product.images.all()
                    ],
                    "item_total": item_total  
                })

        return Response({
            "grocery_products": grocery_items,
            "total_amount": total_amount  
        })


class DishCartView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart, product_type="dish")

        dish_items = []
        total_amount = 0  

        for item in cart_items:
            product = Dish.objects.filter(id=item.product_id).first()
            if product:
                item_total = item.price * item.quantity  
                total_amount += item_total  

                dish_items.append({
                    "id": item.product_id,
                    "vendor_id": item.vendor_id,
                    "name": product.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "variant": item.variant,
                    "images": [
                        request.build_absolute_uri(img.image.url) for img in product.images.all()
                    ],
                    "item_total": item_total  
                })

        return Response({
            "dishes": dish_items,
            "total_amount": total_amount  
        })


class ClothingCartView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart, product_type="clothing")

        clothing_items = []
        total_amount = 0  

        for item in cart_items:
            product = Clothing.objects.filter(id=item.product_id).first()
            if product:
                item_total = item.price * item.quantity  
                total_amount += item_total  

                clothing_items.append({
                    "id": item.product_id,
                    "vendor_id": item.vendor_id,
                    "name": product.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "variant": item.variant,
                    "images": [
                        request.build_absolute_uri(img.image.url) for img in product.images.all()
                    ],
                    "item_total": item_total  
                })

        return Response({
            "clothing": clothing_items,
            "total_amount": total_amount  
        })
class CheckoutView(generics.CreateAPIView):
    queryset = Checkout.objects.all()
    serializer_class = CheckoutSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        print(f"DEBUG: User ID: {user.id}")

        # Validate the incoming data using the serializer
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Fetch the user's cart and validate if it has items
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        print(f"DEBUG: Cart items found: {cart_items.count()}")

        # Calculate total cart amount
        total_amount = sum(item.price * item.quantity for item in cart_items)
        print(f"DEBUG: Total cart amount = {total_amount}")

        # Apply coupon if provided
        coupon_code = request.data.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            # Log the coupon details to ensure it is correctly fetched
            print(f"Coupon fetched: {coupon}")

            # Check if the current date is within the valid range
            current_date = timezone.now()  # Use timezone-aware datetime

            if not (coupon.valid_from <= current_date <= coupon.valid_to):
                return Response({"error": "Coupon is not valid anymore."}, status=status.HTTP_400_BAD_REQUEST)

            # Proceed with coupon application logic
            if coupon.discount_type == 'percentage':
                discount_amount = total_amount * (coupon.discount_value / 100)
                if discount_amount > coupon.max_discount:
                    discount_amount = coupon.max_discount
                total_amount -= discount_amount  # Apply discount

            return Response({"message": "Coupon applied successfully", "total_amount": total_amount})

        except Coupon.DoesNotExist:
            return Response({"error": "Coupon code does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        # Create checkout instance
        payment_method = validated_data.get('payment_method')
        checkout = Checkout.objects.create(
            user=user,
            order_id=str(uuid.uuid4()),
            total_amount=total_amount,
            payment_method=payment_method,
            shipping_address=validated_data.get('shipping_address'),
            contact_number=validated_data.get('contact_number'),
            payment_status='pending' if payment_method == 'online' else 'cod'
        )

        # Create CheckoutItem instances for each cart item
        for item in cart_items:
            CheckoutItem.objects.create(
                checkout=checkout,
                vendor=item.vendor,
                product_type=item.product_type,
                product_id=item.product_id,
                quantity=item.quantity,
                color=item.color,
                size=item.size,
                variant=item.variant,
                price=item.price,
                subtotal=item.price * item.quantity,
            )

        # Clear the cart items after checkout
        cart_items.delete()
        print(f"DEBUG: Cart items deleted: {cart_items.count()} remaining.")

        # Handle Razorpay payment if it's online
        if payment_method == 'online':
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                razorpay_order = client.order.create({
                    "amount": int(total_amount * 100),  # Convert to paisa
                    "currency": "INR",
                    "payment_capture": "1"
                })
                checkout.razorpay_order_id = razorpay_order['id']
                checkout.save()
                print(f"DEBUG: Razorpay order created: {checkout.razorpay_order_id}")
                return Response({
                    "razorpay_order_id": checkout.razorpay_order_id,
                    "amount": checkout.total_amount,
                    "currency": "INR",
                    "message": "Razorpay order created successfully"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"DEBUG: Razorpay error: {str(e)}")
                return Response({"error": "Failed to create Razorpay order."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"order_id": checkout.order_id, "message": "Order placed successfully!"}, status=status.HTTP_201_CREATED)


class CheckoutListView(generics.ListAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Checkout.objects.filter(user=self.request.user)


class CheckoutDetailView(generics.RetrieveAPIView):
    queryset = Checkout.objects.all()
    serializer_class = CheckoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Checkout.objects.filter(user=self.request.user)


class CancelOrderView(generics.UpdateAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Checkout.objects.filter(user=self.request.user, order_status="pending")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.order_status = "cancelled"
        instance.save()
        return Response({"message": "Order cancelled successfully."}, status=status.HTTP_200_OK)
    
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None
    
    

# Get Orders for Logged-in User
class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)\
            .select_related('checkout')\
            .prefetch_related('checkout__items')

    
#get single user order using order id
class UserOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'  
    lookup_url_kwarg = 'order_id'  

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)\
            .select_related('checkout')\
            .prefetch_related('checkout__items')

# Update Order Status (For Admin)
class UpdateOrderStatusView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id)
            new_status = request.data.get("order_status")
            if new_status in dict(Order.ORDER_STATUS_CHOICES).keys():
                order.order_status = new_status
                order.save()
                return Response({"message": f"Order {order_id} status updated to {new_status}"})
            else:
                return Response({"error": "Invalid status"}, status=400)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        

class AllorderviewAdmin(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    pagination_class =None

class VendorOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [VendorJWTAuthentication]

    def get(self, request):
        vendor = request.user  # Assuming vendor logs in to view their orders

        # Fetch orders that have items belonging to the vendor
        vendor_orders = Order.objects.filter(checkout__items__vendor=vendor).distinct()

        # Prefetch related data for better query optimization
        vendor_orders = vendor_orders.prefetch_related(
            'checkout__items'
        )

        order_data = []
        for order in vendor_orders:
            # Get all items in the order that belong to the vendor
            vendor_items = order.checkout.items.filter(vendor=vendor)

            order_data.append({
                "order_id": order.order_id,
                "user_name": order.user.name,
                "total_amount": order.total_amount,
                "final_amount": order.final_amount,
                "used_coupon": order.used_coupon,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "order_status": order.order_status,
                "shipping_address": order.shipping_address,
                "contact_number": order.contact_number,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
                "products": CheckoutItemSerializer(vendor_items, many=True).data  # Serialize only vendor-specific products
            })

        return Response(order_data)
    
class VendorOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [VendorJWTAuthentication]

    def get(self, request, order_id):
        vendor = request.user
        order = get_object_or_404(Order, order_id=order_id, checkout__items__vendor=vendor)
        vendor_items = order.checkout.items.filter(vendor=vendor)

        data = {
            "order_id": order.order_id,
            "user_name": order.user.name,
            "total_amount": order.total_amount,
            "final_amount": order.final_amount,
            "used_coupon": order.used_coupon,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "order_status": order.order_status,
            "shipping_address": order.shipping_address,
            "contact_number": order.contact_number,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "products": CheckoutItemSerializer(vendor_items, many=True).data
        }

        return Response(data)


from collections import defaultdict
from decimal import Decimal
from rest_framework.permissions import AllowAny

class GroupedCartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        cart_items = CartItem.objects.filter(cart__user=user)

        # Group by vendor
        grouped_data = {}
        for item in cart_items:
            vendor_id = str(item.vendor.id)
            if vendor_id not in grouped_data:
                grouped_data[vendor_id] = {
                    "vendor_id": item.vendor.id,
                    "vendor_name": item.vendor.business_name,
                    "vendor_logo": request.build_absolute_uri(item.vendor.store_logo.url) if item.vendor.store_logo else None,
                    "vendor_image": request.build_absolute_uri(item.vendor.display_image.url) if item.vendor.display_image else None,
                    "items": []
                }
            grouped_data[vendor_id]["items"].append(item)

        
        for group in grouped_data.values():
            group["item_count"] = len(group["items"])  
            group["items"] = CartItemSerializer(group["items"], many=True, context={'request': request}).data

        return Response(list(grouped_data.values()), status=status.HTTP_200_OK)



class VendorCartItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, vendor_id):
        user = request.user
        cart_items = CartItem.objects.filter(cart__user=user, vendor_id=vendor_id)

        if not cart_items.exists():
            return Response({"detail": "No items found for this vendor."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartItemSerializer(cart_items, many=True, context={'request': request})

        # Calculate total cart amount for this vendor
        total_amount = sum(item.quantity * float(item.price) for item in cart_items)

        return Response({
            "vendor_id": vendor_id,
            "final_total_amount": total_amount,
            "items": serializer.data
        }, status=status.HTTP_200_OK)
    


from coupon_tracking.models import UserCouponUsage
from django.db import transaction
import random
class VendorCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, vendor_id):
        user = request.user
        data = request.data

        # Validate required fields
        shipping_address_id = data.get('shipping_address_id')
        contact_number = data.get('contact_number')
        payment_method = data.get('payment_method', 'cod')
        coupon_code = data.get('coupon_code')

        if not shipping_address_id:
            return Response(
                {'error': 'Shipping address is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Start atomic transaction
            with transaction.atomic():
                # Lock relevant database rows
                address = Address.objects.select_for_update().get(
                    id=shipping_address_id,
                    user=user
                )
                vendor = Vendor.objects.select_for_update().get(id=vendor_id)
                cart = Cart.objects.select_for_update().get(user=user)
                cart_items = cart.items.filter(vendor=vendor).select_related('vendor')

                if not cart_items.exists():
                    return Response(
                        {'error': 'No items in cart for this vendor.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Calculate total
                total_amount = sum(item.price * item.quantity for item in cart_items)
                coupon = None
                coupon_discount = Decimal('0.00')

                # Apply coupon if provided
                if coupon_code:
                    coupon_result = self.validate_and_apply_coupon(
                        coupon_code, total_amount, user, vendor_id
                    )
                    if 'error' in coupon_result:
                        return Response(
                            {'error': coupon_result['error']},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    coupon = coupon_result['coupon']
                    coupon_discount = coupon_result['discount']

                final_amount = total_amount - coupon_discount
                final_amount = max(final_amount, Decimal('0.00'))

                # Generate order details
                order_id = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}-{user.id}"
                delivery_pin = str(random.randint(100000, 999999))

                # Create checkout record
                checkout = Checkout.objects.create(
                    user=user,
                    order_id=order_id,
                    total_amount=total_amount,
                    discount_amount=coupon_discount,
                    final_amount=final_amount,
                    payment_method=payment_method,
                    contact_number=contact_number or '',
                    shipping_address=address,
                    coupon=coupon,
                    coupon_code=coupon_code if coupon else None,
                    coupon_discount=coupon_discount
                )

                # Process each cart item
                product_details = []
                for item in cart_items:
                    # Create checkout item
                    CheckoutItem.objects.create(
                        checkout=checkout,
                        vendor=item.vendor,
                        product_type=item.product_type,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        color=item.color,
                        size=item.size,
                        variant=item.variant,
                        price=item.price,
                        subtotal=item.price * item.quantity,
                    )

                    # Record product details
                    product_details.append({
                        "product_id": item.product_id,
                        "variant": item.variant,
                        "quantity": item.quantity,
                        "color": item.color,
                        "size": item.size
                    })

                    # Reduce stock
                    try:
                        if item.product_type == 'grocery':
                            self.handle_grocery_stock_reduction(item)
                        elif item.product_type == 'clothing':
                            self.handle_clothing_stock_reduction(item)
                    except Exception as e:
                        return Response(
                            {'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # Create order
                order = Order.objects.create(
                    user=user,
                    checkout=checkout,
                    order_id=order_id,
                    total_amount=total_amount,
                    final_amount=final_amount,
                    payment_method=payment_method,
                    order_status='pending',
                    shipping_address=address,
                    contact_number=contact_number,
                    used_coupon=checkout.coupon_code,
                    delivery_pin=delivery_pin,
                    product_details=product_details
                )

                # Track coupon usage
                if coupon:
                    UserCouponUsage.objects.create(
                        coupon=coupon,
                        user=user,
                        checkout=checkout
                    )

                # Clear cart items
                cart_items.delete()

                # Handle payment
                if payment_method == 'online':
                    try:
                        client = razorpay.Client(
                            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                        )
                        razorpay_order = client.order.create({
                            "amount": int(final_amount * 100),
                            "currency": "INR",
                            "payment_capture": "1"
                        })
                        checkout.razorpay_order_id = razorpay_order['id']
                        checkout.save()
                    except Exception as e:
                        return Response(
                            {'error': f'Payment error: {str(e)}'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE
                        )

                return Response({
                    "order_id": order.order_id,
                    "final_amount": float(final_amount),
                    "payment_status": "pending",
                    "delivery_pin": delivery_pin
                }, status=status.HTTP_201_CREATED)

        except (Vendor.DoesNotExist, Address.DoesNotExist, Cart.DoesNotExist) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Checkout failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def handle_grocery_stock_reduction(self, item):
        """Atomic stock reduction for grocery items"""
        product = GroceryProducts.objects.select_for_update().get(id=item.product_id)

        if isinstance(product.weights, list):
            # Create new list to force JSON field update
            new_weights = []
            found = False
            for weight in product.weights:
                if weight['weight'] == item.variant:
                    if weight['quantity'] < item.quantity:
                        raise ValueError(f"Insufficient stock for {item.variant}")
                    new_weight = weight.copy()
                    new_weight['quantity'] = F('quantity') - item.quantity
                    new_weight['is_in_stock'] = new_weight['quantity'] > 0
                    found = True
                new_weights.append(new_weight)

            if not found:
                raise ValueError(f"Variant {item.variant} not found")

            # Update using bulk_update for better performance
            GroceryProducts.objects.filter(id=product.id).update(weights=new_weights)

        elif isinstance(product.weights, dict):
            variant_data = product.weights.get(item.variant)
            if not variant_data or variant_data['quantity'] < item.quantity:
                raise ValueError(f"Insufficient stock for {item.variant}")

            # Use F expression for atomic update
            GroceryProducts.objects.filter(id=product.id).update(
                weights={
                    **product.weights,
                    item.variant: {
                        'quantity': F(f'weights__{item.variant}__quantity') - item.quantity,
                        'is_in_stock': F(f'weights__{item.variant}__quantity') - item.quantity > 0,
                        'price': variant_data['price']
                    }
                }
            )

        else:
            raise ValueError("Invalid weight format")

    def handle_clothing_stock_reduction(self, item):
        """Atomic stock reduction for clothing items"""
        # Update relational data
        updated = ClothingSize.objects.filter(
            color__clothing_id=item.product_id,
            color__color_name=item.color,
            size=item.size
        ).update(stock=F('stock') - item.quantity)

        if updated == 0:
            raise ValueError("Size/color combination not found")

        # Verify stock didn't go negative
        size = ClothingSize.objects.get(
            color__clothing_id=item.product_id,
            color__color_name=item.color,
            size=item.size
        )
        if size.stock < 0:
            raise ValueError("Insufficient stock after reduction")

        # Update JSON representation
        clothing = Clothing.objects.get(id=item.product_id)
        for color in clothing.colors:
            if color['color_name'] == item.color:
                for size in color.get('sizes', []):
                    if size['size'] == item.size:
                        size['stock'] = size.stock  # From relational model
        clothing.save(update_fields=['colors'])

    def validate_and_apply_coupon(self, coupon_code, total_amount, user, vendor_id):
        """Validate and calculate coupon discount"""
        now = timezone.now()

        try:
            coupon = Coupon.objects.get(
                code=coupon_code,
                valid_from__lte=now,
                valid_to__gte=now,
                is_active=True
            )
        except Coupon.DoesNotExist:
            return {'error': 'Invalid or expired coupon code.'}

        # Vendor validation
        if coupon.vendor and coupon.vendor.id != int(vendor_id):
            return {'error': 'This coupon is not valid for this vendor.'}

        # Minimum order amount
        if coupon.min_order_amount and total_amount < coupon.min_order_amount:
            return {'error': f'Minimum order amount of {coupon.min_order_amount} required.'}

        # Usage limits
        if coupon.usage_limit == 1 and UserCouponUsage.objects.filter(
            coupon=coupon, user=user
        ).exists():
            return {'error': 'You have already used this coupon.'}

        # New customer restriction
        if coupon.is_new_customer and Order.objects.filter(user=user).exists():
            return {'error': 'This coupon is for new customers only.'}

        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount = (total_amount * coupon.discount_value) / 100
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:  # fixed amount
            discount = min(coupon.discount_value, total_amount)

        return {'coupon': coupon, 'discount': discount}