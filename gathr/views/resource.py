import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.security import has_permission
from pyramid.traversal import resource_path
from pyramid.view import view_config

from ..metadata import Form
from ..metadata import Resource
from ..security import GROUPS
from ..security import MANAGE
from ..security import READ
from ..security import WRITE
from ..utils import find_users
from .users import user_title

_ = TranslationStringFactory('gathr')
isinstance = isinstance  # For use by mock in unittests


@view_config(context=Resource, permission=READ,
             renderer="templates/view_resource.pt")
def view_resource(context, request):
    types = []
    actions = []
    add_types = []
    if has_permission(MANAGE, context, request):
        actions.append(
            {'title': _("Manage Permissions"),
             'url': request.resource_url(context, 'manage_permissions')})

    for resource_type in context.addable_types:
        type_children = [
            {'title': child.title, 'url': request.resource_url(child)}
            for child in context[resource_type.__name__].values()]
        type_children.sort(key=lambda child: child['title'])
        add_url = request.resource_url(context, 'add', query={
            'type': resource_type.__name__})
        types.append({
            'add_url': add_url,
            'name': resource_type.__name__,
            'singular': resource_type.display,
            'plural': resource_type.plural,
            'next_id': resource_type.next_id,
            'children': type_children,
        })
        if has_permission(WRITE, context, request):
            if resource_type.next_id == 'user':
                add_types.append({
                    'title': resource_type.display,
                    'url': '#add-%s-modal' % resource_type.__name__,
                    'datatoggle': 'modal'})
            else:
                add_types.append({
                    'title': resource_type.display,
                    'url': add_url})

    if add_types:
        if len(add_types) == 1:
            add_types[0]['title'] = _(
                "Add ${something}", mapping={'something': add_types[0]['title']}
            )
            actions.append(add_types[0])
        else:
            actions.append({
                'title': _("Add"),
                'children': add_types})

    children = [{'title': child.title, 'url': request.resource_url(child)}
                for child in context.values()
                if isinstance(child, (Resource, Form))]

    return {'title': context.title,
            'types': types,
            'children': children,
            'actions': actions}


@view_config(context=Resource, name='add', permission=WRITE, renderer='json')
def add_resource(context, request):
    type_name = request.params['type']
    metadata = request.registry.metadata
    resource_type = metadata.classes[type_name]
    folder = context[type_name]
    resource = resource_type.create(folder, request)
    resource_url = request.resource_url(resource)
    transaction.get().note('Created %s: %s' % (
        type_name, resource_path(resource)))
    if request.is_xhr:
        return {'resource_url': resource_url}
    return HTTPFound(resource_url)


@view_config(context=Resource, name='manage_permissions', permission=MANAGE,
             renderer='templates/manage_permissions.pt')
def manage_permissions(context, request):
    users = find_users(context)
    action = request.params.get('action')
    if action == 'change_membership':
        userid = request.params['userid']
        prev_group = request.params['prev_group']
        group = request.params['group']
        user = users[userid]
        user.remove_from_group(context, prev_group)
        if group != 'REMOVE':
            assert group in GROUPS
            user.add_to_group(context, group)
        return HTTPFound(request.resource_url(context, request.view_name))

    elif action == 'add_member' and request.params.get('userid'):
        userid = request.params['userid']
        group = request.params['group']
        user = users[userid]
        user.add_to_group(context, group)
        return HTTPFound(request.resource_url(context, request.view_name))

    local_members = []
    member_ids = set()
    for group_name, group_members in context.members.items():
        for userid in group_members:
            member_ids.add(userid)
            user = users[userid]
            local_members.append({
                'user': user_title(user),
                'userid': userid,
                'group': group_name,
            })
    local_members.sort(key=lambda m: m['user'])

    inherited_members = []
    if context.__parent__:
        for resource in lineage(context.__parent__):
            if not hasattr(resource, 'members'):
                continue
            for group_name, group_members in resource.members.items():
                for userid in group_members:
                    user = users[userid]
                    inherited_members.append({
                        'user': user_title(user),
                        'group': GROUPS[group_name]['label'],
                        'path': resource.title,
                        'url': request.resource_url(resource, request.view_name)
                    })
    inherited_members.sort(key=lambda m: m['user'])

    users = [{'name': user_title(user), 'userid': user.__name__}
             for user in users.values() if user.__name__ not in member_ids]

    layout = request.layout_manager.layout
    layout.page_title = _("Manage permissions: ${title}",
                          mapping={'title': context.title})
    return {'local_members': local_members, 'GROUPS': GROUPS,
            'inherited_members': inherited_members, 'users': users}


def lineage(node):
    if node.__parent__:
        for ancestor in lineage(node.__parent__):
            yield ancestor
    yield node
