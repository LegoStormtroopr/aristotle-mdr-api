from django.conf.urls import include, url
from .views import concepts, views, concepttypes
from rest_framework import routers
from rest_framework.schemas import SchemaGenerator, get_schema_view
schema_view = get_schema_view(title="Aristotle Concepts API")

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register(r'concepts', concepts.ConceptViewSet)
router.register(r'types', concepttypes.ConceptTypeViewSet)
router.register(r'search', views.SearchViewSet, base_name="search")
router.register(r'ras', views.RegistrationAuthorityViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url('^schemas', schema_view),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
]
