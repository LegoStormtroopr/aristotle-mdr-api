Aristotle-MDR API
=================

.. image:: https://travis-ci.org/aristotle-mdr/aristotle-mdr-api.svg?branch=master
    :target: https://travis-ci.org/aristotle-mdr/aristotle-mdr-api

.. image:: https://coveralls.io/repos/aristotle-mdr/aristotle-mdr-api/badge.svg
    :target: https://coveralls.io/r/aristotle-mdr/aristotle-mdr-api

The Aristotle-MDR API provides a self-documenting JSON API for retrieving content
from thean Aristotle-MeteData-Registry

Quick start
-----------

1. Add `aristotle_mdr_api` and `rest_framework`  to your INSTALLED_APPS setting::

        INSTALLED_APPS = (
            ...
            Your apps
            ...
        ) + aristotle_mdr_api.settings.REQUIRED_APPS

#. Add `SERIALIZATION_MODULES` and `REST_FRAMEWORK` to settings::

        SERIALIZATION_MODULES = { 'mdrjson' : 'aristotle_mdr_api.serializers.idjson' }
        REST_FRAMEWORK = aristotle_mdr_api.settings.REST_FRAMEWORK

#. Include the API URL definitions in your Django URLconf file ::

        url(r'^api/', include('aristotle_mdr_api.urls')),

#. Thats it!
