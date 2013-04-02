import deform
import transaction

from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import resource_path
from pyramid.view import view_config

from ..metadata import Form
from ..utils import HTML


@view_config(context=Form, renderer='templates/form.pt')
def form(context, request):
    if 'cancel' in request.params:
        return HTTPFound(request.resource_url(context.__parent__))

    form = deform.Form(context.schema(), buttons=('submit', 'cancel'))
    if 'submit' in request.params:
        try:
            created = not filter(None, context.data().values())
            data = form.validate(request.params.items())
            context.update(data)
            verb = "Filled out" if created else "Edited"
            transaction.get().note("%s form: %s" % (
                verb, resource_path(context)))
            return HTTPFound(request.resource_url(context.__parent__))
        except deform.ValidationFailure, e:
            form = e.render()
    else:
        form = form.render(context.data())

    return {'form': HTML(form)}
