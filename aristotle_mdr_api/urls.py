from django.conf.urls import include, url
from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view
from django.utils.module_loading import import_string

import re

API_TITLE = 'Aristotle MDR API'
API_DESCRIPTION = """
---

The Aristotle Metadata Registry API is a standardised way to access metadata through a consistent
machine-readable interface.

"""

def version_schema(*args, **kwargs):
    version = kwargs.pop('version')
    if version:
        patterns = import_string('aristotle_mdr_api.%s.urls.urlpatterns' % version)
    else:
        patterns = []

    return get_swagger_view(
            title='Aristotle API %s' % version,
            patterns=patterns
        )(*args)


urlpatterns = [
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^docs/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),

    url(r'^(?P<version>(v1|v2|v3)?)/schemas/', version_schema),
    url(r'^schemas/', get_swagger_view(title='Aristotle API')),

    url(r'^v1/', include('aristotle_mdr_api.v1.urls', namespace='aristotle_mdr_api.v1')),
    url(r'^v2/', include('aristotle_mdr_api.v2.urls', namespace='aristotle_mdr_api.v2')),
    url(r'^v3/', include('aristotle_mdr_api.v3.urls', namespace='aristotle_mdr_api.v3')),
    # url(r'^edge/', include('aristotle_mdr_api.v3.urls', namespace='aristotle_mdr_api.v3')),
]
