import argparse
import os
import sys

from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po

from pyramid.paster import bootstrap


def main(argv=sys.argv[1:]):
    # Parse arguments and find a config file
    parser = argparse.ArgumentParser(
        description="Internationalize a study.")
    parser.add_argument('--config', '-C', metavar='INI_FILE',
        help="Path to ini configuration file.  Default: etc/gathr.ini")
    subparsers = parser.add_subparsers(
        title='command', help='Available commands.')
    extract_messages_parser = subparsers.add_parser(
        'extract_messages', help='Extract messages and create .pot file.')
    extract_messages_parser.set_defaults(
        func=extract_messages, parser=extract_messages_parser)

    args = parser.parse_args(argv)
    config = args.config
    if not config:
        envdir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
        config = os.path.join(envdir, 'etc', 'gathr.ini')
    args.env = bootstrap(config)
    args.func(args)


def extract_messages(args):
    metadata = args.env['registry'].metadata
    locale_dir = os.path.join(metadata.folder, 'locale')
    if not os.path.exists(locale_dir):
        os.makedirs(locale_dir)
    outfile = os.path.join(locale_dir, metadata.i18n_domain + '.pot')
    catalog = Catalog(domain=metadata.i18n_domain)
    for message in metadata.messages:
        catalog.add(message, message.default)
    with open(outfile, 'w') as out:
        write_po(out, catalog)
