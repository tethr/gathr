import colander
import csv
import datetime
import deform.widget
import imp
import sys
import yaml

from deform_bootstrap.widget import DateTimeInputWidget

from churro import Persistent
from churro import PersistentDate
from churro import PersistentDatetime
from churro import PersistentDict
from churro import PersistentList
from churro import PersistentFolder
from churro import PersistentProperty
from churro import PersistentType

from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPConflict
from pyramid.i18n import TranslationString
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid.security import Allow
from pyramid.traversal import resource_path

from .security import GROUPS
from .utils import make_name
from .utils import PersistentSetProperty


resolve_dotted_name = DottedNameResolver().resolve
_ = TranslationStringFactory('gathr')


class Metadata(object):

    def __init__(self, fileobj, dynamic_package='gathr.dynamic'):
        self.datastreams = {}
        self.classes = {}
        self.dynamic_package = dynamic_package
        self.messages = []
        if isinstance(fileobj, basestring):
            fileobj = open(fileobj)
        yaml_data = yaml.load(fileobj)
        self.i18n_domain = yaml_data.pop('i18n_domain', 'gathr_metadata')
        self.i18n_message = MessageFactory(self.i18n_domain, self.messages)
        self.load_datastreams(yaml_data.pop('datastreams', None))
        self.load_resources(yaml_data.pop('resources'))
        assert not yaml_data, "Unknown nodes in metadata: %s" % yaml_data
        self.hook_import()

    def load_resources(self, resources):
        assert len(resources) == 1, "One and only one root resource allowed."
        name, node = resources.items()[0]
        node['one_only'] = True
        self.Root = ResourceType.load(
            self, self.classes, self.dynamic_package, name, node)

    def load_datastreams(self, datastreams):
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
        dynamic_package = self.dynamic_package
        if '.' in dynamic_package:
            base, dynamic = dynamic_package.rsplit('.', 1)
            package = resolve_dotted_name(base)
            module = getattr(package, dynamic, None)
            if module and module.__loader__ is self:
                delattr(package, dynamic)
        if dynamic_package in sys.modules:
            del sys.modules[dynamic_package]
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

        i18n = metadata.i18n_message
        if 'display' in node:
            members['display'] = i18n(node.pop('display'))
        else:
            members['display'] = i18n(name)
        members['plural'] = i18n(node.pop('plural', members['display'] + 's'))
        name = make_name(types, name.title().replace(' ', ''))

        if members['next_id'] == 'serial':
            i18n_id = "serial_id_%s" % name
            i18n(i18n_id, default="%s ${number}" % members['display'])
            def title(self):
                return TranslationString(
                    i18n_id, default="%s ${number}" % self.display,
                    mapping={'number': self.__name__})
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
    members = PersistentProperty()

    @reify
    def __acl__(self):
        path = resource_path(self)
        return [
            (Allow, '%s:%s' % (name, path), group['permissions'])
            for name, group in GROUPS.items()]

    def _group(self, group):
        assert group in GROUPS
        return '%s:%s' % (group, resource_path(self))

    def _add_member(self, group, userid):
        group_members = self.members.get(group)
        if group_members is None:
            self.members[group] = group_members = PersistentList()
        group_members.append(userid)

    def _remove_member(self, group, userid):
        self.members[group].remove(userid)

    def __init__(self):
        for T in self.singleton_types:
            self[T.__name__] = T()
        for T in self.addable_types:
            self[T.__name__] = ResourceContainer(T)
        for F in self.addable_forms:
            self[F.__name__] = F()
        self.members = PersistentDict()


class ResourceContainer(PersistentFolder):
    title = PersistentProperty()

    def __init__(self, resource_type):
        self.title = resource_type.plural


class FormType(PersistentType):

    @classmethod
    def load(cls, metadata, types, package, name, node):
        datastream = node.pop('datastream')
        if datastream not in metadata.datastreams:
            raise ValueError("No such datastream: %s" % datastream)
        members = {
            'datastream': datastream,
            '__metadata__': metadata,
        }
        i18n = metadata.i18n_message
        if 'display' in node:
            members['title'] = i18n(node.pop('display'))
        else:
            members['title'] = i18n(name)
        name = make_name(types, name.title().replace(' ', ''))

        datastream = metadata.datastreams[datastream]
        for field in datastream.fields:
            members[field.name] = field

        assert not node, "Unknown resource attributes: %s" % node

        form = FormType(name, (Form,), members)
        form.__module__ = package
        types[name] = form
        return form


class Form(Persistent):
    timestamp = PersistentDatetime()

    def schema(self):
        datastream = self.__metadata__.datastreams[self.datastream]
        schema = colander.SchemaNode(colander.Mapping())
        for field in datastream.fields:
            schema.add(field.field())
        return schema

    def update(self, data):
        for name, value in data.iteritems():
            setattr(self, name, value)
        self.timestamp = datetime.datetime.now()
        datastream = self.__metadata__.datastreams[self.datastream]
        datastream.record(self._fs, self)

    def data(self):
        data = {}
        for cls in type(self).mro():
            for field in cls.__dict__.values():
                if isinstance(field, Field):
                    data[field.name] = getattr(self, field.name)
        return data

    def csv_data(self):
        data = {}
        for cls in type(self).mro():
            for field in cls.__dict__.values():
                if isinstance(field, Field):
                    data[field.name] = field.to_csv(getattr(self, field.name))
        return data


class Datastream(object):

    def __init__(self, metadata, name, fields):
        self.__metadata__ = metadata
        self.name = name
        self.fields = [Field.load(metadata, node) for node in fields]

    def record(self, fs, form):
        if not fs.exists('/datastreams'):
            fs.mkdir('/datastreams')
        data = form.csv_data()
        data_keys = data.keys()
        data['PATH'] = path = resource_path(form)
        data['TIMESTAMP'] = form.timestamp
        fpath = '/datastreams/%s.csv' % self.name
        if fs.exists(fpath):
            reader = csv.DictReader(fs.open(fpath, 'rb'))
            with fs.open(fpath, 'wb') as out:
                print >> out, ','.join(reader.fieldnames)
                writer = csv.DictWriter(out, reader.fieldnames)
                written = False
                for row in reader:
                    if path < row['PATH'] and not written:
                        writer.writerow(data)
                        writer.writerow(row)
                        written = True
                    elif path == row['PATH']:
                        writer.writerow(data)
                        written = True
                    else:
                        writer.writerow(row)
                if path > row['PATH']:
                    writer.writerow(data)
        else:
            fieldnames = ['PATH', 'TIMESTAMP'] + data_keys
            with fs.open(fpath, 'wb') as out:
                print >> out, ','.join(fieldnames)
                writer = csv.DictWriter(out, fieldnames)
                writer.writerow(data)


class Field(object):
    types = {}
    widget = None
    missing = None
    required = True

    @classmethod
    def load(cls, metadata, node):
        type = node.pop('type')
        return cls.types[type](metadata, node)

    def __init__(self, metadata, node):
        i18n = metadata.i18n_message
        self.name = node.pop('name')
        self.title = i18n(node.pop('display', self.name))
        self.required = node.pop('required', self.required)

        assert not node, "Unknown field attributes: %s" % node

    def field(self):
        nodeargs = {'name': self.name, 'title': self.title}
        if self.widget:
            nodeargs['widget'] = self.widget()
        if not self.required:
            nodeargs['missing'] = self.missing
        nodeargs['required'] = False
        return colander.SchemaNode(
            self.schema_type(), **nodeargs)

    def to_csv(self, value):
        if value is not None:
            return str(value)


def fieldtype(name):
    def decorator(cls):
        Field.types[name] = cls
        return cls
    return decorator


@fieldtype('string')
class StringField(Field, PersistentProperty):
    schema_type = colander.String


@fieldtype('integer')
class IntegerField(Field, PersistentProperty):
    schema_type = colander.Int


@fieldtype('float')
class FloatField(Field, PersistentProperty):
    schema_type = colander.Float

    def __init__(self, metadata, node):
        units = node.pop('units', None)
        super(FloatField, self).__init__(metadata, node)

        if units:
            self.units = metadata.i18n_message(
                'unit_of_measure_%s' % units, default=units)
        else:
            self.widget = None

    def widget(self):
        return deform.widget.TextInputWidget(input_append=self.units)


@fieldtype('boolean')
class BooleanField(Field, PersistentProperty):
    schema_type = colander.Boolean
    widget = deform.widget.CheckboxWidget


@fieldtype('datetime')
class DatetimeField(Field, PersistentDatetime):
    schema_type = colander.DateTime
    widget = DateTimeInputWidget


@fieldtype('date')
class DateField(Field, PersistentDate):
    schema_type = colander.Date


@fieldtype('text')
class TextField(Field, PersistentProperty):
    schema_type = colander.String

    def widget(self):
        return deform.widget.TextAreaWidget(rows=8, css_class="input-xlarge")


@fieldtype('choose one')
class ChooseOneField(Field, PersistentProperty):
    schema_type = colander.String
    break_point = 4

    def __init__(self, metadata, node):
        choices = node.pop('choices')
        super(ChooseOneField, self).__init__(metadata, node)

        i18n = metadata.i18n_message
        self.choices = [
            (choice, i18n("%s_%s" % (self.name, choice), default=choice))
            for choice in choices]

    def widget(self):
        choices = self.choices
        if len(choices) <= self.break_point:
            widget = deform.widget.RadioChoiceWidget
        else:
            choices = list(self.choices) # copy before mutate
            widget = deform.widget.SelectWidget
            choices.insert(0, ('', _('Choose one')))
        return widget(values=choices)


@fieldtype('choose many')
class ChooseManyField(Field, PersistentSetProperty):
    schema_type = colander.Set
    break_point = 4
    required = False

    def __init__(self, metadata, node):
        choices = node.pop('choices')
        super(ChooseManyField, self).__init__(metadata, node)

        i18n = metadata.i18n_message
        self.choices = [
            (choice, i18n("%s_%s" % (self.name, choice), default=choice))
            for choice in choices]

    def widget(self):
        return deform.widget.CheckboxChoiceWidget(values=self.choices)

    def to_csv(self, value):
        if value:
            return '|'.join(value)


class MessageFactory(object):

    def __init__(self, domain, messages):
        self.factory = TranslationStringFactory(domain)
        self.messages = messages

    def __call__(self, *args, **kw):
        message = self.factory(*args, **kw)
        self.messages.append(message)
        return message


def extract_messages(fileobj, keywords, comment_tags, options):
    metadata = Metadata(fileobj)
    messages = []
    for message in metadata.messages:
        default = message.default
        if default:
            comments = (u'Default: %s' % default,)
        else:
            comments = ()
        messages.append((0, None, message, comments))
    return messages
