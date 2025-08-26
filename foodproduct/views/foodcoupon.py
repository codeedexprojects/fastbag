from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from foodproduct.models import *
from rest_framework import generics
from foodproduct.serializers import *
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework import status

class FoodCouponListCreateView(generics.ListCreateAPIView):
    queryset = FoodCoupon.objects.all()
    serializer_class = FoodCouponSerializer
    permission_classes = [IsAdminUser] 


class FoodApplyCouponView(APIView):

    permission_classes = [IsAuthenticated] 

    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        coupon_code = request.data.get('coupon_code')

        # Validate the product
        try:
            product = Dish.objects.get(id=product_id)
        except Dish.DoesNotExist:
            raise ValidationError("Product not found.")

        # Validate the coupon
        try:
            coupon = FoodCoupon.objects.get(code=coupon_code)
        except FoodCoupon.DoesNotExist:
            raise ValidationError("Invalid coupon code.")

        # Apply the coupon
        try:
            discounted_price = product.apply_coupon(coupon, request.user)  
        except ValueError as e:
            raise ValidationError(str(e))

        # Return the response
        return Response({
            "original_price": product.price,
            "discounted_price": discounted_price,
            "coupon_code": coupon.code
        })


class FoodCouponUsageListView(generics.ListAPIView):

    serializer_class = FoodCouponUsageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return FoodCouponUsage.objects.filter(user=self.request.user)
    
class FoodCouponUpdateView(generics.RetrieveUpdateDestroyAPIView):

    queryset = FoodCoupon.objects.all()
    serializer_class = FoodCouponUpdateSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):

        return super().get_queryset()
    
    