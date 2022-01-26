import concurrent.futures
import json
from typing import Optional, List, Tuple
from lxml import etree
from urllib.error import URLError
from urllib.parse import urljoin, urlencode, parse_qs
from urllib.request import urlopen
from .cache import Cache


class WikiData:

    class WikiDataException(Exception):

        def __init__(self, message: str, source_exception: Exception = None):
            self.source_exception = source_exception
            super().__init__(message)

    class __FetchException(WikiDataException):

        def __init__(
                self,
                message: str,
                page_id: str = None,
                source_exception: Exception = None):
            if page_id:
                super().__init__(
                    'Could not fetch the page: {}\n{}'.format(
                        page_id, message),
                    source_exception)
            else:
                super().__init__(message, source_exception)

    def __init__(
            self,
            cache: Cache = None,
            wikipedia_url: str = 'https://en.wikipedia.org/'):
        self.__cache = cache
        self.__wikipedia_url = wikipedia_url
        self.__timeout: int = 30
        self.__max_worker_count: int = 8
        self.__tables: list[etree.Element] = []
        self.__lists: list[etree.Element] = []
        if not self.__cache:
            self.__cache = Cache()
            self.__cache.setup()

    def __get_text(self, node: etree.Element) -> Optional[str]:
        if node is None:
            return None
        if not node.text:
            if len(node) > 0:
                return self.__get_text(node[0])
            return None
        return node.text

    def __is_sublist(self, node: etree.Element) -> bool:
        for child_node in node:
            if child_node.tag in ['ul', 'ol', 'dl']:
                return True
        return False

    def __get_url(
            self,
            page_id: str,
            section_id: int = None,
            wikipedia_url: str = None) -> str:
        if not wikipedia_url:
            wikipedia_url = self.__wikipedia_url
        url_base = urljoin(wikipedia_url, '/w/api.php')
        url_params = {
            'action': 'parse',
            'page': page_id,
            'format': 'json'
        }
        if section_id != None:
            url_params['section'] = section_id
            url_params['prop'] = 'text'
            url_params['disabletoc'] = '1'
            url_params['disableeditsection'] = '1'
        else:
            url_params['prop'] = 'sections'
        return url_base + '?' + urlencode(url_params)

    def __fetch_url(self, url: str) -> str:
        page_id = None
        if 'page' in parse_qs(url):
            page_id = parse_qs(url)['page'][0]
        try:
            response = urlopen(url, timeout=self.__timeout)
            data = json.loads(response.read())
        except URLError as e:
            raise WikiData.__FetchException(
                'Could not fetch the URL: {}'.format(url), page_id, e)
        except json.JSONDecodeError as e:
            raise WikiData.__FetchException(
                'The response is not a valid JSON text.', page_id, e)
        if 'error' in data and 'info' in data['error']:
            raise WikiData.__FetchException(
                'Wikipedia API: {}'.format(data['error']['info']), page_id)
        return data

    def __fetch_section_list(
            self,
            page_id: str,
            wikipedia_url: str = None) -> List[Tuple[int, str]]:
        url = self.__get_url(page_id, None, wikipedia_url)
        data = self.__cache.read(url)
        if not data:
            data = self.__fetch_url(url)
            if 'parse' not in data or 'sections' not in data['parse']:
                raise WikiData.__FetchException(
                    'The response has an unexpected format.', page_id)
            data = data['parse']['sections']
            data = [(int(x['index']), x['line']) for x in data if x['index']]
            data.insert(0, (0, ''))
            self.__cache.write(url, json.dumps(data))
        else:
            data = json.loads(data)
        return data

    def __fetch_section(
            self,
            page_id: str,
            section_id: int,
            wikipedia_url: str = None) -> str:
        url = self.__get_url(page_id, section_id, wikipedia_url)
        data = self.__cache.read(url)
        if not data:
            data = self.__fetch_url(url)
            if 'parse' not in data or 'text' not in data['parse'] or \
                    '*' not in data['parse']['text']:
                raise WikiData.__FetchException(
                    'The response has an unexpected format.', page_id)
            data = data['parse']['text']['*']
            self.__cache.write(url, data)
        return data

    def __process_section(self, data: str):
        root = etree.HTML(data)
        for table in root.iter('tbody'):
            self.__tables.append(table)
        for list_tag in ['ul', 'ol', 'dl']:
            for list_node in root.iter(list_tag):
                self.__lists.append(list_node)

    def fetch(
            self,
            page_id: str,
            excluded_sections: List[str] = [],
            wikipedia_url: str = None):
        self.__tables.clear()
        self.__lists.clear()
        section_list = self.__fetch_section_list(page_id, wikipedia_url)
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.__max_worker_count) as executor:
            future_list = []
            for section in section_list:
                if section[1] in excluded_sections:
                    continue
                future = executor.submit(
                    self.__fetch_section, page_id, section[0], wikipedia_url)
                future_list.append(future)
            for future in concurrent.futures.as_completed(future_list):
                data = future.result()
                self.__process_section(data)

    def get_table_count(self) -> int:
        return len(self.__tables)

    def get_list_count(self) -> int:
        return len(self.__lists)

    def get_table_headers(self, table_index: int) -> List[str]:
        headers: list[str] = []
        rows = iter(self.__tables[table_index])
        if not rows:
            return None
        for row in rows:
            for cell in row:
                text = self.__get_text(cell)
                if text:
                    headers.append(text.strip())
                else:
                    headers.append(None)
            break
        return headers

    def get_table_values_by_column(
            self, table_index: int, column_index: int) -> List[str]:
        values: list[str] = []
        rows = iter(self.__tables[table_index])
        for row in rows:
            if column_index >= len(row):
                continue
            value = self.__get_text(row[column_index])
            if value:
                values.append(value)
        return values[1:]

    def get_table_values_by_header(
            self, table_index: int, header: str) -> List[str]:
        headers = self.get_table_headers(table_index)
        if not headers:
            return []
        if header in headers:
            return self.get_table_values_by_column(
                table_index, headers.index(header))
        elif header.strip() in headers:
            return self.get_table_values_by_column(
                table_index, headers.index(header.stip()))
        return []

    def get_list_values(self, list_index: int) -> List[str]:
        values: list[str] = []
        rows = iter(self.__lists[list_index])
        for row in rows:
            if row.tag not in ['li', 'dt']:
                continue
            if self.__is_sublist(row):
                continue
            value = self.__get_text(row)
            if value:
                values.append(value)
        return values
