from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

from django.utils.module_loading import import_string
from aristotle_mdr.utils import fetch_aristotle_settings


class About(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        
        settings = fetch_aristotle_settings()

        about = {
            'name': settings['SITE_NAME'],
            'description': settings['SITE_DESCRIPTION'],
            'version': "1.6",
            'installed_apps': [],
            'aristotle_mdr' : {
                'version': import_string("aristotle_mdr.__version__"),
            }
        }
        return Response(about)
