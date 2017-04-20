from django.conf.urls import include, url
from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='Aristotle API')

API_TITLE = 'Aristotle MDR API'
API_DESCRIPTION = """
---

The Aristotle Metadata Registry API is a standardised way to access metadata through a consistent
machine-readable interface.

"""

urlpatterns = [
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^docs/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),
    # url(r'^schemas/', schema_view),

    url(r'^v1/', include('aristotle_mdr_api.v1.urls', namespace='aristotle_mdr_api.v1')),
    url(r'^v2/', include('aristotle_mdr_api.v2.urls', namespace='aristotle_mdr_api.v2')),
]
