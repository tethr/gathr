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
        yaml = ("Clinic:\n"
                "  children:\n"
                "    Patient: {}\n"
                "    Nurse: {}\n")
        md = self.make_one(yaml)
        rt = md.resource_types
        self.assertEqual(len(rt), 4, rt)
        self.assertEqual(md.Root.__name__, 'Root')
        self.assertEqual(md.Root.addable_types[0].__name__, 'Clinic')
        self.assertIn(rt['Patient'], rt['Clinic'].addable_types)
        self.assertIn(rt['Nurse'], rt['Clinic'].addable_types)

    def test_hook_import(self):
        yaml = ("Clinic:\n"
                "  children:\n"
                "    Patient: {}\n"
                "    Nurse: {}\n")
        md = self.make_one(yaml)
        rt = md.resource_types
        from gathr.dynamic import Root
        from gathr.dynamic import Clinic
        from gathr.dynamic import Patient
        from gathr.dynamic import Nurse
        self.assertIs(rt['Root'], Root)
        self.assertIs(rt['Clinic'], Clinic)
        self.assertIs(rt['Patient'], Patient)
        self.assertIs(rt['Nurse'], Nurse)
        self.assertIs(Nurse, md.load_module('gathr.dynamic').Nurse)
