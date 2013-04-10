from collections import deque

from pyramid.decorator import reify
from pyramid.i18n import TranslationStringFactory
from pyramid.security import has_permission
from pyramid_layout.layout import layout_config

_ = TranslationStringFactory('gathr')


from ..metadata import ResourceContainer
from ..security import MANAGE
from ..security import READ
from ..utils import find_users


@layout_config(name='anonymous', template='templates/anonymous_layout.pt')
class AnonymousLayout(object):
    brand = _('Gathr')
    page_title = _('Gathr')
    actions = None

    def __init__(self, context, request):
        self.context = context
        self.request = request
        title = getattr(context, 'title', None)
        if title:
            self.page_title = title

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
        request = self.request
        url = request.resource_url
        while node is not None:
            if not isinstance(node, ResourceContainer):
                breadcrumbs.appendleft({
                    'title': node.title,
                    'url': url(node),
                    'viewable': has_permission(READ, node, request)})
            node = node.__parent__
        return breadcrumbs

    @reify
    def main_menu(self):
        items = []
        users = find_users(self.context)
        request = self.request
        if has_permission(MANAGE, users, request):
            items.append({
                'title': _("Manage Users"),
                'url': request.resource_url(users)})
        return items
