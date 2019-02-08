from os import mkdir
from os.path import exists
from typing import List
from pysenate.scrapers import fetch_all_since
from datetime import date
import yaml

def projectinit(
    path: str='.', 
    years: List[int]= [2016, 2017, 2018]):
    """
    Creates the project structure at the specified path

    Parameters:
        [str] path: string with relative or absolute path to directory that will host project
        [List[int]] years: what years to keep updated
    Returns:
        It creates a project structure and a yaml config file at the specified path.
    """
    # validate input
    assert all([int(y) in range(1985, 2030) for y in years])

    # standardise path
    if path[-1] == '/':
        path = path[:-1]

    # check if data folders exist
    datapath = path + '/data'
    rollcallpath = path + '/data/rollcalls'
    batchpath = path + '/data/batch_data'
    if not exists(path):
        mkdir(path)
    if not exists(datapath):
        mkdir(datapath)
    if not exists(rollcallpath):
        mkdir(rollcallpath)
    if not exists(batchpath):
        mkdir(batchpath)

    # create config file
    configyml = {'years': years, 'path': path, 'lastupdate': date(min(years), 1, 1)}
    fn = path + "/config.yaml"
    with open(fn, 'w') as file:
        yaml.dump(configyml, file)

def update_data(configpath='config.yaml'):
    try:
        with open(configpath, 'r') as file:
            config = yaml.load(file)
    except FileNotFoundError as e:
        print("please provide project config file path or run pysenate.projectinit() first")
    finally: 
        lastupdate = config['lastupdate']
        savepath = config['path']
        fetch_all_since(lastupdate, path=savepath, save=True)
        config['lastupdate'] = date.today()
        with open(configpath, 'w') as file:
            yaml.dump(config, file)