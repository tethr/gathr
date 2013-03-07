import imp
import os
import sys
import yaml

from churro import PersistentFolder
from churro import PersistentProperty
from churro import PersistentType

from .utils import make_name


class Metadata(object):

    def __init__(self, folder, filename='gathr.yaml',
                 dynamic_package='gathr.dynamic'):
        self.folder = folder
        self.resource_types = {}
        self.dynamic_package = dynamic_package
        yaml_data = yaml.load(open(os.path.join(folder, filename)))
        tree = yaml_data['tree']
        assert len(tree) == 1, "One and only one root resource allowed."
        name, node = tree.items()[0]
        node['one_only'] = True
        self.Root = ResourceType.load(
            self.resource_types, dynamic_package, name, node)
        self.hook_import()

    def find_module(self, fullname, path=None):
        if fullname == self.dynamic_package:
            return self

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        module = imp.new_module(fullname)
        module.__loader__ = self
        module.__file__ = '<dynamic>'
        module.__dict__.update(self.resource_types)
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
    def load(cls, types, package, name, node):
        addable_types = []
        singleton_types = []
        children = node.pop('children', None)
        if children:
            for childname, child in children.items():
                t = cls.load(types, package, childname, child)
                if t.one_only:
                    singleton_types.append(t)
                else:
                    addable_types.append(t)

        one_only = node.pop('one_only', False)
        if one_only:
            next_id = 'singleton'
        else:
            next_id = node.pop('id', 'user')
        members = {
            'addable_types': addable_types,
            'singleton_types': singleton_types,
            'one_only': one_only,
            'next_id': next_id,
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
        elif members['next_id'] == 'user':
            members['title'] = PersistentProperty()
        elif members['next_id'] == 'singleton':
            members['title'] = members['display']

        assert not node, "Unknown resource attributes: %s" % node

        resource_type = ResourceType(name, (Resource,), members)
        resource_type.__module__ = package
        types[name] = resource_type
        return resource_type


class Resource(PersistentFolder):

    def __init__(self):
        for t in self.singleton_types:
            self[t.__name__] = t()
        for t in self.addable_types:
            self[t.__name__] = ResourceContainer(t)


class ResourceContainer(PersistentFolder):
    title = PersistentProperty()

    def __init__(self, resource_type):
        self.title = resource_type.plural

