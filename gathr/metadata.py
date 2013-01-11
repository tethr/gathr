import imp
import os
import sys
import yaml

from pyramid.threadlocal import get_current_registry

from churro import PersistentType
from churro import PersistentFolder



class Metadata(object):
    Root = None

    def __init__(self, folder, filename='gathr.yaml',
                 dynamic_package='gathr.dynamic'):
        self.folder = folder
        self.resource_types = {}
        self.dynamic_package = dynamic_package
        self.yaml_data = yaml.load(open(os.path.join(folder, filename)))
        self.load_resource_type('Root', {'children': self.yaml_data})
        sys.meta_path.append(self)

    def load_resource_type(self, name, node):
        addable_types = []
        children = node.get('children')
        if children:
            for childname, child in children.items():
                addable_types.append(
                    self.load_resource_type(childname, child))
        self.resource_types[name] = resource_type = PersistentType(
            name, (PersistentFolder,), {'addable_types': addable_types})
        resource_type.__module__ = self.dynamic_package
        return resource_type

    def find_module(self, fullname, path=None):
        registry = get_current_registry()
        if registry and getattr(registry, 'metadata', None) is self:
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
