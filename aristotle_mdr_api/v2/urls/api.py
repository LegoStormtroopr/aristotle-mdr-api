from django.conf.urls import include, url
from ..views import concepts, views, concepttypes
from rest_framework import routers

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register(r'metadata', concepts.ConceptViewSet)
router.register(r'types', concepttypes.ConceptTypeViewSet)
router.register(r'search', views.SearchViewSet, base_name="search")
router.register(r'ras', views.RegistrationAuthorityViewSet)
router.register(r'organizations', views.OrganizationViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
]