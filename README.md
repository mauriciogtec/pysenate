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
import pysenate as sen
sen.projectinit()
```

This will create the following project structure

```
config.yml
data/
    rollcalls/
    batch/
    auto/
```

## Basic extraction

### 1. Extract list and urls of available sessions

For this, run the command

```python
tbl = sen.list_sessions(save=True)
```

```nohighlight
Found option save=True, saving a copy to ./data/all_urls.csv
```

```python
tbl.head()
```

```nohighlight
   year  congress  session              label          url
0  2018       115        2  2018 (115th, 2nd)  https://...
1  2017       115        1  2017 (115th, 1st)  https://...
2  2016       114        2  2016 (114th, 2nd)  https://...
3  2015       114        1  2015 (114th, 1st)  https://...
4  2014       113        2  2014 (113th, 2nd)  https://...
```


### 2. Extract details of a session

```python
tbl2 = sen.session_details(congress=115, session=2, save=True)
```
```
Found option save=True, saving a copy to  ./data/vote_menu_115_2.csv
```

```python
tbl2.head()
```

```
vote_number         title   yeas  nays result     issue         question  vote_date          url
0  244  Confirmation M...    64    34  Confir    PN1860       On the Nom 2018-11-15  https://...
1  243  Motion to Tabl...    77    21  Agreed    S.J...  On the Motion t 2018-11-15  https://...
2  242  Motion to Invo...    63    36  Agreed    PN1860   On the Cloture 2018-11-14  https://...
3  241  Motion to Conc...    94     6  Agreed    S. 140           On the 2018-11-14  https://...
4  240  Motion to Invo...    93     5  Agreed    S. 140   On the Cloture 2018-11-13  https://...
```

Alternatively, we can provide the url directly

```python
url = 'https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_115_2.xml'
tbl2 = sen.session_details(congress=115, session=2)
```

### 3. Extract roll call


```python
tbl3 = sen.rollcall_details(congress=115, session=2, vote_number=244, save=True)
tbl3.head()
```

```nohighlight
               senator party state vote lis_member_id
0     Lamar, Alexander     R    TN  Yea          S289
1       Tammy, Baldwin     D    WI  Nay          S354
2       John, Barrasso     R    WY  Yea          S317
3      Michael, Bennet     D    CO  Yea          S330
4  Richard, Blumenthal     D    CT  Nay          S341
```

Similarly as with session details, we can provide the url directly.

```python
url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1152/vote_115_2_00244.xml'
tbl3 = sen.rollcall_details(url=url)
```

## Batch extraction

We are usually interested in comparing voting data from several sessions. One approach would be to call the function `rollcall_details` several times. Since this is a frequent operation, we have included this as a pre-built function.  

```python
tbl4 = sen.rollcall_batch(congress=115, session=2, fmt='concat', save=True)
```

```nohighlight
Found option save=True, saving a copy to ./data/rollcalls/vote_115_2_00244.csv
Finished vote 244, pausing 2 sec...
Found option save=True, saving a copy to ./data/rollcalls/vote_115_2_00243.csv
Finished vote 243, pausing 2 sec...
Found option save=True, saving a copy to ./data/rollcalls/vote_115_2_00242.csv
Finished vote 242, pausing 2 sec...
    ...  
    ...
```

```python
tbl4.head()
```

```nohighlight
   vote_number              senator party state vote lis_member_id
0          244     Lamar, Alexander     R    TN  Yea          S289
1          244       Tammy, Baldwin     D    WI  Nay          S354
2          244       John, Barrasso     R    WY  Yea          S317
3          244      Michael, Bennet     D    CO  Yea          S330
4          244  Richard, Blumenthal     D    CT  Nay          S341
```

```python
tb4.tail()
```

```nohighlight
    vote_number              senator party state vote lis_member_id
95            1    Elizabeth, Warren     D    MA  Nay          S366
96            1  Sheldon, Whitehouse     D    RI  Yea          S316
97            1        Roger, Wicker     R    MS  Yea          S318
98            1           Ron, Wyden     D    OR  Nay          S247
99            1          Todd, Young     R    IN  Yea          S391
```

It is also possible to keep the information in separate tables for each vote, choosing the option `fmt='dict'`.

## Auto-updating

It is not practical to download all the data every time it is needed. That would involve many new requests, and could be interpreted as an atack. Thus we can set-up the project so that it only looks for new rollcalls. To configure the options, we use the `config.yml` file, which by default looks something like

```yml
years: 
    - 2016 
    - 2017
    - 2018
lastupdate: None
```

The function `autoupdate` compares the value of `lastupdate` with the local stored data, and downloads the missing rollcalls.

```
```

## Offline data

To-do
