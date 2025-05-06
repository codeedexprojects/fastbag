from rest_framework import serializers
from deliverypartner.models import DeliveryBoy,OrderAssign,DeliveryNotification

class DeliveryBoySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryBoy
        fields = [
            'id', 
            'name', 
            'mobile_number', 
            'email', 
            'photo', 
            'address', 
            'vehicle_type', 
            'vehicle_number', 
            'gender', 
            'dob', 
            'is_active', 
            'aadhar_card_image', 
            'driving_license_image', 
            'created_at', 
            'updated_at'
        ]

    def validate_mobile_number(self, value):
        # Add any custom validation for mobile number here
        if len(value) < 10:
            raise serializers.ValidationError("Mobile number must be at least 10 digits.")
        return value

class OTPLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

from cart.serializers import OrderSerializer
class OrderAssignSerializer(serializers.ModelSerializer):
    order_details = OrderSerializer(source='order', read_only=True)
    delivery_boy_details = DeliveryBoySerializer(source='delivery_boy', read_only=True)

    class Meta:
        model = OrderAssign
        fields = ['id','order', 'delivery_boy', 'assigned_at', 'status', 'order_details', 'delivery_boy_details']
        extra_kwargs = {
            'order': {'write_only': True},
            'delivery_boy': {'write_only': True}
        }


class DeliveryNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryNotification
        fields = ['id', 'message', 'created_at', 'is_read']

class AcceptedOrderSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source='order.order_id')
    delivery_boy_name = serializers.CharField(source='accepted_by.name', read_only=True)
    vendor_name = serializers.CharField(source='order.checkout.vendor.name', read_only=True)  # assuming a vendor exists in checkout

    class Meta:
        model = OrderAssign
        fields = ['id', 'order_id', 'delivery_boy_name', 'vendor_name', 'status', 'assigned_at']

class OrderAssignStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAssign
        fields = ['status']