from cryptacular.bcrypt import BCRYPTPasswordManager

from churro import Persistent
from churro import PersistentFolder
from churro import PersistentList
from churro import PersistentProperty

bcrypt = BCRYPTPasswordManager()


class UsersFolder(PersistentFolder):
    pass


class User(Persistent):
    password = PersistentProperty()
    fullname = PersistentProperty()
    email = PersistentProperty()
    groups = PersistentProperty()

    def __init__(self, fullname, email):
        self.fullname = fullname
        self.email = email
        self.groups = PersistentList()

    def add_to_group(self, context, group_name):
        group = context._group(group_name)
        if group not in self.groups:
            self.groups.append(group)

    def set_password(self, password):
        self.password = bcrypt.encode(password)

    def check_password(self, password):
        return bcrypt.check(self.password, password)
