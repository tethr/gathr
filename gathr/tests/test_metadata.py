try: #pragma NO COVER
    import unittest2 as unittest
    unittest # stfu pyflakes
except ImportError:
    import unittest


class MetadataTests(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp('.gathr-tests')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)
        if self.metadata:
            self.metadata.unhook_import()

    def make_one(self, yaml):
        import os
        from gathr.metadata import Metadata
        open(os.path.join(self.tmp, 'gathr.yaml'), 'w').write(yaml)
        self.metadata = Metadata(self.tmp)
        return self.metadata

    def test_create_resource_types(self):
        yaml = ("Study:\n"
                "  children:\n"
                "    Clinic:\n"
                "      children:\n"
                "        Patient: {}\n"
                "        Nurse: {}\n")
        md = self.make_one(yaml)
        rt = md.resource_types
        self.assertEqual(len(rt), 4, rt)
        self.assertEqual(md.Root.__name__, 'Study')
        self.assertEqual(md.Root.addable_types[0].__name__, 'Clinic')
        self.assertIn(rt['Patient'], rt['Clinic'].addable_types)
        self.assertIn(rt['Nurse'], rt['Clinic'].addable_types)

    def test_hook_import(self):
        yaml = ("Study:\n"
                "  children:\n"
                "    Clinic:\n"
                "      children:\n"
                "        Patient: {}\n"
                "        Nurse: {}\n")
        md = self.make_one(yaml)
        rt = md.resource_types
        from gathr.dynamic import Study
        from gathr.dynamic import Clinic
        from gathr.dynamic import Patient
        from gathr.dynamic import Nurse
        self.assertIs(rt['Study'], Study)
        self.assertIs(rt['Clinic'], Clinic)
        self.assertIs(rt['Patient'], Patient)
        self.assertIs(rt['Nurse'], Nurse)
        self.assertIs(Nurse, md.load_module('gathr.dynamic').Nurse)

    def test_singleton(self):
        yaml = ("Study:\n"
                "  children:\n"
                "    Singleton:\n"
                "      one_only: True")
        md = self.make_one(yaml)
        rt = md.resource_types
        root = md.Root()
        self.assertIsInstance(root['Singleton'], rt['Singleton'])

    def test_display_name(self):
        yaml = ("Study:\n"
                "  children:\n"
                "    Dude:\n"
                "      display: Man\n")
        md = self.make_one(yaml)
        rt = md.resource_types
        self.assertEqual(rt['Study'].display, 'Study')
        self.assertEqual(rt['Dude'].display, 'Man')

    def test_serial(self):
        yaml = ("Study:\n"
                "  children:\n"
                "    LolCat:\n"
                "      id: serial\n")
        md = self.make_one(yaml)
        root = md.Root()
        LolCat = root.addable_types[0]
        one = LolCat.create(root['Lolcat'], None)
        self.assertEqual(one.__name__, '1')
        self.assertEqual(one.title, 'LolCat 1')
        two = LolCat.create(root['Lolcat'], None)
        self.assertEqual(two.__name__, '2')
        self.assertEqual(two.title, 'LolCat 2')

    def test_user(self):
        from pyramid.httpexceptions import HTTPConflict
        from pyramid.testing import DummyRequest
        yaml = ("Study:\n"
                "  children:\n"
                "    Clinic: {}\n")
        md = self.make_one(yaml)
        root = md.Root()
        request = DummyRequest(params={'title': 'Foo Bar'})
        Clinic = root.addable_types[0]
        folder = root['Clinic']
        foo = Clinic.create(folder, request)
        self.assertEqual(foo.__name__, 'Foo-Bar')
        self.assertEqual(foo.title, 'Foo Bar')
        self.assertIn('Foo-Bar', folder)
        with self.assertRaises(HTTPConflict):
            Clinic.create(folder, request)
