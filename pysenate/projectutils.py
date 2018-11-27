from os import mkdir
from os.path import exists
from typing import List

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

    # check if data folders exist
    datapath = path + '/data'
    rollcallpath = path + '/data/rollcalls'
    batchpath = path + '/data/batch'
    if not exists(path):
        mkdir(path)
    if not exists(datapath):
        mkdir(datapath)
    if not exists(rollcallpath):
        mkdir(rollcallpath)
    if not exists(batchpath):
        mkdir(batchpath)

    # create config file
    configyml = "years: {}\nlastupdate: {}\n".format(years, None)
    fn = path + "/config.yml"
    with open(fn, 'w') as file:
        file.write(configyml)

    return 0
    