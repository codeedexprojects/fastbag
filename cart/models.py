from django.db import models
from django.contrib.auth import get_user_model
from foodproduct.models import *
from groceryproducts.models import *
from fashion.models import *
from vendors.models import *
from decimal import Decimal


User = get_user_model()

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='cart_items')
    product_type = models.CharField(max_length=20, choices=[('clothing', 'Clothing'), ('dish', 'Dish'), ('grocery', 'Grocery')])
    product_id = models.PositiveIntegerField()  
    quantity = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=50, null=True, blank=True)  
    size = models.CharField(max_length=10, null=True, blank=True)  
    variant = models.CharField(max_length=50, null=True, blank=True)  
    price = models.DecimalField(max_digits=10, decimal_places=2)  

    def save(self, *args, **kwargs):
        if self.product_type == 'clothing':
            product = Clothing.objects.get(id=self.product_id)
            if self.color and self.size:
                color_idx = next((i for i, c in enumerate(product.colors) if c['color_name'] == self.color), None)
                if color_idx is not None:
                    size_idx = next((i for i, s in enumerate(product.colors[color_idx]['sizes']) if s['size'] == self.size), None)
                    if size_idx is not None:
                        self.price = product.get_variant_offer_price(color_idx, size_idx)
        elif self.product_type == 'dish':
            product = Dish.objects.get(id=self.product_id)
            self.price = product.get_price_for_variant(self.variant) if self.variant else product.offer_price or product.price
        elif self.product_type == 'grocery':
            product = GroceryProducts.objects.get(id=self.product_id)
            self.price = product.get_price_for_weight(self.variant) if self.variant else product.offer_price or product.price
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_type} - {self.product_id} ({self.quantity})"


User = get_user_model()

class Checkout(models.Model):
    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("out for delivery", "Out for Delivery"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("return", "Return"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=50, unique=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Before discount
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')

    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="shipping_address", null=True, blank=True)
    contact_number = models.CharField(max_length=15)

    coupon = models.ForeignKey('users.Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='checkouts_used')
    coupon_code = models.CharField(max_length=50, blank=True, null=True)  # Stored for backup or reporting
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.final_amount = self.total_amount - self.coupon_discount
        self.save()

    def apply_coupon(self, coupon):
        """Applies a coupon and calculates discount."""
        if coupon:
            if coupon.discount_type == 'percentage':
                discount = (self.total_amount * coupon.discount_value) / 100
                if coupon.max_discount:
                    discount = min(discount, coupon.max_discount)
            else:
                discount = coupon.discount_value

            # Ensure minimum order amount is met
            if coupon.min_order_amount and self.total_amount < coupon.min_order_amount:
                return  # Do not apply

            self.coupon = coupon
            self.coupon_code = coupon.code
            self.coupon_discount = discount
            self.final_amount = self.total_amount - discount
            self.save()

    def __str__(self):
        return f"Order {self.order_id} - {self.user} - ₹{self.final_amount}"



class CheckoutItem(models.Model):
    checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name='items')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='order_items')
    product_type = models.CharField(max_length=20, choices=[('clothing', 'Clothing'), ('dish', 'Dish'), ('grocery', 'Grocery')])
    product_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=10, null=True, blank=True)
    variant = models.CharField(max_length=50, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
        self.checkout.calculate_total()  

    def __str__(self):
        return f"Order {self.checkout.order_id} - {self.product_type} ({self.quantity})"
    
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("out for delivery", "Out for Delivery"), 
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("return", "Return"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    checkout = models.OneToOneField(Checkout, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)  
    used_coupon = models.CharField(max_length=100, blank=True, null=True)  
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    # billing_address = models.TextField()
    contact_number = models.CharField(max_length=15)
    delivery_pin = models.CharField(max_length=6, blank=True, null=True)
    product_details = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"
