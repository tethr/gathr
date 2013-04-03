import deform
import pkg_resources
import transaction
from churro import Churro

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from .metadata import Metadata
from .users import UsersFolder


def main(global_config, **config):
    settings = global_config.copy()
    settings.update(config)

    config = Configurator(settings=settings, root_factory=root_factory)
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
    config.scan()
    add_deform_search_path()
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


def add_deform_search_path():
    """
    We do read only forms differently than standard deform, so we need to get
    our own widget templates on the search path.  This should be called after
    deform_bootstrap has been included in the config.
    """
    loader = deform.Form.default_renderer.loader
    loader.search_path = (
        pkg_resources.resource_filename('gathr.views', 'forms'),
        ) + loader.search_path

    # OMG monkey patch!  Consider fixing readonly forms upstream.
    from deform_bootstrap.widget import DateTimeInputWidget as widget
    widget.readonly_template = 'readonly/splitted_datetimeinput'
