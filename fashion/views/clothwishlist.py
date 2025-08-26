from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from fashion.models import FashionWishlist, Clothing
from fashion.serializers import *
from fashion.models import *
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from vendors.authentication import VendorJWTAuthentication

class WishlistListCreateView(generics.ListCreateAPIView):
    pagination_class = None
    serializer_class = FashionWishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FashionWishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        wishlist_item = serializer.save(user=self.request.user)
        wishlist_item.cloth.is_wishlisted = True
        wishlist_item.cloth.save()

    def create(self, request, *args, **kwargs):
        user = request.user
        cloth_id = request.data.get('cloth')

        if FashionWishlist.objects.filter(user=user, cloth_id=cloth_id).exists():
            return Response(
                {
                    "status": False,
                    "message": "This item is already in your wishlist.",
                    "status_code": status.HTTP_400_BAD_REQUEST
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {
                "status": True,
                "message": "Item added to wishlist successfully.",
                "data": serializer.data,
                "status_code": status.HTTP_201_CREATED
            },
            status=status.HTTP_201_CREATED
        )



class WishlistDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, cloth_id):
        user = request.user
        try:
            wishlist_item = FashionWishlist.objects.get(user=user, cloth_id=cloth_id)
            cloth = wishlist_item.cloth
            wishlist_item.delete()

            if not FashionWishlist.objects.filter(cloth=cloth).exists():
                cloth.is_wishlisted = False
                cloth.save()

            return Response(
                {
                    "status": True,
                    "message": "Item removed from wishlist successfully.",
                    "status_code": status.HTTP_200_OK
                },
                status=status.HTTP_200_OK
            )
        except FashionWishlist.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Item not found in your wishlist.",
                    "status_code": status.HTTP_404_NOT_FOUND
                },
                status=status.HTTP_404_NOT_FOUND
            )



class FashionReviewListCreateView(generics.ListCreateAPIView):
    
    serializer_class = FashionReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cloth_id = self.request.query_params.get('cloth')
        if cloth_id:
            return FashionReview.objects.filter(cloth_id=cloth_id)
        return FashionReview.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        cloth_id = request.data.get('cloth')
        user = request.user

        if FashionReview.objects.filter(user=user, cloth_id=cloth_id).exists():
            return Response(
                {"detail": "You have already reviewed this item."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)
    
class ListFashionProductReviewsView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[VendorJWTAuthentication]
    def get(self, request, cloth_id):
        reviews = FashionReview.objects.filter(cloth_id=cloth_id)
        serializer = FashionReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class FashionReviewDeleteView(generics.DestroyAPIView):
    
    queryset = FashionReview.objects.all()
    serializer_class = FashionReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FashionReview.objects.filter(user=self.request.user)
    
class FashionReviewByClothIDView(generics.ListAPIView):
    serializer_class = FashionReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cloth_id = self.kwargs.get('cloth_id')
        return FashionReview.objects.filter(cloth_id=cloth_id).order_by('-created_at')
    
class FashionReportListCreateView(generics.ListCreateAPIView):
    
    serializer_class = FashionReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return FashionReport.objects.all()
        return FashionReport.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FashionReportUpdateView(generics.UpdateAPIView):
    
    queryset = FashionReport.objects.all()
    serializer_class = FashionReportSerializer
    permission_classes = [IsAdminUser]

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        is_resolved = request.data.get("is_resolved", None)

        if is_resolved is not None:
            instance.is_resolved = is_resolved
            instance.save()
            return Response({"detail": "Report status updated successfully."})
        return Response({"detail": "Invalid data provided."}, status=status.HTTP_400_BAD_REQUEST)

class FashionReportDeleteView(generics.DestroyAPIView):
   
    queryset = FashionReport.objects.all()
    serializer_class = FashionReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return FashionReport.objects.all()
        return FashionReport.objects.filter(user=self.request.user)