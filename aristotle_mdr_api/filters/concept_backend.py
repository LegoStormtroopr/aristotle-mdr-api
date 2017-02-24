from django_filters.rest_framework import DjangoFilterBackend, FilterSet
import django_filters
from aristotle_mdr import models as MDR

ACCEPTABLE_FORMATS = ['%Y-%m-%d'] #,       # '25-10-2006'
                    #   '%d/%m/%Y',       # '25/10/2006'
                    #   '%d/%m/%y']       # '25/10/06'
                      # Add your own at will, but be mindful of collisions.


class ConceptFilterBackend(DjangoFilterBackend):
    pass

class ConceptFilter(FilterSet):
    superseded_by = django_filters.UUIDFilter(
        name='superseded_by__uuid',
    )

    class Meta:
        model = MDR._concept
        fields = {
            # 'id': ['exact',],
            'modified': ['exact', 'gte', 'lte'],
            'created': ['exact', 'gte', 'lte'],
        }
        #strict=django_filters.STRICTNESS.RAISE_VALIDATION_ERROR
