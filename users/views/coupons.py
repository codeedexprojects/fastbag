from rest_framework import generics
from rest_framework.permissions import AllowAny,IsAuthenticated
from users.models import Coupon
from users.serializers import CouponSerializer
from vendors.models import Vendor
from rest_framework.views import APIView
from rest_framework.response import Response

class CouponCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_superuser:
            vendor = None
            print(f"Admin User: {request.user}")
        else:
            try:
                vendor = Vendor.objects.get(id=request.user.id)
            except Vendor.DoesNotExist:
                return Response({"error": "Vendor not found."}, status=404)

        serializer = CouponSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(vendor=vendor, created_by=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class CouponRetrieveAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'

class CouponListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_superuser or user.is_staff:
            coupons = Coupon.objects.all()
        else:
            try:
                vendor = Vendor.objects.get(id=user.id)
                coupons = Coupon.objects.filter(vendor=vendor)
            except Vendor.DoesNotExist:
                return Response({"error": "Vendor not found."}, status=404)

        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)
