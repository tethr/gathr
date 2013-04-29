import deform
import os
import pkg_resources
import transaction
from churro import Churro

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import get_localizer
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.threadlocal import get_current_request


from .metadata import Metadata
from .users import UsersFolder


def main(global_config, **config):
    settings = global_config.copy()
    settings.update(config)

    config = Configurator(
        settings=settings,
        root_factory=root_factory,
        locale_negotiator=locale_negotiator,
    )
    metadata = Metadata(settings['metadata'])
    config.set_authentication_policy(
        AuthTktAuthenticationPolicy(settings['secret'], find_user))
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.registry.metadata = metadata
    config.include('deform_bootstrap')
    config.include('pyramid_layout')
    config.include('pyramid_tm')
    config.add_static_view('/static', 'gathr.views:static')
    config.set_session_factory(
        UnencryptedCookieSessionFactoryConfig(settings['secret']))
    metadata_folder = os.path.dirname(os.path.abspath(settings['metadata']))
    translation_folder = os.path.join(metadata_folder, 'locale')
    translation_dirs = ["gathr:locale", "deform:locale"]
    if os.path.exists(translation_folder):
        translation_dirs.append(translation_folder)
    config.add_translation_dirs(*translation_dirs)
    config.scan()
    config_deform()
    return config.make_wsgi_app()


def root_factory(request):
    metadata = request.registry.metadata
    settings = request.registry.settings
    def factory():
        root = metadata.Root()
        root['users'] = UsersFolder()
        return root
    churro = Churro(settings['data'], factory=factory)
    return churro.root()


def find_user(userid, request):
    users = request.root['users']
    user = users.get(userid)
    if user:
        tx = transaction.get()
        if user.fullname:
            tx.setUser(user.fullname)
        else:
            tx.setUser(userid)
        if user.email:
            tx.setExtendedInfo('email', user.email)
        request.user = user
        return user.groups


def config_deform():
    def translator(term):
        return get_localizer(get_current_request()).translate(term)

    default_path = deform.Form.default_renderer.loader.search_path
    gathr_path = (pkg_resources.resource_filename('gathr.views', 'forms'),)
    search_path = gathr_path + default_path
    zpt_renderer = deform.ZPTRendererFactory(search_path, translator=translator)
    deform.Form.set_default_renderer(zpt_renderer)

    # OMG monkey patch!  Consider fixing readonly forms upstream.
    from deform_bootstrap.widget import DateTimeInputWidget as widget
    widget.readonly_template = 'readonly/splitted_datetimeinput'


DEFAULT_LOCALE = 'en'
AVAILABLE_LOCALES = set(['en', 'it'])
LOCALE_COOKIE = '_LOCALE_'

def locale_negotiator(request):
    # Give user chance to change language
    locale = request.params.get(LOCALE_COOKIE)
    if locale:
       request.response.set_cookie(LOCALE_COOKIE, locale)
       return locale

    # Prefer cookie, fall back on Accept-Language header.
    locale = request.cookies.get(LOCALE_COOKIE)
    if locale:
        return locale

    if request.accept_language:
        for locale in request.accept_language:
            if locale in AVAILABLE_LOCALES:
                request.response.set_cookie(LOCALE_COOKIE, locale)
                return locale

    return DEFAULT_LOCALE
