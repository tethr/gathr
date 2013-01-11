from churro import Churro
from pyramid.config import Configurator

from .metadata import Metadata


def main(global_config, **config):
    settings = global_config.copy()
    settings.update(config)

    config = Configurator(settings=settings, root_factory=root_factory)
    metadata = Metadata(settings['metadata'])
    config.registry.metadata = metadata
    config.scan()
    return config.make_wsgi_app()


def root_factory(request):
    metadata = request.registry.metadata
    settings = request.registry.settings
    churro = Churro(settings['data'], factory=metadata.Root)
    return churro.root()
