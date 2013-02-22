from pyramid.httpexceptions import HTTPConflict
from pyramid.view import view_config

from ..metadata import Resource
from ..utils import make_name


@view_config(context=Resource, renderer="templates/view_resource.pt")
def view_resource(context, request):
    types = []
    for resource_type in context.addable_types:
        children = context[resource_type.__name__].values()
        types.append({
            'name': resource_type.__name__,
            'singular': resource_type.display,
            'plural': resource_type.plural,
            'add_url': request.resource_url(context, 'add', query={
                'type': resource_type.__name__}),
            'next_id': resource_type.next_id,
            'children': [
                {'title': child.title,
                 'url': request.resource_url(child)}
                for child in children]
            })

    return {'title': context.title,
            'types': types}


@view_config(context=Resource, name='add', renderer='json')
def add_resource(context, request):
    type_name = request.params['type']
    title = request.params['title']
    metadata = request.registry.metadata
    resource_type = metadata.resource_types[type_name]
    folder = context[type_name]
    try:
        name = make_name(folder, title)
    except ValueError, e:
        response = HTTPConflict()
        response.body = str(e)
        return response
    resource = resource_type()
    resource.title = title
    folder[name] = resource
    return {'resource_url': request.resource_url(resource)}
