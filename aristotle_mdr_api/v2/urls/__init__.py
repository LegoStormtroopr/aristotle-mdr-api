from django.conf.urls import include, url
from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view
# schema_view = get_swagger_view(title="Aristotle Concepts API", url='/api/v2')

API_TITLE = 'Aristotle MDR API v2'
API_DESCRIPTION = """
---

The Aristotle Metadata Registry API is a standardised way to access metadata through a consistent
machine-readable interface.

"""

# schema_view = get_swagger_view(title='Aristotle API v2',
#     patterns=urlpatterns
# )

urlpatterns = [
    url(r'^docs/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),
    url(r'^', include('aristotle_mdr_api.v2.urls.api', app_name="aristotle_mdr_api", namespace="aristotle_mdr_api.v2")),
]
