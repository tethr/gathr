import mock
import unittest

class TestUsersFolder(unittest.TestCase):

    def test_it(self):
        from gathr.users import UsersFolder
        from pyramid.security import Allow, Deny, Everyone, ALL_PERMISSIONS
        from pyramid.i18n import TranslationString
        from gathr.security import MANAGERS
        folder = UsersFolder()
        self.assertEqual(folder.__acl__, [
            (Allow, '%s:/' % MANAGERS, ALL_PERMISSIONS),
            (Deny, Everyone, ALL_PERMISSIONS)])
        self.assertIsInstance(folder.title, TranslationString)


class TestUser(unittest.TestCase):

    def make_one(self):
        from gathr.users import User as cls
        fred = cls('Fred Flintstone', 'fred@bedrock')
        fred.__name__ = 'fred'
        return fred

    def test_ctor(self):
        from pyramid.security import Allow
        from pyramid.security import Deny
        from gathr.security import DELETE
        from gathr.security import READ_WRITE
        fred = self.make_one()
        self.assertEqual(fred.fullname, 'Fred Flintstone')
        self.assertEqual(fred.email, 'fred@bedrock')
        self.assertEqual(fred.groups, [])
        self.assertEqual(fred.title, fred.fullname)
        self.assertEqual(fred.__acl__, [(Deny, 'fred', (DELETE,)),
                                        (Allow, 'fred', READ_WRITE)])

    def test_password(self):
        fred = self.make_one()
        fred.set_password('fred')
        self.assertNotEqual(fred.password, 'fred')
        self.assertTrue(fred.check_password('fred'))
        self.assertFalse(fred.check_password('wilma'))

    def test_add_to_group(self):
        fred = self.make_one()
        context = mock.Mock()
        context._group.return_value = 'mockgroup'
        fred.add_to_group(context, 'group')
        context._group.assert_called_once_with('group')
        context._add_member.assert_called_once_with('group', 'fred')
        self.assertEqual(fred.groups, ['mockgroup'])

    def test_remove_from_group(self):
        fred = self.make_one()
        fred.groups.append('mockgroup')
        context = mock.Mock()
        context._group.return_value = 'mockgroup'
        fred.remove_from_group(context, 'group')
        context._group.assert_called_once_with('group')
        context._remove_member.assert_called_once_with('group', 'fred')
        self.assertEqual(fred.groups, [])

    def test_find_home_one_home(self):
        fred = self.make_one()
        fred.groups.append('group:/foo')
        self.assertEqual(fred.find_home(), ['/foo'])

    def test_find_home_two_homes(self):
        fred = self.make_one()
        fred.groups.append('group:/foo')
        fred.groups.append('group:/bar')
        self.assertEqual(set(fred.find_home()), set(['/foo', '/bar']))

    def test_find_home_two_homes_w_containment(self):
        fred = self.make_one()
        fred.groups.append('group:/foo')
        fred.groups.append('group:/bar')
        fred.groups.append('group2:/bar/baz')
        self.assertEqual(set(fred.find_home()), set(['/foo', '/bar']))

    def test_delete(self):
        from pyramid.testing import DummyResource
        root = DummyResource()
        root['fred'] = fred = self.make_one()
        fred.groups.append('mockgroup:/foo')
        root['foo'] = context = DummyResource(_remove_member=mock.Mock())
        fred.delete()
        context._remove_member.assert_called_once_with('mockgroup', 'fred')
        self.assertNotIn('fred', root)
