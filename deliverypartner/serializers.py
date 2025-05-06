from rest_framework import serializers
from deliverypartner.models import DeliveryBoy

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