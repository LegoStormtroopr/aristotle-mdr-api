from django.conf.urls import include, url
from aristotle_mdr_api.views import concepts, views, concepttypes
from rest_framework import routers
from rest_framework.schemas import SchemaGenerator, get_schema_view
schema_view = get_schema_view(title="Aristotle Concepts API")

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register(r'metadata', concepts.ConceptViewSet)
router.register(r'types', concepttypes.ConceptTypeViewSet)
router.register(r'search', views.SearchViewSet, base_name="search")
router.register(r'ras', views.RegistrationAuthorityViewSet)
# router.register(r'organizations', views.OrganizationViewSet)

from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='Aristotle API')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^schemas/', schema_view),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
]