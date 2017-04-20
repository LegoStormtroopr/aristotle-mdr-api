REQUIRED_APPS = (
    'aristotle_mdr_api',
    'rest_framework',
    'rest_framework_swagger',
    'django_filters',
)

SERIALIZATION_MODULES = { 'mdrjson' : 'aristotle_mdr_api.serializers.idjson' }

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}
