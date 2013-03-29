import transaction
from churro import Churro

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator

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
    config.scan()
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
    root = request.root
    if 'users' in root:
        users = root['users']
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

