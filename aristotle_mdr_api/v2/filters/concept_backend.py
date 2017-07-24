from django_filters.rest_framework import FilterSet
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from aristotle_mdr import models as MDR
from django.contrib.contenttypes.models import ContentType


class ConceptFilterBackend(DjangoFilterBackend):
    pass


class ConceptFilter(django_filters.rest_framework.FilterSet):
    superseded_by = django_filters.UUIDFilter(
        name='superseded_by__uuid',
        label="Superseded by"
    )
    identifier = django_filters.CharFilter(
        label="Identifier",
        method='identifier_filter',
        help_text = (
            'Used to filter concept based on the requested identifier. '
            'Identifiers must be of the type `identifier`, `namespace::identifier` '
            'or `namespace::identifier::version.` '
            'Multiple metadata items may be returned if items have the same identifier '
            'but different versions or namespaces.'
        )
    )
    type = django_filters.CharFilter(
        method='concept_type_filter',
        help_text = (
            'An `app_label:concept_type` pair that filters results to '
            'only return concepts of the specified type.\n\n'
            'A list of models can be accessed at `/api/types/`, filterable '
            'models are limited to the values of the `model` on each item returned '
            'from the list.'

        )
    )
    modified = django_filters.DateFromToRangeFilter(
        # lookup_expr=['exact', 'gte', 'lte'],
        help_text = (
            'An `app_label:concept_type` pair that filters results to '
            'only return concepts of the specified type.\n\n'
            'A list of models can be accessed at `/api/types/`, filterable '
            'models are limited to the values of the `model` on each item returned '
            'from the list.'

        )
    )
    class Meta:
        model = MDR._concept
        fields = {
            'name': ['icontains',],
            'uuid': ['exact',],
            # 'modified': ['exact', 'gte', 'lte'],
            'created': ['exact', 'gte', 'lte'],
            'type': ['exact']
        }
        strict = django_filters.STRICTNESS.RAISE_VALIDATION_ERROR

    def identifier_filter(self, queryset, name, value):
        # construct the full lookup expression.
        args = value.split('::')
        if len(args) == 1:
            kwargs = {'identifiers__identifier': args[0]}
        if len(args) == 2:
            kwargs = {'identifiers__identifier': args[0]}
        elif len(args) == 3:
            kwargs = dict([
                ('identifiers__%s'%k, v)
                for k, v in 
                zip(
                    ['namespace__shorthand_prefix', 'identifier', 'version'],
                    args
                )
                if v
            ])

        return queryset.filter(**kwargs)

    def concept_type_filter(self, queryset, name, value):
        """
        dsfgikjsfoiksdhfksdgfsldkf
        """
        # This requires overriding the queryset model whcih can be done here
        # This is done in concepts.
        # ct = value.lower().split(":",1)
        # if len(ct) == 2:
        #     app,model = ct
        #     concept_type = ContentType.objects.get(app_label=app,model=model).model_class()
        # else:
        #     model = concepttype
        #     concept_type = ContentType.objects.get(model=model).model_class()

        # queryset.model = concept_type
        # queryset.query.model = concept_type
        # queryset = queryset._clone()

        return queryset
