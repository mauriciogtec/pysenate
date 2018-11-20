# pysenate

The website of the U.S. Senate contains all voting information of legislations since 1989. These data is already computer-friendly, available in `.xml` format. 

This lightweight python package provides utilities for downloading U.S. Senate voting data and metadata into a local project, storing it into `.csv` format--making it amenable for use with `pandas`. The functions provided also help to maintain the data updates as new roll call votes are issued. It uses `BeautifulSoup (bs4)` and `requests` as principal tools.

## Installation

```bash
pip install git+https://github.com/mauriciogtec/pysenate.git
```

## Starting a project

The first step is to open python in desired directory where the project will be hosted (make sure to have writing permissions), and run the following code from the Python REPL or a jupyter notebook

```python
import pysenate
pysenate.projectinit()
```

This will create the following project structure

```
config.yml
data/
    rollcalls/
```

## Step 1: Extract urls and general info from legislation sessions

For this, run the command

```python
tbl = urls_to_sessions()
```

```nohighlight
Found option save=True (default), saving a copy to ./data/sessionurls.csv
```

```python
tbl.head()
```

```nohighlight
   year  congress  session              label               xml
0  2018       115        2  2018 (115th, 2nd)  https://... .xml
1  2017       115        1  2017 (115th, 1st)  https://... .xml
2  2016       114        2  2016 (114th, 2nd)  https://... .xml
3  2015       114        1  2015 (114th, 1st)  https://... .xml
4  2014       113        2  2014 (113th, 2nd)  https://... .xml
```


## Extracting bill metadata by year

