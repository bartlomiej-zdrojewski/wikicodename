import json
import random
import re
from colorama import Fore
from typing import List, Dict
from unidecode import unidecode
from .cache import Cache
from .config import Config
from .wiki_data import WikiData


class Generator:

    class GeneratorException(Exception):

        def __init__(
                self,
                message,
                profile_name=None,
                source_exception=None) -> None:
            self.source_exception = source_exception
            if profile_name:
                super().__init__(
                    'Could not generate a list of code names for the profile: '
                    '{}\n{}'.format(profile_name, message))
            else:
                super().__init__(message)

    def __init__(
            self,
            config: Config = None,
            cache: Cache = None,
            max_attempt_count: int = 64,
            quiet: bool = False) -> None:
        self.__config = config
        self.__cache = cache
        self.__max_attempt_count = max_attempt_count
        self.__quiet = quiet
        if not self.__config:
            self.__config = Config()
        if not self.__cache:
            self.__cache = Cache()
            self.__cache.setup()

    def __parse_pattern(self, pattern: str) -> Dict[str, List[str]]:
        start = 0
        end = 0
        sequence_start = -1
        format_pattern = ''
        profiles: list[str] = []
        while end >= 0 and end < len(pattern):
            if sequence_start < 0:
                end = pattern.find('{', start)
            else:
                end = pattern.find('}', start)
            if end >= 0:
                if sequence_start < 0:
                    format_pattern += pattern[start:(end+1)]
                    sequence_start = end + 1
                else:
                    format_pattern += '}'
                    profile = pattern[sequence_start:end]
                    profiles.append(profile)
                    sequence_start = -1
                start = end + 1
                end = start
        format_pattern += pattern[start:]
        return {'format_pattern': format_pattern, 'profiles': profiles}

    def __format_code_name(self, code_name, profile) -> str:
        transformed_code_name = code_name
        transform_case = profile['transform_case']
        transform_space = profile['transform_space']
        transform_unidecode = profile['transform_unidecode']
        validation_pattern = profile['validation_pattern']
        if transform_case == 'lower':
            transformed_code_name = transformed_code_name.lower()
        elif transform_case == 'upper':
            transformed_code_name = transformed_code_name.upper()
        if transform_space != False:
            transformed_code_name = [
                transform_space if x.isspace() else x
                for x in transformed_code_name]
            transformed_code_name = ''.join(transformed_code_name)
        if transform_unidecode != False:
            transformed_code_name = unidecode(transformed_code_name)
        validation_result = re.search(
            validation_pattern, transformed_code_name)
        if not validation_result:
            return None
        return validation_result.group(0)

    def __get_code_name_list(self, profile_name: str) -> None:
        cache_name = 'profile_' + profile_name
        cache_data = self.__cache.read(cache_name)
        if cache_data:
            return json.loads(cache_data)
        if not self.__quiet:
            print('\r{}Fetching data for the profile: {}{}'.format(
                Fore.YELLOW, profile_name, Fore.RESET),
                end='')
        code_name_list = []
        profile = self.__config.get_profile(profile_name)
        if not profile:
            raise self.GeneratorException(
                'The profile is not defined.', profile_name)
        if 'code_name_list' not in profile:
            raise self.GeneratorException(
                'The profile does not define a list of code names.',
                profile_name)
        pages = profile['code_name_list']['pages']
        sources = profile['code_name_list']['sources']
        wikipedia_url = self.__config.get_wikipedia_url()
        excluded_sections = self.__config.get_excluded_sections()
        if profile['code_name_list']['wikipedia_url']:
            wikipedia_url = profile['code_name_list']['wikipedia_url']
        if profile['code_name_list']['excluded_sections']:
            excluded_sections = profile['code_name_list']['excluded_sections']
        data = WikiData(self.__cache, wikipedia_url)
        for page in pages:
            if not self.__quiet:
                print(
                    '\r{}Fetching data for the profile: {} '
                    '(page {}/{}){}'.format(
                        Fore.YELLOW,
                        profile_name,
                        pages.index(page) + 1,
                        len(pages),
                        Fore.RESET),
                    end='')
            data.fetch(page, excluded_sections, wikipedia_url)
            for i in range(data.get_table_count()):
                for header in sources['tables']:
                    code_name_list += data.get_table_values_by_header(
                        i, header)
            for i in range(data.get_list_count()):
                if sources['lists']:
                    code_name_list += data.get_list_values(i)
            code_name_list = [
                self.__format_code_name(x, profile) for x in code_name_list]
            code_name_list = [x for x in code_name_list if x]
        cache_data = json.dumps(code_name_list)
        self.__cache.write(cache_name, cache_data)
        if not self.__quiet:
            print('\r{}Fetched data for the profile: {}{}{}'.format(
                Fore.GREEN, profile_name, ' ' * (9 + 2 * 4), Fore.RESET))
        return code_name_list

    def __get_code_name(self, profile_name: str) -> str:
        attempt_count = 0
        code_name = None
        profile = self.__config.get_profile(profile_name)
        if not profile:
            raise self.GeneratorException(
                'The profile is not defined.', profile_name)
        pattern_data = profile['pattern']
        pattern = self.__parse_pattern(pattern_data)
        format_pattern = pattern['format_pattern']
        subprofile_names = pattern['profiles']
        subprofile_count = len(pattern['profiles'])
        if subprofile_count > 1:
            while not code_name and attempt_count < self.__max_attempt_count:
                subprofile_code_names = []
                if profile_name in subprofile_names:
                    raise self.GeneratorException(
                        'The user defined pattern must not contain its '
                        'profile: {}'.format(
                            pattern_data),
                        profile_name)
                for subprofile_name in subprofile_names:
                    subprofile_code_names.append(
                        self.__get_code_name(subprofile_name))
                code_name = self.__format_code_name(
                    format_pattern.format(*subprofile_code_names), profile)
                attempt_count += 1
        elif subprofile_count == 1:
            subprofile_name = subprofile_names[0]
            if profile_name == subprofile_name:
                code_name_list = self.__get_code_name_list(subprofile_name)
                if len(code_name_list) == 0:
                    raise self.GeneratorException(
                        'No code name match the profile.',
                        profile_name)
                code_name_index = random.randrange(0, len(code_name_list))
                code_name = code_name_list[code_name_index]
            else:
                while not code_name and attempt_count < self.__max_attempt_count:
                    subprofile_code_name = self.__get_code_name(
                        subprofile_name)
                    code_name = self.__format_code_name(
                        format_pattern.format(subprofile_code_name), profile)
                    attempt_count += 1
        else:
            raise self.GeneratorException(
                'The pattern does not contain any profile: {}'.format(
                    profile['pattern']),
                profile_name)
        if not code_name:
            raise self.GeneratorException(
                'The maximum number of attempts has been reached.')
        return code_name

    def generate(self, profile_name: str, count: int) -> List[str]:
        attempt_count = 0
        code_name_list: list[str] = []
        try:
            while len(code_name_list) < count and \
                    attempt_count < self.__max_attempt_count:
                code_name = self.__get_code_name(profile_name)
                if code_name not in code_name_list:
                    code_name_list.append(code_name)
                attempt_count += 1
        except Cache.CacheException as e:
            raise self.GeneratorException(
                str(e), profile_name, e.source_exception)
        except WikiData.WikiDataException as e:
            raise self.GeneratorException(
                str(e), profile_name, e.source_exception)
        if len(code_name_list) < count:
            raise self.GeneratorException(
                'The maximum number of attempts has been reached.')
        return code_name_list

    def generate_all(self, profile_name: str) -> List[str]:
        try:
            return self.__get_code_name_list(profile_name)
        except Cache.CacheException as e:
            raise self.GeneratorException(
                str(e), profile_name, e.source_exception)
        except WikiData.WikiDataException as e:
            raise self.GeneratorException(
                str(e), profile_name, e.source_exception)
