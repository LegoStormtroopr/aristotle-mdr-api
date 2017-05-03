"""
A Python "serializer". Doesn't do much serializing per se -- just converts to
and from basic Python data types (lists, dicts, strings, etc.). Useful as a basis for
other serializers.
"""
from __future__ import unicode_literals

from collections import OrderedDict

from django.apps import apps
from django.conf import settings
from django.core.serializers import base
from django.db import DEFAULT_DB_ALIAS, models
from django.utils import six
from django.utils.encoding import force_text, is_protected_type
from django.core.serializers.python import _get_model
from django.core.serializers.python import Serializer as PySerializer
from aristotle_mdr.models import _concept
from django.core.serializers.json import Serializer as JSONSerializer

excluded_fields = [
        "workgroup",
        "submitter",
    ]

def exclude_fields(obj,excludes):
    return [n.name for n in obj._meta.get_fields() if n.name not in excludes]

class Serializer(PySerializer):
    """
    Serializes a QuerySet to basic Python objects.
    """

    internal_use_only = True
    use_aristotle_ids = False

    def start_serialization(self):
        self._current = None
        self.objects = []

    def end_serialization(self):
        pass

    def start_object(self, obj):
        self._current = OrderedDict()

    def end_object(self, obj):
        self.objects.append(self.get_dump_object(obj))
        self._current = None

    def get_dump_object(self, obj):
        data = OrderedDict([('model', force_text(obj._meta))])
        if not self.use_natural_primary_keys or not hasattr(obj, 'natural_key'):
            data["pk"] = force_text(obj._get_pk_val(), strings_only=True)
        data['fields'] = self._current
        return data

    def handle_field(self, obj, field):
        value = field.value_from_object(obj)
        # Protected types (i.e., primitives like None, numbers, dates,
        # and Decimals) are passed through as is. All other values are
        # converted to string first.
        if is_protected_type(value):
            self._current[field.name] = value
        else:
            self._current[field.name] = field.value_to_string(obj)

    def handle_fk_field(self, obj, field):
        #if self.use_aristotle_ids and hasattr(related, 'identifiers') and related.identifiers.count() > 0 :
        #if True: # and hasattr(related, 'identifiers') and related.identifiers.count() > 0 :
        foreign_model = field.rel.to  # change to field.remote_field.model for django >= 1.9
        if foreign_model and issubclass(foreign_model, _concept):
            value = []
            # print field.get_attname()
            if getattr(obj, field.get_attname()) is not None:
                value.append({
                        "namespace": "#pk",
                        "identifier": getattr(obj, field.get_attname()),
                        "version": None
                })

            if hasattr(foreign_model, 'identifiers'):
                related = getattr(obj, field.name)
                #print obj.name, field.name, related
                if related is not None:
                    value += [
                        {
                            "namespace": scopedid.namespace.shorthand_prefix,
                            "identifier": scopedid.identifier,
                            "version": scopedid.version,
                        }
                        for scopedid in related.identifiers.all()
                    ]
            
            
        elif self.use_natural_foreign_keys and hasattr(field.remote_field.model, 'natural_key'):
            related = getattr(obj, field.name)
            if related:
                value = related.natural_key()
            else:
                value = None
        else:
            value = getattr(obj, field.get_attname())
            if not is_protected_type(value):
                value = field.value_to_string(obj)
        self._current[field.name] = value

    def handle_m2m_field(self, obj, field):
        foreign_model = field.rel  # change to field.remote_field.model for django >= 1.9
        if foreign_model.through._meta.auto_created:
            if self.use_natural_foreign_keys and hasattr(foreign_model.model, 'natural_key'):
                def m2m_value(value):
                    return value.natural_key()
            else:
                def m2m_value(value):
                    return force_text(value._get_pk_val(), strings_only=True)
            self._current[field.name] = [
                m2m_value(related) for related in getattr(obj, field.name).iterator()
            ]
        elif hasattr(obj, 'serialize_weak_entities') and field.name in dict(obj.serialize_weak_entities).keys():
            weak_field = dict(obj.serialize_weak_entities).get(field.name)
            foreign_model = getattr(obj.__class__, weak_field).rel.related_model
            self._current[field.name] = [
                related for related in getattr(obj, weak_field).all().values(*exclude_fields(foreign_model, 'id'))
            ]

    def getvalue(self):
        return self.objects

    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.pop("stream", six.StringIO())
        self.selected_fields = options.pop("fields", None)
        self.use_natural_keys = options.pop("use_natural_keys", False)
        if self.use_natural_keys:
            warnings.warn("``use_natural_keys`` is deprecated; use ``use_natural_foreign_keys`` instead.",
                RemovedInDjango19Warning)
        self.use_natural_foreign_keys = options.pop('use_natural_foreign_keys', False) or self.use_natural_keys
        self.use_natural_primary_keys = options.pop('use_natural_primary_keys', False)

        self.start_serialization()
        self.first = True
        for obj in queryset:
            self.start_object(obj)
            # Use the concrete parent class' _meta instead of the object's _meta
            # This is to avoid local_fields problems for proxy models. Refs #17717.
            concrete_model = obj #._meta.concrete_model
            for field in obj._meta.fields: # concrete_model._meta.local_fields:
                if field.name.startswith('_') or field.name in excluded_fields:
                    # Skip cached / protected fields
                    continue

                if field.serialize:
                    if field.rel is None:
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_field(obj, field)
                    else:
                        if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                            self.handle_fk_field(obj, field)
            for field in concrete_model._meta.many_to_many:
                if field.serialize:
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_m2m_field(obj, field)
            self.end_object(obj)
            if self.first:
                self.first = False
        self.end_serialization()
        return self.getvalue()


def Deserializer(object_list, **options):
    """
    Deserialize simple Python objects back into Django ORM instances.

    It's expected that you pass the Python objects themselves (instead of a
    stream or a string) to the constructor
    """
    db = options.pop('using', DEFAULT_DB_ALIAS)
    ignore = options.pop('ignorenonexistent', False)
    field_names_cache = {}  # Model: <list of field_names>

    for d in object_list:
        # Look up the model and starting build a dict of data for it.
        try:
            Model = _get_model(d["model"])
        except base.DeserializationError:
            if ignore:
                continue
            else:
                raise
        data = {}
        if 'pk' in d:
            try:
                data[Model._meta.pk.attname] = Model._meta.pk.to_python(d.get('pk'))
            except Exception as e:
                raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), None)
        m2m_data = {}

        if Model not in field_names_cache:
            field_names_cache[Model] = {f.name for f in Model._meta.get_fields()}
        field_names = field_names_cache[Model]

        # Handle each field
        for (field_name, field_value) in six.iteritems(d["fields"]):

            if ignore and field_name not in field_names:
                # skip fields no longer on model
                continue

            if isinstance(field_value, str):
                field_value = force_text(
                    field_value, options.get("encoding", settings.DEFAULT_CHARSET), strings_only=True
                )

            field = Model._meta.get_field(field_name)

            # Handle M2M relations
            if field.remote_field and isinstance(field.remote_field, models.ManyToManyRel):
                model = field.remote_field.model
                if hasattr(model._default_manager, 'get_by_natural_key'):
                    def m2m_convert(value):
                        if hasattr(value, '__iter__') and not isinstance(value, six.text_type):
                            return model._default_manager.db_manager(db).get_by_natural_key(*value).pk
                        else:
                            return force_text(model._meta.pk.to_python(value), strings_only=True)
                else:
                    def m2m_convert(v):
                        return force_text(model._meta.pk.to_python(v), strings_only=True)

                try:
                    m2m_data[field.name] = []
                    for pk in field_value:
                        m2m_data[field.name].append(m2m_convert(pk))
                except Exception as e:
                    raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), pk)

            # Handle FK fields
            elif field.remote_field and isinstance(field.remote_field, models.ManyToOneRel):
                model = field.remote_field.model
                if field_value is not None:
                    try:
                        default_manager = model._default_manager
                        field_name = field.remote_field.field_name
                        if hasattr(default_manager, 'get_by_natural_key'):
                            if hasattr(field_value, '__iter__') and not isinstance(field_value, six.text_type):
                                obj = default_manager.db_manager(db).get_by_natural_key(*field_value)
                                value = getattr(obj, field.remote_field.field_name)
                                # If this is a natural foreign key to an object that
                                # has a FK/O2O as the foreign key, use the FK value
                                if model._meta.pk.remote_field:
                                    value = value.pk
                            else:
                                value = model._meta.get_field(field_name).to_python(field_value)
                            data[field.attname] = value
                        else:
                            data[field.attname] = model._meta.get_field(field_name).to_python(field_value)
                    except Exception as e:
                        raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), field_value)
                else:
                    data[field.attname] = None

            # Handle all other fields
            else:
                try:
                    data[field.name] = field.to_python(field_value)
                except Exception as e:
                    raise base.DeserializationError.WithData(e, d['model'], d.get('pk'), field_value)

        obj = base.build_instance(Model, data, db)
        yield base.DeserializedObject(obj, m2m_data)
