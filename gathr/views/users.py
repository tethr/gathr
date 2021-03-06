import colander
import deform
import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.security import has_permission
from pyramid.view import view_config

from ..security import DELETE
from ..security import MANAGE
from ..security import READ
from ..security import WRITE
from ..users import User
from ..users import UsersFolder
from ..utils import HTML
from ..utils import make_readonly

_ = TranslationStringFactory('gathr')


@view_config(context=User, permission=READ, renderer='templates/form.pt')
def view_user(context, request):
    if request.referrer and 'came_from' not in request.session:
        request.session['came_from'] = request.referrer
    editable = has_permission(WRITE, context, request)
    schema = UserSchema().bind(context=context)
    form = deform.Form(schema, buttons=(_('Save changes'),))
    if editable and request.method == 'POST':
        try:
            note = 'Edited user: %s.' % context.fullname
            data = form.validate(request.params.items())
            context.fullname = data.get('fullname', context.fullname)
            context.email = data.get('email', context.email)
            if data['password']:
                note += '  Changed password.'
                context.set_password(data['password'])
            if data['userid'] != context.__name__:
                folder = context.__parent__
                del folder[context.__name__]
                folder[data['userid']] = context
            redirect_to = request.session.pop(
                'came_from', request.application_url)
            transaction.get().note(note)
            return HTTPFound(redirect_to)
        except deform.ValidationFailure, form:
            rendered = HTML(form.render())
    else:
        data = {'userid': context.__name__, 'fullname': context.fullname,
                'email': context.email}
        if not editable:
            make_readonly(form)
        rendered = HTML(form.render(data))

    if has_permission(DELETE, context, request):
        layout = request.layout_manager.layout
        layout.actions = [
            {'title': _('Delete User'),
             'url': request.resource_url(context, 'delete'),
             'class': 'btn btn-danger',
             'confirm': _("Are you sure you want to delete the user, ${name}?",
                          mapping={'name': context.fullname})
            }]

    return {'form': rendered}


@colander.deferred
def unique_or_unchanged_name(node, kw):
    user = kw['context']
    def validator(node, cstruct):
        if cstruct != user.__name__ and cstruct in user.__parent__:
            raise colander.Invalid(
                node, _('A user with that id already exists.'))
    return validator


class UserSchema(colander.Schema):
    userid = colander.SchemaNode(
        colander.String(), validator=unique_or_unchanged_name,
        description=_("Used for login"))
    fullname = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(colander.String(), missing=None)
    password = colander.SchemaNode(
        colander.String(), title=_("Change password"), missing=None,
        widget=deform.widget.CheckedPasswordWidget())


@view_config(context=UsersFolder, permission=MANAGE,
             renderer='templates/manage_users.pt')
def manage_users(context, request):
    url = request.resource_url
    users = [{'title': user_title(user), 'url': url(user)}
             for user in context.values()]
    users.sort(key=lambda user: user['title'])
    layout = request.layout_manager.layout
    layout.page_title = _("Manage Users")
    return {'users': users, 'add_user_url': url(context, 'add_user')}


def user_title(user):
    if user.email:
        return '%s (%s)' % (user.fullname, user.email)
    return user.fullname


@view_config(context=UsersFolder, name='add_user', permission=MANAGE,
             renderer='templates/form.pt')
def add_user(context, request):
    schema = AddUserSchema().bind(context=context)
    form = deform.Form(schema, buttons=(_('Add user'),))
    if  request.method == 'POST':
        try:
            data = form.validate(request.params.items())
            user = User(data['fullname'], data['email'])
            user.set_password(data['password'])
            context[data['userid']] = user
            transaction.get().note('Added new user: %s.' % user.fullname)
            return HTTPFound(request.resource_url(context))
        except deform.ValidationFailure, form:
            pass

    layout = request.layout_manager.layout
    layout.page_title = _("Add new user")
    rendered = HTML(form.render())
    return {'form': rendered}


@colander.deferred
def unique_name(node, kw):
    users = kw['context']
    def validator(node, cstruct):
        if cstruct in users:
            raise colander.Invalid(
                node, _('A user with that id already exists.'))
    return validator


class AddUserSchema(colander.Schema):
    userid = colander.SchemaNode(colander.String(), validator=unique_name,
        description=_("Name user will use to log in"))
    fullname = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(colander.String(), missing=None)
    password = colander.SchemaNode(colander.String(),
        widget=deform.widget.CheckedPasswordWidget())


@view_config(context=User, name='delete', permission=DELETE)
def delete_user(context, request):
    transaction.get().note('Deleted user: %s' % context.fullname)
    folder = context.__parent__
    context.delete()
    return HTTPFound(request.resource_url(folder))
