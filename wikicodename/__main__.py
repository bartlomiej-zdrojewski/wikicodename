import argparse
import sys
from appdirs import user_cache_dir, user_config_dir
from colorama import Fore, init as colorama_init
from os import path
from .cache import Cache
from .generator import Generator
from .config import Config

CONFIG_PATH_FLAG = '--config-path'
CACHE_PATH_FLAG = '--cache-path'
PROFILE_FLAG = '--profile'
PROFILE_FLAG_SHORT = '-p'
COUNT_FLAG = '--count'
COUNT_FLAG_SHORT = '-c'
ATTEMPT_COUNT_FLAG = '--attempt-count'
SORT_FLAG = '--sort'
SORT_FLAG_SHORT = '-s'
LIST_ALL_FLAG = '--list-all'
LIST_PROFILES_FLAG = '--list-profiles'
GENERATE_CONFIG_FLAG = '--generate-config'
CLEAR_CACHE_FLAG = '--clear-cache'
QUIET_FLAG = '--quiet'
QUIET_FLAG_SHORT = '-q'

APPLICATION_MESSAGE = 'Generate code names using lists and tables from ' \
    'Wikipedia articles.'
CONFIG_PATH_FLAG_MESSAGE = 'set a path to the configuration directory'
CACHE_PATH_FLAG_MESSAGE = 'set a path to the cache directory'
PROFILE_FLAG_MESSAGE = 'set a profile name'
COUNT_FLAG_MESSAGE = 'set a length of the generated list of code names'
ATTEMPT_COUNT_FLAG_MESSAGE = 'set a maximum number of attempts to generate ' \
    'a valid code name'
SORT_FLAG_MESSAGE = 'sort the generated list of code names'
LIST_ALL_FLAG_MESSAGE = 'list all code names for the profile (must be a list ' \
    'of code names)'
LIST_PROFILES_FLAG_MESSAGE = 'list all available profiles'
GENERATE_CONFIG_FLAG_MESSAGE = 'generate a default configuration'
CLEAR_CACHE_FLAG_MESSAGE = 'clear the cache'
QUIET_FLAG_MESSAGE = 'do not print additional messages (useful in scripts)'

APP_DIRECTORY_NAME = 'wikicodename'
CONFIG_VERSION_CACHE_KEY = 'config_version'

INITIAL_CONFIG_GENERATION_FAILED_MESSAGE = '{}Failed to generate the initial ' \
    'configuration.{}'.format(Fore.RED, Fore.RESET)
CONFIG_GENERATED_MESSAGE = '{}The configuration has been generated.{}'.format(
    Fore.GREEN, Fore.RESET)
CONFIG_SHOULD_BE_GENERATED_OR_FIXED_MESSAGE = '{}Please run the application ' \
    'with the {} flag to generate a valid configuration or fix it manually.' \
    '{}'.format(Fore.YELLOW, GENERATE_CONFIG_FLAG, Fore.RESET)
CONFIG_CHANGED_MESSAGE = '{}The configuration has changed. Please run the ' \
    'application with the {} flag to clear the cache.{}'.format(
        Fore.YELLOW, CLEAR_CACHE_FLAG, Fore.RESET)
CACHE_CLEARED_MESSAGE = '{}The cache has been cleared.{}'.format(
    Fore.GREEN, Fore.RESET)


def get_default_config_path():
    return user_config_dir(APP_DIRECTORY_NAME, False)


def get_default_cache_path():
    return user_cache_dir(APP_DIRECTORY_NAME, False)


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description=APPLICATION_MESSAGE, add_help=False)
    arg_parser.add_argument(
        '--help', '-h', action='help', help='show this help message')
    arg_parser.add_argument(
        CONFIG_PATH_FLAG,
        type=str,
        nargs=1,
        default=get_default_config_path(),
        help=CONFIG_PATH_FLAG_MESSAGE)
    arg_parser.add_argument(
        CACHE_PATH_FLAG,
        type=str,
        nargs=1,
        default=get_default_cache_path(),
        help=CACHE_PATH_FLAG_MESSAGE)
    arg_parser.add_argument(
        PROFILE_FLAG,
        PROFILE_FLAG_SHORT,
        type=str,
        nargs=1,
        default='main',
        help=PROFILE_FLAG_MESSAGE)
    arg_parser.add_argument(
        COUNT_FLAG,
        COUNT_FLAG_SHORT,
        type=int,
        nargs=1,
        default=10,
        help=COUNT_FLAG_MESSAGE)
    arg_parser.add_argument(
        ATTEMPT_COUNT_FLAG,
        type=int,
        nargs=1,
        default=64,
        help=ATTEMPT_COUNT_FLAG_MESSAGE)
    arg_parser.add_argument(
        SORT_FLAG,
        SORT_FLAG_SHORT,
        action='store_const',
        const=True,
        default=False,
        help=SORT_FLAG_MESSAGE)
    arg_parser.add_argument(
        LIST_ALL_FLAG,
        action='store_const',
        const=True,
        default=False,
        help=LIST_ALL_FLAG_MESSAGE)
    arg_parser.add_argument(
        LIST_PROFILES_FLAG,
        action='store_const',
        const=True,
        default=False,
        help=LIST_PROFILES_FLAG_MESSAGE)
    arg_parser.add_argument(
        GENERATE_CONFIG_FLAG,
        action='store_const',
        const=True,
        default=False,
        help=GENERATE_CONFIG_FLAG_MESSAGE)
    arg_parser.add_argument(
        CLEAR_CACHE_FLAG,
        action='store_const',
        const=True,
        default=False,
        help=CLEAR_CACHE_FLAG_MESSAGE)
    arg_parser.add_argument(
        QUIET_FLAG,
        QUIET_FLAG_SHORT,
        action='store_const',
        const=True,
        default=False,
        help=QUIET_FLAG_MESSAGE)
    return arg_parser.parse_args()


def get_arg(value):
    if isinstance(value, list):
        return value[0]
    return value


def print_exception(exception: Exception):
    print('\r{}{}{}'.format(Fore.RED, exception, Fore.RESET), file=sys.stderr)
    if hasattr(exception, 'source_exception'):
        if exception.source_exception:
            print(exception.source_exception, file=sys.stderr)


def main():
    colorama_init()
    args = parse_args()
    config_path = get_arg(args.config_path)
    if config_path == get_default_config_path():
        if not path.isdir(config_path):
            try:
                initial_config = Config(config_path)
                initial_config.generate()
            except Config.ConfigException as e:
                print(INITIAL_CONFIG_GENERATION_FAILED_MESSAGE)
                print_exception(e)
                return 1
    try:
        config = Config(config_path)
        if args.generate_config:
            config.generate()
            if not args.quiet:
                print(CONFIG_GENERATED_MESSAGE)
            return 0
        config.load()
        if args.list_profiles:
            profile_name_list = config.get_profile_name_list()
            profile_name_list.sort()
            for profile_name in profile_name_list:
                print(profile_name)
            return 0
    except Config.ConfigException as e:
        print(CONFIG_SHOULD_BE_GENERATED_OR_FIXED_MESSAGE)
        print_exception(e)
        return 2
    try:
        cache = Cache(get_arg(args.cache_path))
        cache.setup()
        if args.clear_cache:
            cache.clear()
            if not args.quiet:
                print(CACHE_CLEARED_MESSAGE)
            return 0
        if not args.quiet:
            config_version = cache.read(CONFIG_VERSION_CACHE_KEY)
            if config_version and config_version != config.get_version():
                print(CONFIG_CHANGED_MESSAGE)
        cache.write(CONFIG_VERSION_CACHE_KEY, config.get_version())
    except Cache.CacheException as e:
        print_exception(e)
        return 3
    try:
        generator = Generator(
            config,
            cache,
            get_arg(args.attempt_count),
            get_arg(args.quiet))
        code_name_list = None
        if args.list_all:
            code_name_list = generator.generate_all(
                get_arg(args.profile))
        else:
            code_name_list = generator.generate(
                get_arg(args.profile), get_arg(args.count))
        if args.sort:
            code_name_list.sort()
        for code_name in code_name_list:
            print(code_name)
    except Generator.GeneratorException as e:
        print_exception(e)
        return 4
    return 0


if __name__ == '__main__':
    sys.exit(main())
