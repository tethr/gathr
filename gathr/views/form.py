import deform

from pyramid.httpexceptions import HTTPFound
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
            data = form.validate(request.params.items())
            print 'Huh?', data
            context.data.update(data)
            return HTTPFound(request.resource_url(context.__parent__))
        except deform.ValidationFailure, e:
            form = e.render()
    else:
        form = form.render(context.data)

    return {
        'title': context.title,
        'form': HTML(form)
    }

