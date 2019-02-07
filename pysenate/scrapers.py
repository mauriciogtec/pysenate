# Libraries ===========

# system utils
import time
from datetime import date

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

# Global variables and URL construction =====
def httpheaders():
    return {'User-Agent': 'Mozilla/5.0'}

def domain():
    return 'https://www.senate.gov/'

def sessionlisturl():
    return domain() + '/legislative/votes.htm'

def rollcallurl(congress, session, vote_number):
    return domain() + 'legislative/LIS/roll_call_votes/vote{}{}/vote_{}_{}_{:05d}.xml'.\
                format(congress, session, congress, session, vote_number)

def sessionurl(congress, session):
    return domain() + 'legislative/LIS/roll_call_lists/vote_menu_{}_{}.xml'.format(congress, session)

def billinfourl(congress, number, what):
    assert what in ['senate-bill', 'senate-resolution', 'house-concurrent-resolution']
    return 'https://www.congress.gov/bill/{}th-congress/{}/{}/all-info'.format(congress, what, number)

# Request and parse ===================
def read_soup(url, parser):
    try:
        req = requests.get(url, headers = httpheaders()).content
        if len(req) == 0:
            raise ValueError
        bs = BeautifulSoup(req, parser)
        return bs
    except ValueError:
        print("connection established but content is null")
        return None
    except AttributeError:
        print('Error while trying to parse xml with beautiful soup')
        return None
    except Exception as e:
        print(e)
        return None

def latest_available():
    """
    returns: the most recent vote information available.
    description: it's meant to be useful for querying if the currently stored data is up-to-date
    """
    url = 'https://www.senate.gov/legislative/votes.htm'
    bs = read_soup(url, 'html.parser')
    return


# Process information =============
def rollcall_details(
        congress=None, 
        session=None, 
        vote_number=None, 
        url=None, 
        save=False,
        path="."):
    # validate input
    assert url is None or url[-4:] == '.xml', "please provide url of .xml of session details"
    assert url != None or (congress != None and session != None and vote_number != None), "if url is not provide, must provide congress, session and vote number"
    if url == None:
        url = rollcallurl(congress, session, vote_number)

    # obtain parsed xml
    bs = read_soup(url, 'xml')
    if bs == None:
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
        fn = "{}/data/rollcalls/{}.csv".format(path, url[-20:-4])
        print("Found option save=True, saving a copy to", fn)
        try:
            df.to_csv(fn, index=False)
        except PermissionError as e:
            print('Unable to save, check project folder permissions')
        except FileNotFoundError:
            print('Could not find ' + path + '/data/. Are you in project folder? Run pysenate.projectinit() first')

    return df


def session_details(
    congress=None, 
    session=None, 
    url=None, 
    save=False,
    path="."):
    # validate input
    assert url == None or url[-4:] == '.xml', "please provide url of .xml of session details"
    assert url != None or (congress != None and session != None), "if url is not provide, must provide congress and session"
    if url == None:
        url = sessionurl(congress, session)

    # obtain parsed xml
    bs = read_soup(url, 'xml')
    if bs == None:
        return None

    # process detailed information
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
        fn = "{}/data/{}.csv".format(path, url[-19:-4])
        print("Found option save=True, saving a copy to ", fn)
        try:
            df.to_csv(fn, index=False)
        except PermissionError as e:
            print('Unable to save, check project folder permissions')
        except FileNotFoundError:
            print('Could not find ' + fn + 'Are you in project folder? Run pysenate.projectinit() first')


    return df

def list_sessions(save=False, path="."):
    # read html or catch error
    bs = read_soup(sessionlisturl(), 'html.parser')
    if bs == None:
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
        url.append(domain() + x['href'])
    
    xml = [re.sub('.htm', '.xml', x) for x in url]

    df = pd.DataFrame({'year': year, 'congress': congress, 'session': session,
        'label': text, 'url': xml})

    # save to data/
    if save:
        print("Found option save=True, saving a copy to <path>/data/session_list.csv")
        try:
            df.to_csv(path + '/data/session_list.csv', index=False)
        except PermissionError as e:
            print('Unable to save, check project folder permissions')
        except FileNotFoundError:
            print('Could not find ' + path + '. Are you in project folder? Run pysenate.projectinit() first')

    return df

# Batch extraction ===============

def rollcall_batch(
    congress: int, 
    session: int, 
    fmt: str = 'dict',
    save: bool = False,
    path: str = ".",
    verbose:bool = False, 
    min_vote_date: date = date(1900, 1, 1)):

    # validate input
    assert fmt in ['dict', 'concat'], 'valid formats are "dict" and "concat"'
    assert min_vote_date
    # obtain list of all available sessions
    sessdetails = session_details(congress, session)
    if sessdetails.shape[0] == 0:
        return

    # extract detail for each rollcall
    rollcall_results = []
    for rollcall, d in zip(sessdetails.vote_number.values, sessdetails.vote_date.values):
        # this is useful
        if d < min_vote_date:
            continue

        result = rollcall_details(
            congress=congress, 
            session=session, 
            vote_number=rollcall, 
            save=False,
            path=path)
        result.insert(0, 'vote_number', [rollcall] * result.shape[0])
        result.insert(0, 'date', [d] * result.shape[0])

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
        fn = "{}/data/batch_data/rollcall_batch_{}_{}.csv".format(path, congress, session)
        print("Found option save=True, saving a copy to", fn)
        df = pd.concat(rollcall_results)
        df.to_csv(fn, index=False)

    return df


### Autoupdate

def fetch_all_since(d: date, save: bool = False, path="."):
    assert isinstance(d, date)
    sesslist = list_sessions(path=path)
    sesslist = sesslist[sesslist.year >= d.year]
    
    # exit program if empty
    n = sesslist.shape[0]
    if n == 0:
        return

    # now bring all
    dfs = [rollcall_batch(
        sesslist.congress[i], 
        sesslist.session[i], 
        min_vote_date=d,
        save=save,
        path=path) for i in range(n)]
    
    return pd.concat(dfs)
    
    
# --- This one takes a long time but get all we need # --------------

def billinfo(congress, number, what):
    url = billinfourl(congress, number, what)
    bs = read_soup(url, 'html.parser')

    bill = 'S.{}'.format(number) 

    # TO-DO!: obtain ALL titles not just one
    title = bs.find(class_='titles-row').p.text.strip()

    # overview table (sponsor, committee, latest)
    overview = bs.find(class_='overview').table
    overviewvals = list(overview.find_all('td'))
    sponsorinfo = overviewvals[0].text.strip()
    committee = overviewvals[1].text.strip()
    latestaction = overviewvals[2].text.strip()

    # parse the sponsor info form above
    r = 'Sen\.[ ]+(.+) \[(\w+)-(\w{2})'
    rematch = re.search(r, sponsorinfo)
    sponsor, party, state = [rematch.group(i) for i in range(1, 4)]

    # now tracker information
    tracker_banner = bs.find(class_='selected last').contents[0]
    all_actions =  bs.find(id='allActions-content').table
    all_actions_str = ''
    rows = all_actions.tbody.find_all('tr')
    for i, row in enumerate(rows):
        d, c, a = list(row.find_all('td'))
        all_actions_str += '{}\t{}\t{}'.format(d.text, c.text, a.text)
        if i < len(rows) - 1:
            all_actions_str += '\n'

    # cosponsors
    cosponsorsinfo = bs.find(id='cosponsors-content')
    entries = cosponsorsinfo.tbody.find_all('td', class_='actions')
    cosponsors = []
    for d in entries:
        r = '\\nSen\. (.+) \[.*'
        rematch = re.search(r, d.text)
        c = rematch.group(1)
        cosponsors.append(c)

    return bill, title, sponsor, party, state, all_actions_str, cosponsors

# restring = '(S.\d+).*- (.*)\.(\d+th.*)'
# header = bs.h1.text
# reparse = re.search(restring, header)
# bill, title = reparse.group(1), reparse.group(2)
# table = bs.find(class_='overview').


