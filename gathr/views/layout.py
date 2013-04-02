from collections import deque

from pyramid.decorator import reify
from pyramid.i18n import TranslationStringFactory
from pyramid_layout.layout import layout_config

_ = TranslationStringFactory('gathr')


from ..metadata import ResourceContainer


@layout_config(name='anonymous', template='templates/anonymous_layout.pt')
class AnonymousLayout(object):
    brand = _('Gathr')
    page_title = _('Gathr')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def static(self, path):
        return self.request.static_url('gathr.views:static/' + path)

    def deform(self, path):
        return self.request.static_url('deform_bootstrap:static/' + path)

    @reify
    def flash(self):
        return ' '.join(self.request.session.pop_flash())


@layout_config(template="templates/main_layout.pt")
class MainLayout(AnonymousLayout):

    def __init__(self, context, request):
        super(MainLayout, self).__init__(context, request)
        self.user_url = request.resource_url(request.user)
        self.logout = {'label': _("logout"),
                       'url': request.resource_url(request.root, 'logout')}

    @reify
    def breadcrumbs(self):
        breadcrumbs = deque()
        node = self.context
        url = self.request.resource_url
        while node is not None:
            if not isinstance(node, ResourceContainer):
                breadcrumbs.appendleft({
                    'title': node.title,
                    'url': url(node)})
            node = node.__parent__
        return breadcrumbs
