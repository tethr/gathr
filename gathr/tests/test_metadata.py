try: #pragma NO COVER
    import unittest2 as unittest
    unittest # stfu pyflakes
except ImportError:
    import unittest

import mock

class MetadataTests(unittest.TestCase):
    metadata = None

    def setUp(self):
        import tempfile
        import transaction
        transaction.abort()
        self.tmp = tempfile.mkdtemp('.gathr-tests')

    def tearDown(self):
        import shutil
        import transaction
        transaction.abort()
        shutil.rmtree(self.tmp)
        if self.metadata:
            self.metadata.unhook_import()

    def make_one(self, yaml):
        import os
        from gathr.metadata import Metadata
        open(os.path.join(self.tmp, 'gathr.yaml'), 'w').write(yaml)
        self.metadata = Metadata(self.tmp)
        return self.metadata

    def assertStartsWith(self, s, sub):
        self.assertTrue(s.startswith(sub),
                        "%s does not start with %s" % (repr(s), repr(sub)))

    def assertEndsWith(self, s, sub):
        self.assertTrue(s.endswith(sub),
                        "%s does not end with %s" % (repr(s), repr(sub)))

    def root(self):
        import churro
        import os
        datadir = os.path.join(self.tmp, 'data')
        self.db = churro.Churro(datadir, factory=self.metadata.Root)
        return self.db.root()

    def test_create_resource_types(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    children:\n"
                "      Clinic:\n"
                "        children:\n"
                "          Patient: {}\n"
                "          Nurse: {}\n")
        md = self.make_one(yaml)
        rt = md.classes
        self.assertEqual(len(rt), 4, rt)
        self.assertEqual(md.Root.__name__, 'Study')
        self.assertEqual(md.Root.addable_types[0].__name__, 'Clinic')
        self.assertIn(rt['Patient'], rt['Clinic'].addable_types)
        self.assertIn(rt['Nurse'], rt['Clinic'].addable_types)

    def test_hook_import(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    children:\n"
                "      Clinic:\n"
                "        children:\n"
                "          Patient: {}\n"
                "          Nurse: {}\n")
        md = self.make_one(yaml)
        rt = md.classes
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
        yaml = ("resources:\n"
                "  Study:\n"
                "    children:\n"
                "      Singleton:\n"
                "        one_only: True")
        md = self.make_one(yaml)
        rt = md.classes
        root = md.Root()
        self.assertIsInstance(root['Singleton'], rt['Singleton'])

    def test_display_name(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    children:\n"
                "      Dude:\n"
                "        display: Man\n")
        md = self.make_one(yaml)
        rt = md.classes
        self.assertEqual(rt['Study'].display, 'Study')
        self.assertEqual(rt['Dude'].display, 'Man')

    def test_serial(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    children:\n"
                "      LolCat:\n"
                "        id: serial\n")
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
        yaml = ("resources:\n"
                "  Study:\n"
                "    children:\n"
                "      Clinic: {}\n")
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

    def test_datastreams(self):
        from ..metadata import StringField
        from ..metadata import IntegerField
        yaml = ("resources:\n"
                "  Study: {}\n"
                "datastreams:\n"
                "  one:\n"
                "    -\n"
                "      name: A\n"
                "      type: string\n"
                "    -\n"
                "      name: B\n"
                "      type: integer\n"
                "  two:\n"
                "    -\n"
                "      name: A\n"
                "      type: string\n"
                "    -\n"
                "      name: B\n"
                "      type: integer\n")
        md = self.make_one(yaml)
        one = md.datastreams['one']
        self.assertEqual(one.name, 'one')
        self.assertEqual(one.fields[0].name, 'A')
        self.assertIsInstance(one.fields[0], StringField)
        self.assertEqual(one.fields[1].name, 'B')
        self.assertIsInstance(one.fields[1], IntegerField)

        two = md.datastreams['two']
        self.assertEqual(two.name, 'two')
        self.assertEqual(two.fields[0].name, 'A')
        self.assertIsInstance(two.fields[0], StringField)
        self.assertEqual(two.fields[1].name, 'B')
        self.assertIsInstance(two.fields[1], IntegerField)

    def test_missing_datastream(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        datastream: manifesto\n")
        with self.assertRaises(ValueError):
            self.make_one(yaml)


    def test_form(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        datastream: manifesto\n"
                "datastreams:\n"
                "  manifesto: []\n")
        md = self.make_one(yaml)
        form = md.classes['Manifesto']
        self.assertEqual(form.datastream, 'manifesto')
        Study = md.classes['Study']
        study = Study()
        self.assertIn('Manifesto', study)

    def test_form_title(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        display: Hoo Ha!\n"
                "        datastream: manifesto\n"
                "datastreams:\n"
                "  manifesto: []\n")
        md = self.make_one(yaml)
        form = md.classes['Manifesto']
        self.assertEqual(form.datastream, 'manifesto')
        Study = md.classes['Study']
        study = Study()
        self.assertIn('Manifesto', study)
        self.assertEqual(study['Manifesto'].title, 'Hoo Ha!')

    def test_form_w_string_field(self):
        import colander
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        datastream: manifesto\n"
                "datastreams:\n"
                "  manifesto:\n"
                "    -\n"
                "      name: foo\n"
                "      type: string\n")
        md = self.make_one(yaml)
        schema = md.Root()['Manifesto'].schema()
        self.assertIsInstance(schema.get('foo').typ, colander.String)

    def test_form_w_int_field(self):
        import colander
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        datastream: manifesto\n"
                "datastreams:\n"
                "  manifesto:\n"
                "    -\n"
                "      name: foo\n"
                "      type: integer\n")
        md = self.make_one(yaml)
        schema = md.Root()['Manifesto'].schema()
        self.assertIsInstance(schema.get('foo').typ, colander.Int)

    @mock.patch('gathr.metadata.datetime')
    def test_form_update(self,  mocktime):
        import datetime
        timestamp = datetime.datetime(2010, 5, 12, 2, 42)
        mocktime.datetime.now.return_value = timestamp
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        datastream: manifesto\n"
                "datastreams:\n"
                "  manifesto:\n"
                "    -\n"
                "      name: foo\n"
                "      type: string\n")
        self.make_one(yaml)
        root = self.root()
        root['Manifesto'] = form = root.addable_forms[0]()
        self.db.flush()
        form.update({'foo': 'hubba'})
        self.assertEqual(form.timestamp, timestamp)
        fs = self.db.fs
        self.assertTrue(fs.exists('/datastreams/manifesto.csv'))
        header, data = fs.open('/datastreams/manifesto.csv', 'r').readlines()
        self.assertEqual(header, u'PATH,TIMESTAMP,foo\n')
        self.assertEqual(data, u'/Manifesto,2010-05-12 02:42:00,hubba\n')

    def test_form_insert_csv(self):
        yaml = ("resources:\n"
                "  Study:\n"
                "    children:\n"
                "      Child:\n"
                "        forms:\n"
                "          Favorites:\n"
                "            datastream: favorites\n"
                "datastreams:\n"
                "  favorites:\n"
                "    -\n"
                "      name: color\n"
                "      type: string\n")
        self.make_one(yaml)
        root = self.root()
        Child = root.addable_types[0]
        folder = root['Child']
        folder['nick'] = nick = Child()
        self.db.flush()
        nick['Favorites'].update({'color': 'blue'})
        folder['zeno'] = zeno = Child()
        self.db.flush()
        zeno['Favorites'].update({'color': 'black'})
        folder['abby'] = abby = Child()
        self.db.flush()
        abby['Favorites'].update({'color': 'yellow'})
        folder['jay'] = jay = Child()
        self.db.flush()
        jay['Favorites'].update({'color': 'red'})

        lines = self.db.fs.open('/datastreams/favorites.csv')
        lines.next() # throw away header
        line = lines.next().strip()
        self.assertStartsWith(line, '/Child/abby/Favorites')
        self.assertEndsWith(line, 'yellow')
        line = lines.next().strip()
        self.assertStartsWith(line, '/Child/jay/Favorites')
        self.assertEndsWith(line, 'red')
        line = lines.next().strip()
        self.assertStartsWith(line, '/Child/nick/Favorites')
        self.assertEndsWith(line, 'blue')
        line = lines.next().strip()
        self.assertStartsWith(line, '/Child/zeno/Favorites')
        self.assertEndsWith(line, 'black')
        with self.assertRaises(StopIteration):
            lines.next()

        jay['Favorites'].update({'color': 'orange'})
        lines = self.db.fs.open('/datastreams/favorites.csv').readlines()
        line = lines[2].strip()
        self.assertStartsWith(line, '/Child/jay/Favorites')
        self.assertEndsWith(line, 'orange')

    def test_datetime_field(self):
        import datetime
        import transaction
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        datastream: manifesto\n"
                "datastreams:\n"
                "  manifesto:\n"
                "    -\n"
                "      name: foo\n"
                "      type: datetime\n")
        self.make_one(yaml)
        root = self.root()
        root['Manifesto'] = form = root.addable_forms[0]()
        self.db.flush()
        bday = datetime.datetime(2010, 5, 12, 2, 42)
        form.update({'foo': bday})
        fs = self.db.fs
        self.assertTrue(fs.exists('/datastreams/manifesto.csv'))
        header, data = fs.open('/datastreams/manifesto.csv', 'r').readlines()
        self.assertTrue(data.endswith(u'2010-05-12 02:42:00\n'))

        transaction.commit()
        root =  self.root()

    def test_date_field(self):
        import datetime
        import transaction
        yaml = ("resources:\n"
                "  Study:\n"
                "    forms:\n"
                "      Manifesto:\n"
                "        datastream: manifesto\n"
                "datastreams:\n"
                "  manifesto:\n"
                "    -\n"
                "      name: foo\n"
                "      type: date\n")
        self.make_one(yaml)
        root = self.root()
        root['Manifesto'] = form = root.addable_forms[0]()
        self.db.flush()
        bday = datetime.date(2010, 5, 12)
        form.update({'foo': bday})
        fs = self.db.fs
        self.assertTrue(fs.exists('/datastreams/manifesto.csv'))
        header, data = fs.open('/datastreams/manifesto.csv', 'r').readlines()
        self.assertTrue(data.endswith(u'2010-05-12\n'), data)

        transaction.commit()
        root =  self.root()
