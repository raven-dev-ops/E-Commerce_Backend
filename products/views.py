# products/views.py

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from products.models import Product
from products.filters import ProductFilter
from products.serializers import ProductSerializer
from bson.objectid import ObjectId
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django.http import Http404

class CustomProductPagination(PageNumberPagination):
    page_size = 10

class ProductViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['product_name', 'description', 'tags', 'category']
    pagination_class = CustomProductPagination

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            return Product.objects.get(id=ObjectId(pk))
        except Product.DoesNotExist:
            raise Http404
        except Exception as e:
            # Optional: log or handle invalid ObjectId errors
            raise Http404

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
