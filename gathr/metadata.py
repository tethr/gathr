import colander
import imp
import os
import sys
import yaml

from churro import Persistent
from churro import PersistentDict
from churro import PersistentFolder
from churro import PersistentProperty
from churro import PersistentType

from pyramid.httpexceptions import HTTPConflict

from .utils import make_name


class Metadata(object):

    def __init__(self, folder, filename='gathr.yaml',
                 dynamic_package='gathr.dynamic'):
        self.folder = folder
        self.datastreams = {}
        self.classes = {}
        self.dynamic_package = dynamic_package
        yaml_data = yaml.load(open(os.path.join(folder, filename)))
        self.load_resources(yaml_data)
        self.load_datastreams(yaml_data)

    def load_resources(self, yaml_data):
        resources = yaml_data['resources']
        assert len(resources) == 1, "One and only one root resource allowed."
        name, node = resources.items()[0]
        node['one_only'] = True
        self.Root = ResourceType.load(
            self, self.classes, self.dynamic_package, name, node)
        self.hook_import()

    def load_datastreams(self, yaml_data):
        datastreams = yaml_data.get('datastreams')
        if not datastreams:
            return

        for name, fields in datastreams.items():
            self.datastreams[name] = Datastream(self, name, fields)

    def find_module(self, fullname, path=None):
        if fullname == self.dynamic_package:
            return self

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        module = imp.new_module(fullname)
        module.__loader__ = self
        module.__file__ = '<dynamic>'
        module.__dict__.update(self.classes)
        sys.modules[fullname] = module
        return module

    def hook_import(self):
        sys.meta_path.append(self)

    def unhook_import(self):
        if self.dynamic_package in sys.modules:
            del sys.modules[self.dynamic_package]
        sys.meta_path.remove(self)


class ResourceType(PersistentType):

    @classmethod
    def load(cls, metadata, types, package, name, node):
        addable_types = []
        singleton_types = []
        children = node.pop('children', None)
        if children:
            for childname, child in children.items():
                t = cls.load(metadata, types, package, childname, child)
                if t.one_only:
                    singleton_types.append(t)
                else:
                    addable_types.append(t)

        addable_forms = []
        forms = node.pop('forms', None)
        if forms:
            for formname, form in forms.items():
                addable_forms.append(FormType.load(
                    metadata, types, package, formname, form))

        one_only = node.pop('one_only', False)
        if one_only:
            next_id = 'singleton'
        else:
            next_id = node.pop('id', 'user')
        members = {
            'addable_types': addable_types,
            'singleton_types': singleton_types,
            'addable_forms': addable_forms,
            'one_only': one_only,
            'next_id': next_id,
            '__metadata__': metadata,
        }

        if 'display' in node:
            members['display'] = node.pop('display')
        else:
            members['display'] = name
        members['plural'] = node.pop('plural', members['display'] + 's')
        name = make_name(types, name.title().replace(' ', ''))

        if members['next_id'] == 'serial':
            def title(self):
                # Will need to use or return TranslationString for i18n
                return '%s %s' % (self.display, self.__name__)
            members['title'] = property(title)
            def create_serial(cls, folder, request):
                name = str(len(folder) + 1)
                folder[name] = resource = cls()
                return resource
            members['create'] = classmethod(create_serial)

        elif members['next_id'] == 'user':
            members['title'] = PersistentProperty()
            def create_user(cls, folder, request):
                title = request.params['title']
                try:
                    name = make_name(folder, title)
                    folder[name] = resource = cls()
                    resource.title = title
                    return resource
                except ValueError, e:
                    error = HTTPConflict()
                    error.body = str(e)
                    raise error
            members['create'] = classmethod(create_user)

        elif members['next_id'] == 'singleton':
            members['title'] = members['display']

        assert not node, "Unknown resource attributes: %s" % node

        resource_type = ResourceType(name, (Resource,), members)
        resource_type.__module__ = package
        types[name] = resource_type
        return resource_type


class Resource(PersistentFolder):

    def __init__(self):
        for T in self.singleton_types:
            self[T.__name__] = T()
        for T in self.addable_types:
            self[T.__name__] = ResourceContainer(T)
        for F in self.addable_forms:
            self[F.__name__] = F()


class ResourceContainer(PersistentFolder):
    title = PersistentProperty()

    def __init__(self, resource_type):
        self.title = resource_type.plural


class FormType(PersistentType):

    @classmethod
    def load(cls, metadata, types, package, name, node):
        members = {
            'datastream': node.pop('datastream'),
            '__metadata__': metadata,
        }
        if 'display' in node:
            members['title'] = node.pop('display')
        else:
            members['title'] = name
        name = make_name(types, name.title().replace(' ', ''))

        assert not node, "Unknown resource attributes: %s" % node

        form = FormType(name, (Form,), members)
        form.__module__ = package
        types[name] = form
        return form


class Form(Persistent):
    data = PersistentProperty()

    def __init__(self):
        self.data = PersistentDict()

    def schema(self):
        datastream = self.__metadata__.datastreams[self.datastream]
        schema = colander.SchemaNode(colander.Mapping())
        for field in datastream.fields:
            schema.add(field.field())
        return schema


class Datastream(object):

    def __init__(self, metadata, name, fields):
        self.__metadata__ = metadata
        self.name = name
        self.fields = [Field.load(node) for node in fields]


class Field(object):
    types = {}

    @classmethod
    def load(cls, node):
        type = node.pop('type')
        return cls.types[type](node)

    def __init__(self, node):
        self.name = node.pop('name')

        assert not node, "Unknown field attributes: %s" % node

    def field(self):
        return colander.SchemaNode(self.schema_type(), name=self.name)


def fieldtype(name):
    def decorator(cls):
        Field.types[name] = cls
        return cls
    return decorator


@fieldtype('string')
class StringField(Field):
    schema_type = colander.String


@fieldtype('integer')
class IntegerField(Field):
    schema_type = colander.Int

