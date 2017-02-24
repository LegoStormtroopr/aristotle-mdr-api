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
from aristotle_mdr_api.serializers.base import Serializer, exclude_fields
from aristotle_mdr_api.filters import concept_backend

from rest_framework import viewsets

from aristotle_mdr_api.views.utils import (
    DescriptionStubSerializerMixin,
    MultiSerializerViewSetMixin,
    ConceptResultsPagination,
    UUIDLookupModelMixin,
    api_excluded_fields,
    get_api_fields,
)


standard_fields = ('uuid', 'concept_type','api_url','name','visibility_status','definition')
class ConceptSerializerBase(serializers.ModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(
        view_name='aristotle_mdr_api:_concept-detail',
        format='html',
        lookup_field='uuid'
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
    links = serializers.SerializerMethodField()
    statuses = serializers.SerializerMethodField()


    _serialised_object = None
    def get_serialized_object(self, instance):
        if not self._serialised_object:
            s = Serializer().serialize([instance])
            self._serialised_object = s[0]
        return self._serialised_object
        
    class Meta:
        model = models._concept
        fields = standard_fields+('fields','statuses','ids','slots', 'links')

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
        ids = [
            {
                'namespace': {
                    'naming_authority': scoped_id.namespace.naming_authority.uuid,
                    'shorthand_prefix': scoped_id.namespace.shorthand_prefix,
                },
                'id': scoped_id.identifier,
                'version': scoped_id.version
            }
            for scoped_id in instance.identifiers.all()
        ]
        return ids #obj.get('slots',[])

    def get_slots(self, instance):
        obj = self.get_serialized_object(instance)
        slots = [
            {'name': slot.name, 'type': slot.type, 'value': slot.value }
            for slot in instance.slots.all()
        ]
        return slots #obj.get('slots',[])

    def get_links(self, instance):
        obj = self.get_serialized_object(instance)
        from aristotle_mdr.contrib.links import models as link_models
        obj_links = link_models.Link.objects.filter(linkend__concept=instance).all().distinct()

        links = [
            [{
                'relation': {
                    'uuid': link.relation.uuid,
                    'name': link.relation.name,  # Optional!
                },
                'members': {   'concept': {
                        'uuid': linkend.concept.uuid,
                        'name': linkend.concept.name,  # Optional!
                    },
                    'role': {
                        'ordinal': linkend.role.ordinal,
                        'name': linkend.role.name,
                        'definition': linkend.role.definition  # Optional!
                    }
                }
            }
                for linkend in link.linkend_set.all()
            ]
            for link in obj_links
        ]
        return links

    def get_statuses(self, instance):
        obj = self.get_serialized_object(instance)
        stats = [
            {
                "changeDetails": status.changeDetails,
                "until_date": status.until_date,
                "registration_authority": status.registrationAuthority.uuid,
                "state": status.state,
                "state_meaning": status.get_state_display(),
                "registrationDate": status.registrationDate
            }
            for status in instance.current_statuses()
        ]

        return stats
        # return obj.get('statuses',[])


class ConceptViewSet(UUIDLookupModelMixin, MultiSerializerViewSetMixin):
    #mixins.RetrieveModelMixin,
                    #mixins.UpdateModelMixin,
                    
                    #viewsets.ModelViewSet):
    __doc__ = """
    Provides access to a paginated list of concepts within the fields:

        %s

    A single concept can be retrieved by appending the `uuid` for that
    item to the URL, giving access to the fields:

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
    filter_backends = (concept_backend.ConceptFilterBackend,)
    filter_class = concept_backend.ConceptFilter


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
        queryset = super(ConceptViewSet,self).get_queryset()
        concepttype = self.request.query_params.get('type', None)
        if concepttype is not None:
            ct = concepttype.lower().split(":",1)
            if len(ct) == 2:
                app,model = ct
                queryset = ContentType.objects.get(app_label=app,model=model).model_class().objects.all()
            else:
                model = concepttype
                queryset = ContentType.objects.get(model=model).model_class().objects.all()

            # superseded_by_id = self.request.query_params.get('superseded_by', None)
            # if superseded_by_id is not None:
            #     queryset = queryset.filter(superseded_by=superseded_by_id)
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


    def check_object_permissions(self, request, obj):
        item = obj.item
        if not perms.user_can_view(request.user, item):
            raise PermissionDenied
        else:
            return obj

    def get_object(self):
        item = super(ConceptViewSet,self).get_object().item
        if not perms.user_can_view(self.request.user, item):
            raise PermissionDenied
        else:
            return item
