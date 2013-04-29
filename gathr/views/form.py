import deform
import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.security import has_permission
from pyramid.traversal import resource_path
from pyramid.view import view_config

from ..metadata import Form
from ..security import READ
from ..security import WRITE
from ..utils import HTML
from ..utils import make_readonly

_ = TranslationStringFactory('gathr')


@view_config(context=Form, renderer='templates/form.pt', permission=READ)
def form(context, request):
    form = deform.Form(context.schema(), buttons=(_('Save changes'),))
    editable = has_permission(WRITE, context, request)
    if editable and request.method == 'POST':
        try:
            created = not filter(None, context.data().values())
            data = form.validate(request.params.items())
            context.update(data)
            verb = "Filled out" if created else "Edited"
            transaction.get().note("%s form: %s" % (
                verb, resource_path(context)))
            return HTTPFound(request.resource_url(context.__parent__))
        except deform.ValidationFailure, e:
            rendered = HTML(e.render())
    else:
        if not editable:
            make_readonly(form)
        rendered = HTML(form.render(context.data()))

    layout = request.layout_manager.layout
    layout.page_title = context.title
    return {'form': rendered}
