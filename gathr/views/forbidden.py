from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config

_ = TranslationStringFactory('gathr')


@view_config(context=HTTPForbidden, renderer='templates/forbidden.pt')
def forbidden(request):
    if not hasattr(request, 'user'):
        locale = get_localizer(request)
        request.session.flash(locale.translate(_("Login required")))
        request.session['came_from'] = request.url
        return HTTPFound(request.resource_url(request.root, 'login'))

    request.layout_manager.use_layout('anonymous')
    request.layout_manager.layout.page_title = _('Forbidden')
    return {}
