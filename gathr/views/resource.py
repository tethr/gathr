import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import resource_path
from pyramid.view import view_config

from ..metadata import Form
from ..metadata import Resource
from ..security import READ
from ..security import WRITE


@view_config(context=Resource, permission=READ,
             renderer="templates/view_resource.pt")
def view_resource(context, request):
    types = []
    for resource_type in context.addable_types:
        type_children = [
            {'title': child.title, 'url': request.resource_url(child)}
            for child in context[resource_type.__name__].values()]
        type_children.sort(key=lambda child: child['title'])
        types.append({
            'name': resource_type.__name__,
            'singular': resource_type.display,
            'plural': resource_type.plural,
            'add_url': request.resource_url(context, 'add', query={
                'type': resource_type.__name__}),
            'next_id': resource_type.next_id,
            'children': type_children,
        })

    children = [{'title': child.title, 'url': request.resource_url(child)}
                for child in context.values()
                if isinstance(child, (Resource, Form))]

    return {'title': context.title,
            'types': types,
            'children': children}


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
