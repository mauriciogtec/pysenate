# Libraries ===========

# system utils
import time

# Scraping & text processing
import requests
from bs4 import BeautifulSoup
from urllib.error import HTTPError

# Data and config
import yaml
import pandas as pd

# Dates, time, text
import datetime as dt
from calendar import month_abbr
import re

# Globals and URL construction =====
def httpheaders():
    return {'User-Agent': 'Mozilla/5.0'}

def rollcallurl(congress, session, vote_number):
    return 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote{}{}/vote_{}_{}_{:05d}.xml'.\
                format(congress, session, congress, session, vote_number)

def sessionurl(congress, year):
    return 'https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{}_{}.xml'.format(congress, session)    

# Extractors ========
def rollcall_details(
    congress:int = None,
    session:int = None,
    vote_number:int = None,
    url:str = None,
    save:bool = False):
    # validate input
    assert url is None or url[-4:] == '.xml', "please provide url of .xml of session details"
    assert url != None or (congress != None and session != None and vote_number != None), "if url is not provide, must provide congress, session and vote number"
    if url == None:
        url = rollcallurl(congress, session, vote_number)

    try:
        xml = requests.get(url, headers = httpheaders()).content
        if len(xml) == 0:
            raise ValueError('connection established but read null content')
        bs = BeautifulSoup(xml, 'xml')
    except HTTPError as e:
        print(e, 'Could not establish connection')
        return None
    except ValueError as e:
        print(e, 'Connection established but received empty response')
        return None 
    except AttributeError as e:
        print(e, 'Error while trying to parse xml with beautiful soup')
        return None

    senator = []
    party = []
    state = []
    vote = []
    lis_member_id = []

    for x in bs.members.find_all('member'):
        senator.append('{}, {}'.format(x.first_name.text, x.last_name.text))
        party.append(x.party.text)
        state.append(x.state.text)
        vote.append(x.vote_cast.text)
        lis_member_id.append(x.lis_member_id.text)

    df = pd.DataFrame({'senator': senator, 'party': party, 'state': state, 'vote': vote, 'lis_member_id': lis_member_id})

    # save to data/
    if save:
        fn = "./data/rollcalls/{}.csv".format(url[-20:-4])
        print("Found option save=True, saving a copy to", fn)
        try:
            df.to_csv(fn, index=False)
        except PermissionError as e:
            print('Unable to save, check project folder permissions')
        except FileNotFoundError:
            print('Could not find folder .data/. Are you in project folder? Run pysenate.projectinit() first')

    return df


def session_details(
    congress:int = None,
    session:int = None,
    url:str = None, 
    save:bool = False):
    # validate input
    assert url == None or url[-4:] == '.xml', "please provide url of .xml of session details"
    assert url != None or (congress != None and session != None), "if url is not provide, must provide congress and session"
    if url == None:
        url = sessionurl(congress, session)

    # read and parse detailed information
    try:
        xml = requests.get(url, headers = httpheaders()).content
        if len(xml) == 0:
            raise ValueError('connection established but read null content')
        bs = BeautifulSoup(xml, 'xml')
    except HTTPError as e:
        print(e, 'Could not establish connection')
        return None
    except ValueError as e:
        print(e, 'Connection established but received empty response')
        return None 
    except AttributeError as e:
        print(e, 'Error while trying to parse xml with beautiful soup')
        return None
    
    congress = int(bs.congress.text)
    session = int(bs.session.text)
    year = int(bs.congress_year.text)

    fn = '{}.csv'.format(year)
    colnames = ['vote_number', 'title', 'yeas', 'nays', 'result', \
        'issue', 'question', 'vote_date', 'url']

    baseurl = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote{}{}/vote_{}_{}_'.\
        format(congress, session, congress, session)

    # extract all information
    rows = []
    for v in bs.find('votes').find_all('vote'):
        # extraction is straightforward from the xml            
        vote_number_str = v.vote_number.text
        vote_number = int(vote_number_str)
        title = re.sub('[\n\r\t]', '', v.title.text).strip() # trim lead trail space and remove line breaks 
        yeas = int(v.vote_tally.yeas.text)
        nays = int(v.vote_tally.nays.text)
        result = v.result.text
        issue = v.issue.text
        question = re.sub('[\n\r\t]', '', v.question.text).strip() # trim lead trail space and remove line breaks

        # parsing the date will require some creativity
        vote_date_text_format = v.vote_date.text
        vote_date_regex = re.search('(\d{2})-(\w{3})', vote_date_text_format)
        vote_day = int(vote_date_regex.group(1))
        vote_month_abbr = vote_date_regex.group(2)
        vote_month = list(month_abbr).index(vote_month_abbr)
        date = dt.date(year, vote_month, vote_day)

        # add url to additional vote information
        linkurl = baseurl + '{}.xml'.format(vote_number_str)

        # let's put it together in data frame
        row_data = [vote_number, title, yeas, nays, result, issue, question, date, linkurl]
        rows.append(pd.DataFrame([row_data], columns=colnames))      
        
    # ensemble in dataset
    df = pd.concat(rows, ignore_index=True)

    # save to data/
    if save:
        fn = "./data/{}.csv".format(url[-19:-4])
        print("Found option save=True, saving a copy to ", fn)
        try:
            df.to_csv(fn, index=False)
        except PermissionError as e:
            print('Unable to save, check project folder permissions')
        except FileNotFoundError:
            print('Could not find folder .data/. Are you in project folder? Run pysenate.projectinit() first')


    return df

def list_sessions(save:bool = False):
    #
    domain = 'https://www.senate.gov'
    url = domain + '/legislative/votes.htm'

    # read html or catch error
    try:
        html = requests.get(url, headers =  httpheaders()).content
        if len(html) == 0:
            raise ValueError
        bs = BeautifulSoup(html, 'html.parser')
    except HTTPError as e:
        print('Could not establish connection, check connection and try again...')
        return None
    except ValueError as e:
        print('HTTP response empty, check connection and try again; if error persists, please submit an issue...')
        return None 
    except AttributeError as e:
        print(e, 'Error with beautiful soup html parser; please submit an issue')
        return None
    
    # extract links and create table
    # must be a vote menu and text start with a year (as opposed to some text being detailed sessions)
    atags = bs.find_all("a", href=re.compile('vote_menu'), text=re.compile("^\d{4} "))
    text = []
    url = []
    congress = []
    session = []
    year = []
    for x in atags:
        re_parse = re.search('(\d{4}).*(\d{3}).*(\d)', x.text)
        c, s, y = re_parse.group(2), re_parse.group(3), re_parse.group(1)
        congress.append(int(c))
        session.append(int(s))
        year.append(int(y))
        text.append(x.text)
        url.append(domain + x['href'])
    
    xml = [re.sub('.htm', '.xml', x) for x in url]

    df = pd.DataFrame({'year': year, 'congress': congress, 'session': session,
        'label': text, 'url': xml})

    # save to data/
    if save:
        print("Found option save=True, saving a copy to ./data/session_list.csv")
        try:
            df.to_csv('./data/session_list.csv', index=False)
        except PermissionError as e:
            print('Unable to save, check project folder permissions')
        except FileNotFoundError:
            print('Could not find folder .data/. Are you in project folder? Run pysenate.projectinit() first')

    return df

# Batch extraction ===============

def rollcall_batch(
    congress:int, 
    session:int, 
    fmt:str='dict', 
    save:bool=False, 
    verbose:bool=True):
    # validate input
    assert fmt in ['dict', 'concat'], 'valid formats are "dict" and "concat"'

    # obtain list of all available sessions
    rollcall_numbers = list(session_details(congress, session).vote_number)

    # extract detail for each rollcall
    rollcall_results = []
    for rollcall in rollcall_numbers:
        result = rollcall_details(
            congress=congress, 
            session=session, 
            vote_number=rollcall, 
            save=save)
        result.insert(0, 'vote_number', [rollcall] * result.shape[0])

        # Good citizenship: wait 2 seconds
        print("Finished vote {}, pausing 2 sec...".format(rollcall))
        time.sleep(2.0)
        rollcall_results.append(result)

    # Create output according to fmt
    df = pd.concat(rollcall_results)
    if fmt == 'dict':
        output = {v.vote_number[1]: v for v in rollcall_results}
    elif fmt == 'concat':
        output = df

    if save:
        fn = "./data/batch_data/rollcall_batch_{}_{}.csv".format(congress, session)
        print("Found option save=True, saving a copy to", fn)
        df = pd.concat(rollcall_results)
        df.to_csv(fn)

    return df

