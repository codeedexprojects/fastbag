from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from fashion.models import *
from rest_framework import generics
from fashion.serializers import *
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework import status

class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser] 


class ApplyCouponView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        coupon_code = request.data.get('coupon_code')

        try:
            product = Clothing.objects.get(id=product_id)
        except Clothing.DoesNotExist:
            raise ValidationError("Product not found.")

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            raise ValidationError("Invalid coupon code.")

        try:
            discounted_price = product.apply_coupon(coupon, request.user)  
        except ValueError as e:
            raise ValidationError(str(e))

        return Response({
            "original_price": product.price,
            "discounted_price": discounted_price,
            "coupon_code": coupon.code
        })


class CouponUsageListView(generics.ListAPIView):

    serializer_class = CouponUsageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
 
        return CouponUsage.objects.filter(user=self.request.user)
    
class CouponUpdateView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Coupon.objects.all()
    serializer_class = CouponUpdateSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return super().get_queryset()
    
    