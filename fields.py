from django.db import models
from django.db.models.fields.related import SingleRelatedObjectDescriptor 
from django.conf import settings
from cPickle import dumps, loads, UnpicklingError

class ByteA(models.Field):
  def __init__(self, verbose_name=None):
    super(ByteA, self).__init__(blank=True, null=True, editable=False, verbose_name=verbose_name)

  def db_type(self):
    if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
      return 'BYTEA'
    elif settings.DATABASE_ENGINE == 'mysql':
      return 'BLOB'

class BigInt(models.Field):
  def __init__(self, verbose_name=None):
    super(BigInt, self).__init__(blank=True, null=True, editable=False, verbose_name=verbose_name)

  def db_type(self):
    if settings.DATABASE_ENGINE in ['postgresql_psycopg2', 'mysql']:
      return 'BIGINT'
    else:
      raise "settings.DATABASE_ENGINE not in ['postgresql_psycopg2', 'mysql']"


class AutoSingleRelatedObjectDescriptor(SingleRelatedObjectDescriptor):
  def __get__(self, instance, instance_type=None):
    cached_name = '_cached_' + self.related.get_accessor_name()
    if not hasattr(instance, cached_name):
      try:
        obj = super(AutoSingleRelatedObjectDescriptor, self).__get__(instance, instance_type)
      except self.related.model.DoesNotExist:
        obj = self.related.model(**{self.related.field.name: instance})
        obj.save()
      setattr(instance, cached_name, obj)
    return getattr(instance, cached_name)

class AutoOneToOneField(models.OneToOneField):
  """
  OneToOneField, that creates dependant object from parent
  on the first reference if it isnt exists.
  """
  def contribute_to_related_class(self, cls, related):
    setattr(cls, related.get_accessor_name(), AutoSingleRelatedObjectDescriptor(related))
    if not cls._meta.one_to_one_field:
      cls._meta.one_to_one_field = self

class Dict(dict):
    def __init__(self, obj):
	try:
	    self.data = loads(str(obj.prefs))
	except UnpicklingError:
	    self.data = {}
	self.obj = obj

    def __getitem__(self, key):
	if self.data.has_key(key):
	     return self.data[key]
	return None

    def get(self, key, default=None):
	return self.data.get(key, default)

    def __setitem__(self, key, value):
	self.data[key] = value
	self.obj.prefs = dumps(self.data)
    
    def __delitem__(self, key):
	if self.data.has_key(key):
	    del self.data[key]
	    self.obj.prefs = dumps(self.data)

    def update(self, dict_):
	for k, v in dict_.items():
	    self.__setitem__(k, v)

    def has_key(self, key):
	if self.data.has_key(key):
	    return True
	return False

    def __repr__(self):
	return str(self.data)

