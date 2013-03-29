import colander
import deform

from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.security import forget
from pyramid.security import remember
from pyramid.view import view_config

from ..utils import HTML

_ = TranslationStringFactory('gathr')


class LoginSchema(colander.Schema):
    userid = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(), widget=deform.widget.PasswordWidget())

    @colander.deferred
    def validator(node, kw):
        request = kw['request']
        def deferred(node, cstruct):
            userid = cstruct.get('userid')
            password = cstruct.get('password')
            if userid and password:
                user = request.root['users'].get(userid)
                if user and user.check_password(password):
                    cstruct['user'] = user
                    return
            raise colander.Invalid(node, _('Invalid username or password'))

        return deferred


@view_config(name='login', renderer='templates/login.pt')
def login(request):
    schema = LoginSchema().bind(request=request)
    form = deform.Form(schema, buttons=(_('Login'),))
    if request.method == 'POST':
        try:
            user = form.validate(request.params.items())['user']
            came_from = request.session.pop(
                'came_from', request.application_url)
            redirect = HTTPFound(came_from)
            redirect.headerlist.extend(remember(request, user.__name__))
            return redirect
        except deform.ValidationFailure, form:
            pass

    request.layout_manager.use_layout('anonymous')
    layout = request.layout_manager.layout
    layout.page_title = _('Gathr Login')
    return {'form': HTML(form.render())}


@view_config(name='logout')
def logout(request):
    redirect_to = request.resource_url(request.root, 'login')
    redirect = HTTPFound(redirect_to)
    redirect.headerlist.extend(forget(request))
    request.session.flash("Logged out")
    return redirect
