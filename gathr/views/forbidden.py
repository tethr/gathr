from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer
from pyramid.i18n import TranslationStringFactory
from pyramid.traversal import find_resource
from pyramid.view import view_config

_ = TranslationStringFactory('gathr')


@view_config(context=HTTPForbidden, renderer='templates/forbidden.pt')
def forbidden(request):
    if not hasattr(request, 'user'):
        locale = get_localizer(request)
        request.session.flash(locale.translate(_("Login required")))
        request.session['came_from'] = request.url
        return HTTPFound(request.resource_url(request.root, 'login'))

    homes = request.user.find_home()
    at_root = not request.path_info.strip('/')
    if at_root and len(homes) == 1:
        return HTTPFound(request.application_url.rstrip('/') + homes[0])

    at_root = at_root and homes
    homes = [find_resource(request.root, path) for path in homes]
    homes = [{'title': home.title, 'url': request.resource_url(home)}
             for home in homes]
    request.layout_manager.use_layout('anonymous')
    layout = request.layout_manager.layout
    if at_root:
        layout.page_title = _("Welcome to Gathr")
    else:
        layout.page_title = _('Forbidden')
    return {
        'at_root': at_root,
        'homes': homes,
    }
