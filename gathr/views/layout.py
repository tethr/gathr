from collections import deque

from pyramid.decorator import reify
from pyramid.i18n import TranslationStringFactory
from pyramid_layout.layout import layout_config

_ = TranslationStringFactory('gathr')


from ..metadata import ResourceContainer


@layout_config(template="templates/main_layout.pt")
class Layout(object):
    brand = _('Gathr')
    page_title = _('Gathr')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def static(self, path):
        return self.request.static_url('gathr.views:static/' + path)

    @reify
    def breadcrumbs(self):
        breadcrumbs = deque()
        node = self.context
        url = self.request.resource_url
        while node:
            if not isinstance(node, ResourceContainer):
                breadcrumbs.appendleft({
                    'title': node.title,
                    'url': url(node)})
            node = node.__parent__
        return breadcrumbs
