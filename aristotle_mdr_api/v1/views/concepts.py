from django.http import Http404
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from rest_framework import serializers, status, mixins
from rest_framework.views  import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route

from django.forms import model_to_dict
from aristotle_mdr import models, perms
from aristotle_mdr.forms.search import PermissionSearchQuerySet
from ..serializers.base import Serializer, exclude_fields

from rest_framework import viewsets

from .utils import (
    DescriptionStubSerializerMixin,
    MultiSerializerViewSetMixin,
    ConceptResultsPagination,
    api_excluded_fields,
    get_api_fields
)


standard_fields = ('id','concept_type','api_url','name','visibility_status','definition')
class ConceptSerializerBase(serializers.ModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(
        view_name='aristotle_mdr_api.v1:_concept-detail',
        format='html'
    )
    concept_type = serializers.SerializerMethodField()
    definition = serializers.SerializerMethodField()
    visibility_status = serializers.SerializerMethodField()

    class Meta:
        model = models._concept
        fields = standard_fields
    def get_concept_type(self,instance):
        item = instance.item
        out = {"app":item._meta.app_label,'model':item._meta.model_name}
        return out
    def get_visibility_status(self,instance):
        out = {"public":instance.is_public(),'locked':instance.is_locked()}
        return out
    def get_definition(self,instance):
        return instance.definition

class ConceptListSerializer(DescriptionStubSerializerMixin,ConceptSerializerBase):
    pass

class ConceptDetailSerializer(ConceptSerializerBase):
    fields = serializers.SerializerMethodField('get_extra_fields')
    ids = serializers.SerializerMethodField('get_identifiers')
    slots = serializers.SerializerMethodField()
    statuses = serializers.SerializerMethodField()


    _serialised_object = None
    def get_serialized_object(self, instance):
        if not self._serialised_object:
            s = Serializer().serialize([instance])
            self._serialised_object = s[0]
        return self._serialised_object
        
    class Meta:
        model = models._concept
        fields = standard_fields+('fields','statuses','ids','slots')

    def get_extra_fields(self, instance):
        # concept_dict = model_to_dict(instance,
        #     fields=[field.name for field in get_api_fields(instance)],
        #     exclude=api_excluded_fields
        #     )
        # return concept_dict
        obj = self.get_serialized_object(instance)
        return obj.get('fields',[])

    def get_identifiers(self, instance):
        obj = self.get_serialized_object(instance)
        return obj.get('ids',[])

    def get_slots(self, instance):
        obj = self.get_serialized_object(instance)
        return obj.get('slots',[])

    def get_statuses(self, instance):
        obj = self.get_serialized_object(instance)
        return instance.current_statuses().values(*exclude_fields(models.Status, 'id'))
        #return obj.get('slots',[])


class ConceptViewSet(MultiSerializerViewSetMixin):
    #mixins.RetrieveModelMixin,
                    #mixins.UpdateModelMixin,
                    
                    #viewsets.ModelViewSet):
    __doc__ = """
    Provides access to a paginated list of concepts within the fields:

        %s

    A single concept can be retrieved but appending the `id` for that
    authority to the URL, giving access to the fields:

        %s

    Accepts the following GET parameters:

     * `type` (string) : restricts returned items to those of the given model.

        A list of models can be accessed at `/api/types/`, filterable
        models are limited to the values of the `model` on each item returned
        from the list.

        Available models are also available in the `concept_type.model`
        attribute for a particular concept from the items in this list.

    * `is_public` (boolean) : restricts returned items to those which are publicly visible/private (True/False)

    * `is_locked` (boolean) : restricts returned items to those which are locked/unlocked (True/False)

    The following options can only be used if `type` is set to a valid concept type.

     * `superseded_by` (integer) : restricts returned items to those that are
        superseded by the concept with an id that matches the given value.

     * `is_superseded` (boolean) : restricts returned items to those that are
        superseded by any other concept.

        Note: due to database restrictions it is not possible to restrict to only
        concepts that supersede another concepts.

    ---
    """%(ConceptListSerializer.Meta.fields,ConceptDetailSerializer.Meta.fields)
    queryset = models._concept.objects.all()
    serializer_class = ConceptListSerializer
    pagination_class = ConceptResultsPagination

    serializers = {
        'default':  ConceptDetailSerializer,
        'list':    ConceptListSerializer,
        'detail':  ConceptDetailSerializer,
    }

    def get_queryset(self):
        """
        Possible arguments include:

        type (string) : restricts to a particular concept type, eg. dataelement

        """
        queryset = self.queryset
        concepttype = self.request.query_params.get('type', None)
        if concepttype is not None:
            ct = concepttype.lower().split(":",1)
            if len(ct) == 2:
                app,model = ct
                queryset = ContentType.objects.get(app_label=app,model=model).model_class().objects.all()
            else:
                model = concepttype
                queryset = ContentType.objects.get(model=model).model_class().objects.all()

            superseded_by_id = self.request.query_params.get('superseded_by', None)
            if superseded_by_id is not None:
                queryset = queryset.filter(superseded_by=superseded_by_id)
            is_superseded = self.request.query_params.get('is_superseded', False)
            if is_superseded:
                queryset = queryset.filter(superseded_by__isnull=False)

        locked = self.request.query_params.get('is_locked', None)
        if locked is not None:
            locked = locked not in ["False","0","F"]
            queryset = queryset.filter(_is_locked=locked)
        public = self.request.query_params.get('is_public', None)
        if public is not None:
            public = public not in ["False","0","F"]
            queryset = queryset.filter(_is_public=public)


        return queryset.visible(self.request.user)

    def get_object(self):
        item = super(ConceptViewSet,self).get_object()
        request = self.request
        item = item.item
        if not perms.user_can_view(request.user, item):
            raise PermissionDenied
        else:
            return item
