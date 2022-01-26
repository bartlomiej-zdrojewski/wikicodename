import hashlib
import yaml
from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError, DistutilsInternalError
from os import listdir, makedirs, path, remove
from typing import Any, Optional, Union, List


class Config:

    TRANSFORM_CASE_OPTIONS = ['keep', 'lower', 'upper']

    class ConfigException(Exception):

        def __init__(
                self, message: str,
                source_file: str = None,
                source_exception: Exception = None):
            self.source_exception = source_exception
            if source_file:
                super().__init__(
                    'Could not load the configuration file: {}\n{}'.format(
                        source_file, message))
            else:
                super().__init__(message)

    class __MissingParameterException(ConfigException):

        def __init__(self, parameter_name: str):
            super().__init__(
                'The parameter is missing: {}'.format(
                    parameter_name))

    class __InvalidParameterTypeException(ConfigException):

        def __init__(self, parameter_name: str, parameter_type: type):
            super().__init__(
                'The type is not allowed for the \'{}\' parameter: {}'.format(
                    parameter_name, parameter_type.__name__))

    class __InvalidParameterValueException(ConfigException):

        def __init__(self, parameter_name: str, parameter_value: object):
            super().__init__(
                'The value is not allowed for the \'{}\' parameter: {}'.format(
                    parameter_name, parameter_value))

    def __init__(self, base_path: str = 'config/'):
        self.__base_path = base_path
        self.__wikipedia_url = None
        self.__excluded_sections = None
        self.__profiles = {}

    def __load_file(self, file_path: str) -> dict:
        try:
            file = open(file_path, 'r')
            data = yaml.load(file, Loader=yaml.SafeLoader)
            file.close()
            if not isinstance(data, dict):
                raise Config.ConfigException(
                    'The file syntax is invalid.', file_path)
            return data
        except Exception as e:
            if isinstance(e, Config.ConfigException):
                raise e
            else:
                raise Config.ConfigException(
                    'The file does not exist or its syntax is invalid.',
                    file_path,
                    e)

    def __load_parameter(
            self,
            data: dict,
            key: str,
            optional: bool = False,
            types: Union[type, List[type]] = str,
            name: str = None) -> Any:
        display_name = name
        if not display_name:
            display_name = key
        parameter = data.get(key)
        if parameter or parameter == 0:
            if not isinstance(parameter, types):
                raise Config.__InvalidParameterTypeException(
                    display_name, type(parameter))
        elif not optional:
            raise Config.__MissingParameterException(key)
        return parameter

    def __load_profile(self, name: str, data: dict) -> dict:
        if not name:
            raise self.__MissingParameterException('profile/name')
        if '{' in name or '}' in name:
            raise self.__InvalidParameterValueException('profile/name', name)
        if self.get_profile(name):
            raise self.ConfigException(
                'The profile is already defined: {}'.format(name))
        profile = {}
        profile['name'] = name
        profile['pattern'] = '{{{}}}'.format(name)
        if data:
            profile['transform_case'] = self.__load_parameter(
                data,
                'transform_case',
                True,
                name='profile/transform_case')
            profile['transform_space'] = self.__load_parameter(
                data, 'transform_space',
                True,
                (bool, str),
                'profile/transform_space')
            profile['transform_unidecode'] = self.__load_parameter(
                data, 'transform_unidecode',
                True,
                bool,
                'profile/transform_unidecode')
            profile['validation_pattern'] = self.__load_parameter(
                data, 'validation_pattern',
                True,
                name='profile/validation_pattern')
        else:
            profile['transform_case'] = None
            profile['transform_space'] = None
            profile['transform_unidecode'] = None
            profile['validation_pattern'] = None
        if profile['transform_case']:
            if profile['transform_case'] not in self.TRANSFORM_CASE_OPTIONS:
                raise self.__InvalidParameterValueException(
                    'profile/transform_case', profile['transform_case'])
        else:
            profile['transform_case'] = self.TRANSFORM_CASE_OPTIONS[0]
        if not profile['transform_space']:
            profile['transform_space'] = False
        if not profile['transform_unidecode']:
            profile['transform_unidecode'] = False
        if not profile['validation_pattern']:
            profile['validation_pattern'] = '.*'
        return profile

    def __load_main(self, data: dict):
        self.__wikipedia_url = self.__load_parameter(data, 'wikipedia_url')
        self.__excluded_sections = self.__load_parameter(
            data, 'excluded_sections', True, types=list)
        profiles_raw = self.__load_parameter(data, 'profile', types=list)
        for profile_data in profiles_raw:
            profile_name = self.__load_parameter(
                profile_data, 'name', name='profile/name')
            profile_pattern = self.__load_parameter(
                profile_data, 'pattern', name='profile/pattern')
            profile = self.__load_profile(profile_name, profile_data)
            profile['pattern'] = profile_pattern
            self.__profiles[profile['name']] = profile
        if self.__excluded_sections:
            for value in self.__excluded_sections:
                if not isinstance(value, str):
                    raise self.__InvalidParameterTypeException(
                        'excluded_sections/value', type(value))
        else:
            self.__excluded_sections = []
        if not self.get_profile('main'):
            raise self.ConfigException('The \'main\' profile is not defined.')

    def __load_code_name_list(self, name: str, data: dict):
        profile_data = self.__load_parameter(data, 'profile', True, dict)
        profile = self.__load_profile(name, profile_data)
        code_name_list = {}
        code_name_list['wikipedia_url'] = self.__load_parameter(
            data, 'wikipedia_url', True)
        code_name_list['excluded_sections'] = self.__load_parameter(
            data, 'excluded_sections', True, types=list)
        code_name_list['pages'] = self.__load_parameter(
            data, 'pages', types=list)
        code_name_list['sources'] = self.__load_parameter(
            data, 'sources', types=dict)
        for value in code_name_list['pages']:
            if not isinstance(value, str):
                raise self.__InvalidParameterTypeException(
                    'pages/value', type(value))
        if not code_name_list['wikipedia_url']:
            code_name_list['wikipedia_url'] = False
        if not code_name_list['excluded_sections']:
            code_name_list['excluded_sections'] = False
        if 'lists' in code_name_list['sources']:
            if not isinstance(code_name_list['sources']['lists'], bool):
                raise self.__InvalidParameterTypeException(
                    'sources/lists', type(code_name_list['sources']['lists']))
        else:
            code_name_list['sources']['lists'] = False
        if 'tables' in code_name_list['sources']:
            if not isinstance(code_name_list['sources']['tables'], list):
                raise self.__InvalidParameterTypeException(
                    'sources/tables', type(code_name_list['sources']['tables']))
            for value in code_name_list['sources']['tables']:
                if not isinstance(value, str):
                    raise self.__InvalidParameterTypeException(
                        'sources/tables/value', type(value))
        else:
            code_name_list['sources']['tables'] = []
        profile['code_name_list'] = code_name_list
        self.__profiles[profile['name']] = profile

    def generate(self):
        try:
            makedirs(self.__base_path, exist_ok=True)
        except OSError as e:
            raise Config.ConfigException(
                'Could not create the configuration directory: {}'.format(
                    self.__base_path),
                None,
                e)
        for file_name in listdir(self.__base_path):
            file_path = path.join(self.__base_path, file_name)
            if path.isfile(file_path):
                file_extension = path.splitext(file_name)[1]
                if file_extension.lower() != '.yaml':
                    continue
                try:
                    if path.isfile(file_path):
                        remove(file_path)
                except Exception as e:
                    raise Config.ConfigException(
                        'Could not delete the file: {}'.format(file_path), e)
        script_directory_path = path.dirname(path.realpath(__file__))
        default_config_path = path.join(
            script_directory_path, 'defaults', 'config')
        try:
            copy_tree(default_config_path, self.__base_path)
        except (DistutilsFileError, DistutilsInternalError) as e:
            raise Config.ConfigException(
                'Could not copy the default configuration: {} -> {}'.format(
                    default_config_path, self.__base_path),
                None,
                e)

    def load(self):
        if not path.isdir(self.__base_path):
            raise Config.ConfigException(
                'The configuration directory does not exist: {}'.format(
                    self.__base_path))
        for file_name in listdir(self.__base_path):
            file_path = path.join(self.__base_path, file_name)
            if path.isfile(file_path):
                file_base_name = path.splitext(file_name)[0]
                file_extension = path.splitext(file_name)[1]
                if file_extension.lower() != '.yaml':
                    continue
                try:
                    data = self.__load_file(file_path)
                    if file_base_name.lower() == 'main':
                        self.__load_main(data)
                    else:
                        self.__load_code_name_list(
                            file_base_name.lower(), data)
                except (Config.__MissingParameterException,
                        Config.__InvalidParameterTypeException,
                        Config.__InvalidParameterValueException) as e:
                    raise Config.ConfigException(
                        str(e), file_path, e.source_exception)
        if not self.get_profile('main'):
            raise self.ConfigException('The \'main\' profile is not defined.')

    def get_version(self) -> str:
        hash = hashlib.sha1()
        hash.update(str(self.__dict__).encode('utf-8'))
        return hash.hexdigest()

    def get_wikipedia_url(self) -> Optional[str]:
        return self.__wikipedia_url

    def get_excluded_sections(self) -> Optional[List[str]]:
        return self.__excluded_sections

    def get_profile(self, name: str) -> dict:
        return self.__profiles.get(name.lower())

    def get_profile_name_list(self) -> List[str]:
        return list(self.__profiles.keys())
