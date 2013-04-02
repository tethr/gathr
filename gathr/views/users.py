import colander
import deform

from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.security import has_permission
from pyramid.view import view_config

from ..security import READ
from ..security import WRITE
from ..users import User
from ..utils import HTML
from ..utils import make_readonly

_ = TranslationStringFactory('gathr')


@view_config(context=User, permission=READ, renderer='templates/form.pt')
def view_user(context, request):
    if request.referrer and 'came_from' not in request.session:
        request.session['came_from'] = request.referrer
    editable = has_permission(WRITE, context, request)
    schema = UserSchema()
    form = deform.Form(schema, buttons=(_('Save changes'),))
    if editable and request.method == 'POST':
        try:
            data = form.validate(request.params.items())
            context.fullname = data.get('fullname', context.fullname)
            context.email = data.get('email', context.email)
            redirect_to = request.session.pop(
                'came_from', request.application_url)
            return HTTPFound(redirect_to)
        except deform.ValidationFailure, form:
            rendered = HTML(form.render())
    else:
        data = {'fullname': context.fullname, 'email': context.email}
        if not editable:
            make_readonly(form)
        rendered = HTML(form.render(data))

    return {'form': rendered}


class UserSchema(colander.Schema):
    fullname = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(colander.String())
