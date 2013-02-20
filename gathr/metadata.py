import imp
import os
import sys
import yaml

from churro import PersistentType
from churro import PersistentFolder


class Metadata(object):

    def __init__(self, folder, filename='gathr.yaml',
                 dynamic_package='gathr.dynamic'):
        self.folder = folder
        self.resource_types = {}
        self.dynamic_package = dynamic_package
        yaml_data = yaml.load(open(os.path.join(folder, filename)))
        yaml_data.update({
            'id': 'root',
            'one_only': True})
        self.Root = ResourceType.load(
            self.resource_types, dynamic_package, 'Root', yaml_data)
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
        children = node.pop('children', None)
        if children:
            for childname, child in children.items():
                addable_types.append(cls.load(types, package, childname, child))

        members = {
            'addable_types': addable_types,
            'one_only': node.pop('one_only', False),
            'next_id': node.pop('id', 'name'),
            'title': node.pop('title', None)
        }

        assert not node, "Unknown resource attributes: %s" % node

        resource_type = ResourceType(name, (Resource,), members)
        resource_type.__module__ = package
        types[name] = resource_type
        return resource_type


class Resource(PersistentFolder):
    pass

