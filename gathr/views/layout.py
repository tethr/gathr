from pyramid.i18n import TranslationStringFactory
from pyramid_layout.layout import layout_config

_ = TranslationStringFactory('gathr')


@layout_config(template="templates/main_layout.pt")
class Layout(object):
    brand = _('Gathr')
    page_title = _('Gathr')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def static(self, path):
        return self.request.static_url('gathr.views:static/' + path)
