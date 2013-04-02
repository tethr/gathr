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
        return [(Allow, self.__name__, READ_WRITE)]

    def add_to_group(self, context, group_name):
        group = context._group(group_name)
        if group not in self.groups:
            self.groups.append(group)

    def set_password(self, password):
        self.password = bcrypt.encode(password)

    def check_password(self, password):
        return bcrypt.check(self.password, password)

    @property
    def title(self):
        return self.fullname
