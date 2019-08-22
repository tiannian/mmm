import requests
from lxml import etree
import os.path
import json
import config
import hashlib

def _fetch_page(num):
    url_prefix = 'https://www.curseforge.com/minecraft/mc-mods?page=%s'
    cache_path = config.section('cache')['html'] + 'html_%s.html' % num
    return _cache_fetch(url_prefix % num, cache_path, _parse_page)

def _parse_page(_elem):
    li = _parse_mod_list(_elem)
    total = _parse_pages_total(_elem)
    return li, total

def _parse_mod_list(_elem):
    mods_list_xpath = '//div[@class="my-2"]'
    mods_raw_list = _elem.xpath(mods_list_xpath)
    mods_list = []
    for mod in mods_raw_list:
        info = _parse_mod_info(mod)
        mods_list.append(info)
    return mods_list

def _parse_mod_info(_elem):
    url_prefix = 'https://www.curseforge.com%s'
    info = {}
    # parse id and author
    _container = _elem[0]
    _info_field = _container[1]
    _name_and_author = _info_field[0]
    
    # name
    _name = _name_and_author[0]
    _mod_name = _name[0].text
    _mod_link = _name.get('href')
    info['name'] = _mod_name
    hasher = hashlib.sha3_256()
    hasher.update(_mod_name.encode())
    info['hash'] = hasher.hexdigest()
    info['link'] = url_prefix % _mod_link
    
    # author
    author = {}
    _author = _name_and_author[2]
    author['name'] = _author.text.strip()
    author['link'] = url_prefix % _author.get('href')
    info['author'] = author
    
    # time
    _statics_and_time = _info_field[1]
    _update_time = _statics_and_time[1][0]
    info['update_time'] = int(_update_time.get('data-epoch'))
    
    _create_time = _statics_and_time[2][0]
    info['create_time'] = int(_create_time.get('data-epoch'))
    
    # description
    _description = _info_field[2]
    info['description'] = _description.text.strip()
    return info

def _parse_pages_total(_elem):
    xpath_pages = '//a[@class="pagination-item"]'
    total = _elem.xpath(xpath_pages)[-1]
    return int(total[0].text)

def _diff_list():
    hash_map = {}
    print('Fetch page 1 ...')
    li, total = _fetch_page(1)
    for mod in li:
        hash_map[mod['name']] = mod['hash']
        _deal_mod(mod)
    print('Fetch page 1 success, got %d mods' % (len(li)))
    for x in range(2, total + 1):
        print('Fetch page %d ...' % x)
        li, _ = _fetch_page(x)
        for mod in li:
            hash_map[mod['name']] = mod['hash']
            _deal_mod(mod)
        print('Fetch page %d success, got %d mods' % (x, len(li)))
    indexfile = open(config.section('package')['future'] + 'index.json', 'w+')
    json.dump(hash_map, indexfile, indent = 4)

def _deal_mod(mod):
    _name = mod['hash']
    print('Fetch mod %s ...' % mod['name'])
    if os.path.exists(config.section('package')['latest'] + _name + '.json'):
        # diff check
        pass
    else :
        # create file
        _create_mod(mod)
    print('Fetch mod %s success.' % mod['name'])

def _create_mod(mod):
    _name = mod['hash']
    modfile = open(config.section('package')['future'] + _name + '.json', "w+")
    mod['dependencies'] = _fetch_dependencies(mod)
    mod['files'] = _fetch_files(mod)
    json.dump(mod, modfile, indent = 4)

def _cache_fetch(url, cache_path, handler):
    if os.path.exists(cache_path):
        file = open(cache_path, 'r')
        text = file.read()
        _element = etree.HTML(text)
        return (handler(_element))
    else:
        r = requests.get(url)
        file = open(cache_path, 'w+')
        file.write(r.text)
        _element = etree.HTML(r.text)
        return (handler(_element))

def _fetch_dependencies(mod):
    dependencies_url = mod['link'] + '/relations/dependencies'
    cache_path = config.section('cache')['html'] + 'html_%s_dependencies.html' % (mod['hash'])
    return _cache_fetch(dependencies_url, cache_path, _parse_dependencies)

def _parse_dependencies(_element):
    lis = _element.xpath('//li[@class="project-listing-row box py-3 px-4 flex flex-col lg:flex-row lg:items-center mb-2"]')
    deps = []
    for li in lis:
        _title = li[0][1][0][0]
        deps.append(_title.text.strip())
    return deps

def _fetch_files(mod):
    files, total = _fetch_files_page(mod, 1)
    for page in range(2, total + 1):
        li, _ =_fetch_files_page(mod, page)
        files += li
    return files

def _fetch_files_page(mod, page):
    fetch_url = (mod['link'] + '/files/all?page=' + str(page))
    cache_path = config.section('cache')['html'] + 'html_%s_files_%s.html' % (mod['hash'], page)
    return _cache_fetch(fetch_url, cache_path, _parse_files)

_type_map = {
    'R': 'release',
    'B': 'beta',
    'A': 'alpha',
}

def _parse_files(_element):
    _total = _element.xpath('//a[@class="pagination-item"]')
    total = 1
    if len(_total) != 0:
        total = int(_total[-1][0].text)
    li = []
    _tbody = _element.xpath('//tbody')
    for tr in _tbody:
        info = {}
        _type = tr[0][0][0]
        info['type'] = _type_map[_type[0].text.strip()]
        _file = tr[0][1][0]
        info['id'] = _file.get('href').strip().split('/')[-1]
        info['name'] = _file.text.strip()
        _uploaded = tr[0][3][0]
        info['upload_time'] = int(_uploaded.get('data-epoch'))
        _game_version = tr[0][4][0]
        info['game_version'] = _game_version[0].text.strip()
        if len(_game_version) == 2:
            info['version_range'] = _game_version[1].text.strip()
        else:
            info['version_range'] = 0
        info['download_link'] = 'https://www.curseforge.com/minecraft/mc-mods/tinkers-construct/download/%s/file' % info['id']
        li.append(info)
    return li, total

if __name__ == '__main__':
    _diff_list()