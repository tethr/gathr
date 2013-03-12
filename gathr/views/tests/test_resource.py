import mock
import unittest

class ViewResourceTests(unittest.TestCase):

    def setUp(self):
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        from ...metadata import ResourceContainer
        class DummyChild0(object):
            pass
        class DummyChild1(object):
            display = 'Idiot'
            plural = 'Idiots'
            next_id = 'user'
        class DummyChild2(object):
            display = 'Moron'
            plural = 'Morons'
            next_id = 'serial'
        self.context = context = DummyResource(
            title='Losers',
            addable_types=[DummyChild1, DummyChild2],
            singleton_types=[DummyChild0])
        context['DummyChild1'] = ResourceContainer(DummyChild1)
        context['DummyChild1']['a'] = DummyResource(title='A')
        context['DummyChild1']['b'] = DummyResource(title='B')
        context['DummyChild2'] = ResourceContainer(DummyChild2)
        context['DummyChild2']['a'] = DummyResource(title='A')
        context['DummyChild2']['b'] = DummyResource(title='B')
        context['DummyChild0'] = DummyResource(title='Zero')

        self.request = DummyRequest()

    def call_fut(self):
        from ..resource import view_resource
        return view_resource(self.context, self.request)

    def test_it(self):
        self.assertEqual(self.call_fut(),
            {'children': [{'title': 'Zero', 'url': 'http://example.com/DummyChild0/'}],
             'title': 'Losers',
             'types': [{'add_url': 'http://example.com/add?type=DummyChild1',
                        'children': [{'title': 'A',
                                      'url': 'http://example.com/DummyChild1/a/'},
                                     {'title': 'B',
                                      'url': 'http://example.com/DummyChild1/b/'}],
                        'name': 'DummyChild1',
                        'next_id': 'user',
                        'plural': 'Idiots',
                        'singular': 'Idiot'},
                       {'add_url': 'http://example.com/add?type=DummyChild2',
                        'children': [{'title': 'A',
                                      'url': 'http://example.com/DummyChild2/a/'},
                                     {'title': 'B',
                                      'url': 'http://example.com/DummyChild2/b/'}],
                        'name': 'DummyChild2',
                        'next_id': 'serial',
                        'plural': 'Morons',
                        'singular': 'Moron'}]})


class AddResourceTests(unittest.TestCase):

    def setUp(self):
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        class DummyType(object):
            @classmethod
            def create(self, context, request):
                self.create_called = (context, request)
        self.type = DummyType
        self.context = context = DummyResource()
        context['DummyType'] = self.folder = DummyResource()

        self.request = request = DummyRequest(params={'type': 'DummyType'})
        request.registry.metadata = md = mock.Mock()
        md.classes = {'DummyType': DummyType}

    def call_fut(self):
        from ..resource import add_resource
        return add_resource(self.context, self.request)

    def test_redirect(self):
        self.request.is_xhr = False
        self.assertEqual(self.call_fut().location, 'http://example.com/')
        self.assertTrue(self.type.create_called)

    def test_ajax(self):
        self.request.is_xhr = True
        self.assertEqual(self.call_fut(),
                         {'resource_url': 'http://example.com/'})
        self.assertTrue(self.type.create_called)
