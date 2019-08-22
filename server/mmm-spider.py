#!/usr/bin/env python

import config as mmm_config
import packdb
import click
import os.path
import os

@click.command()
@click.option('--config', default=os.path.expanduser('~') + '/.config/mmmrc', help='config file')
@click.option('--empty', default=False, help='create new file')
@click.argument('name')
def main(config, empty, name):
    mmm_config.init(config)
    dirs = mmm_config.section('cache')['html']
    if os.path.exists(dirs):
        os.makedirs(dirs)
    dirs = mmm_config.section('package')['future']
    if os.path.exists(dirs):
        os.makedirs(dirs)
    dirs = mmm_config.section('package')['latest']
    if os.path.exists(dirs):
        os.makedirs(dirs)
    
    
    if empty:
        # unpack latest
        pass
    
    packdb._diff_list()
    
    # pack and rename
    

if __name__ == '__main__':
    main()