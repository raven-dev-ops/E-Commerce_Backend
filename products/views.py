from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from products.models import Product
from products.serializers import ProductSerializer
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django.http import Http404
import logging

class CustomProductPagination(PageNumberPagination):
    page_size = 100

class ProductViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ['product_name', 'description', 'tags', 'category']
    pagination_class = CustomProductPagination
    lookup_field = 'id'

    def get_queryset(self):
        queryset = Product.objects.all()
        # Logging all IDs that will be served in this queryset
        ids = [str(p.id) for p in queryset]
        logging.info(f"[ProductViewSet] Serving {len(ids)} products. Product IDs: {ids}")
        return queryset

    def get_object(self):
        pk = self.kwargs.get(self.lookup_field)
        logging.info(f"[ProductViewSet] Attempting to serve detail for Product id: {pk}")
        try:
            product = Product.objects.get(id=pk)
            logging.info(f"[ProductViewSet] Found Product with id: {pk}")
            return product
        except Product.DoesNotExist:
            logging.error(f"[ProductViewSet] Product with id {pk} not found")
            raise Http404
        except Exception as e:
            logging.error(f"[ProductViewSet] Error retrieving product: {e}")
            raise Http404

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
