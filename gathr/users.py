from cryptacular.bcrypt import BCRYPTPasswordManager

from churro import Persistent
from churro import PersistentFolder
from churro import PersistentList
from churro import PersistentProperty

from pyramid.i18n import TranslationStringFactory
from pyramid.security import Allow
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.traversal import find_resource

from .security import DELETE
from .security import MANAGERS
from .security import READ_WRITE


bcrypt = BCRYPTPasswordManager()
_ = TranslationStringFactory('gathr')


class UsersFolder(PersistentFolder):
    title = _('Users')

    __acl__ = [
        (Allow, '%s:/' % MANAGERS, ALL_PERMISSIONS),
        (Deny, Everyone, ALL_PERMISSIONS)]


class User(Persistent):
    password = PersistentProperty()
    fullname = PersistentProperty()
    email = PersistentProperty()
    groups = PersistentProperty()

    def __init__(self, fullname, email):
        self.fullname = fullname
        self.email = email
        self.groups = PersistentList()

    @property
    def __acl__(self):
        return [(Deny, self.__name__, (DELETE,)),
                (Allow, self.__name__, READ_WRITE)]

    def add_to_group(self, context, group_name):
        group = context._group(group_name)
        if group not in self.groups:
            self.groups.append(group)
            context._add_member(group_name, self.__name__)

    def remove_from_group(self, context, group_name):
        group = context._group(group_name)
        self.groups.remove(group)
        context._remove_member(group_name, self.__name__)

    def set_password(self, password):
        self.password = bcrypt.encode(password)

    def check_password(self, password):
        return bcrypt.check(self.password, password)

    @property
    def title(self):
        return self.fullname

    def find_home(self):
        nodes = [group.split(':')[1] for group in self.groups]
        if len(nodes) <= 1:
            return nodes

        nodes = [filter(None, node.split('/')) for node in nodes]
        nodes.sort(key=lambda node: len(node))
        roots = set()
        for node in nodes:
            for l in xrange(len(node) - 1):
                if tuple(node[:l + 1]) in roots:
                    break
            else:
                roots.add(tuple(node))

        return ['/' + '/'.join(root) for root in roots]

    def delete(self):
        for group in self.groups:
            name, path = group.split(':')
            resource = find_resource(self, path)
            resource._remove_member(name, self.__name__)
        del self.__parent__[self.__name__]

