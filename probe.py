#!/usr/bin/env python3
import json
import re
import socket
import sys
from urllib.parse import urlparse

import requests

PROBE_URL_HTTP = 'http://google.com/generate_204'
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'}
RE_META_REFRESH = re.compile(r"<meta.*http-equiv=['\"]refresh['\"].*?url=['\"\s]*([A-Z/][^'\"\s]*).*?>", re.IGNORECASE)


def absolute_url(url, req):
    if url.startswith('/'):
        host = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(req.url))
        url = host + url
    return url


def meta_refresh(req):
    match = re.search(RE_META_REFRESH, req.text)
    if not match:
        return ''
    return absolute_url(match.group(1), req)


def location_header(req):
    # no location header present
    if 'Location' not in req.headers:
        return ''
    # return absolute url
    url = req.headers['Location']
    return absolute_url(url, req)


def dump_request(red_id, req):
    headers = open(f'{sys.argv[1]}/{red_id}.head', 'w')
    headers.write(json.dumps(dict(req.headers)))
    headers.close()
    body = open(f'{sys.argv[1]}/{red_id}.html', 'w')
    body.write(req.text)
    body.close()


def follow(red_id, url):
    if url == '':
        return []
    req = requests.get(url, allow_redirects=False, headers=HTTP_HEADERS)
    dump_request(red_id, req)
    # check url for potential redirects
    url_location = location_header(req)
    url_refresh = meta_refresh(req)
    # if redirects urls equal use generic redirect (R)
    if url_location == url_refresh:
        trace = follow(red_id + 'R', url_location)
    # if redirect urls differ follow both redirects and specify their types
    else:
        trace = follow(red_id + 'L', url_location)
        trace += follow(red_id + 'M', url_refresh)
    # append info about the current url
    trace = [{
        'ID': red_id,
        'URL': url,
        'IP_Address': socket.gethostbyname(urlparse(url).hostname),
        'HTTP_Code': req.status_code,
        'Location': url_location,
        'Refresh': url_refresh,
    }] + trace
    return trace


def main():
    # print usage if not called properly
    if len(sys.argv) != 2:
        print('usage: redirect.py <DUMPDIR>')
        sys.exit(1)
    # dump trace
    trace = json.dumps(follow('R', PROBE_URL_HTTP))
    f = open(f'{sys.argv[1]}/trace.json', 'w')
    f.write(trace)
    f.close()


if __name__ == "__main__":
    main()
