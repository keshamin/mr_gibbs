import os
import re
from typing import Optional, Union

import transmission_rpc
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from collections import OrderedDict
import requests
from requests.structures import CaseInsensitiveDict

from src.config import TRACKER, ADMIN_ID, USERS_IDS


def get_legal_users_ids():
    return [ADMIN_ID] + USERS_IDS


def humanize_tr_string(line):
    line = [x.strip() for x in line.split('  ') if x]
    tid, percent, have, eta = line[:4]
    status = line[7]
    name = ' '.join(line[8:])
    return '{}) {} - {}, {}/{} (ETA: {})'.format(tid, name, status, have, percent, eta)


def get_search_results(search_request):
    """
    :param search_request: a string to search for
    :raises ValueError: when search results page cannot be parsed
    """
    search_url = urljoin(TRACKER, '/search/0/0/100/2/')
    url = urljoin(search_url, quote(search_request))
    page = requests.get(url).content.decode('utf-8')
    soup = BeautifulSoup(page, 'html.parser')

    index_el = soup.find(id='index')
    if index_el is None:
        raise ValueError('#index element not found on tracker page!')

    rows = index_el.find_all('tr')
    if len(rows) == 0:
        raise ValueError('Rows not found on search page!')

    result = []
    for row in rows[1:]:
        torrent = {}
        td_list = row.find_all('td')
        torrent['link'] = urljoin(TRACKER, row.find('a', class_='downgif')['href'])
        torrent['title'] = str(td_list[1].find_all('a')[2].string)
        torrent['size'] = td_list[-2].string.replace('\xa0', ' ')
        result.append(torrent)
    return result


def prepare_response_list(results_list, start):
    n = start
    response = ''
    for torrent in results_list:
        response += '/{} {} ({})\n'.format(n + 1, torrent['title'], torrent['size'])
        n += 1
    return response


def humanize_bytes(bytesize, precision=2):
    """
    Humanize byte size figures
    """
    abbrevs = (
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'bytes')
    )
    if bytesize == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytesize >= factor:
            break
    if factor == 1:
        precision = 0
    return '%.*f %s' % (precision, bytesize / float(factor), suffix)


def splitall(path):
    if len(path) == 0:
        return []

    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def path_to_dict(path, file: transmission_rpc.File = None):
    parts = splitall(path)
    if len(parts) > 1:
        next_path = '/'.join(parts[1:])
        return {parts[0]: path_to_dict(next_path, file=file)}
    return {path: file}


def unite_dicts(d1, d2):
    result = OrderedDict()
    for key in d1:
        if key not in d2:
            result[key] = d1[key]
        else:
            result[key] = unite_dicts(d1[key], d2[key])

    for key in d2:
        if key not in d1:
            result[key] = d2[key]
        else:
            result[key] = unite_dicts(d1[key], d2[key])

    return result


def paths_to_dict(files):
    """Takes dict of files like {1: {'name': 'path/to/file', 'selected': False, ...}}
    """
    path_dicts = [path_to_dict(file.name, file=file) for file in files]

    result = OrderedDict()
    for d in path_dicts:
        result = unite_dicts(result, d)

    return result


def files_dict_part(files_dict, path):
    for subdir in splitall(path):
        files_dict = files_dict[subdir]
    return files_dict


def calc_selected_set(files_dict: Union[dict, transmission_rpc.File]):
    """
    This method looks through the files_dict and returns all values of 'selected' key in file items
    Basing on the output we can conclude if all files are (de)selected or mixed
    :return: one of {True}, {False} or {True, False}
    """
    if isinstance(files_dict, transmission_rpc.File):
        return {files_dict.selected}

    selected_set = set()
    for item in files_dict.values():
        if isinstance(files_dict, transmission_rpc.File):
            selected_set.add(files_dict.selected)
        else:
            selected_set.union(calc_selected_set(item))
    return selected_set


def extract_filename(h: CaseInsensitiveDict) -> Optional[str]:
    """
    Extracts filename from headers of requests.Response
    :param h: headers dict
    :return: filename or None
    """
    d = h['content-disposition']
    found = re.findall("filename=(.+)", d)
    if not found:
        return None
    return found[0]
