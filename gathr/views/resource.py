from pyramid.view import view_config


@view_config(context='gathr.metadata.Resource',
             renderer="templates/view_resource.pt")
def view_resource(context, request):
    return {'title': context.title}
