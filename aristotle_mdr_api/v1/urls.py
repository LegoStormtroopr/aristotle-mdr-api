from django.conf.urls import include, url
from . import views
from rest_framework import routers

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register(r'concepts', views.ConceptViewSet)
router.register(r'types', views.ConceptTypeViewSet)
router.register(r'search', views.SearchViewSet, base_name="search")
router.register(r'ras', views.RegistrationAuthorityViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
