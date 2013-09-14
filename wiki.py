import urllib2
import json
import nltk
import unicodedata
import sets
import re
import time
from BeautifulSoup import BeautifulSoup
from utils import *

def exists(url):
    request = urllib2.Request(url)
    request.get_method = lambda : 'HEAD'
    try:
        response = urllib2.urlopen(request)
        return True
    except:
        return False

def get_omdb(name, google_images=False, check=False):
    """Search for the most relevant movie name on OMDB,
    then using that IMDB ID lookup get the rest of the
    information: description, actors, etc. Optionally 
    search Google Images for the poster image and hotlink
    it"""
    url = r"http://www.omdbapi.com/?t=%s" % urllib2.quote(name)
    response = urllib2.urlopen(url)
    odata = json.load(response)
    if 'Error' in odata.keys():
        print 'OMDB Error: %s' % name
        return None
    if check and not exists(odata['Poster']):
        print "IMDB Image not Found for %s" % name
        return None
    data = {k.lower():v for k, v in odata.iteritems()}
    return data

def to_title(title):
    out = ""
    for word in title.split(' '):
        word = word[0].upper() + word[1:]
        out += word + " "
    return out

def get_wiki_name(name):
    """Use the WP API to get the most likely diambiguation"""
    for _ in range(3):
        url = r"http://en.wikipedia.org/w/api.php?action=opensearch&search=" +\
              urllib2.quote(name) + \
              r"&limit=1&format=json"
        response = urllib2.urlopen(url)
        odata = json.load(response)
        if len(odata[1]) > 1:
            break
        else:
            time.sleep(0.1)
    else:
        return name
    ptitle = odata[1][0]
    ptitle = unicodedata.normalize('NFKD', ptitle).encode('ascii','ignore')
    return ptitle

def get_wiki_html(name):
    url = r"http://en.wikipedia.org/w/api.php?action=parse&page=" + \
            urllib2.quote(name) +\
            "&format=json&prop=text&section=0"
    response = json.load(urllib2.urlopen(url))
    return response

def process_wiki(name, length=20, max_char=300):
    """Remove excess paragraphs, break out the images, etc."""
    #This gets the first section, gets the text of to a number of words
    # and gets the main image
    response = get_wiki_html(name)
    html = response['parse']['text']['*']
    valid_tags = ['p']
    soup = BeautifulSoup(html)  
    newhtml = ''
    for tag in soup.findAll(recursive=False):
        if len(newhtml.split(' ')) > length:
            continue
        if 'p' == tag.name:
            for c in tag.contents:
                newhtml += ' ' +unicode(c)
    description = nltk.clean_html(newhtml)
    description = re.sub(r'\([^)]*\)', '', description)
    description = re.sub(r'\[[^)]*\]', '', description)
    if len(description) > max_char:
        description = description[:max_char] + '...'
    soup = BeautifulSoup(html)  
    newhtml = ''
    for tag in soup.findAll(recursive=False):
        good = True
        if 'div' == tag.name or 'table' == tag.name:
            if len(tag.attrs) > 0:
                if any(['class' in a for a in tag.attrs]):
                    if 'meta' in tag['class']:
                        good = False
        if good:
            for c in tag.contents:
                newhtml += ' ' +unicode(c)
    img = "http://upload.wikimedia.org/wikipedia/en/b/bc/Wiki.png"
    for tag in BeautifulSoup(newhtml).findAll(recursive=True):
        if 'img' == tag.name:
            if tag['width'] > 70:
                img = "http:" + tag['src']
                break
    url = "http://en.wikipedia.org/wiki/" + name
    title = to_title(name)
    cleaned = dict(img=img, description=description, url=url,
                   title=title, name=name)   
    return cleaned

def get_freebase_types(name, trying = True):
    name = urllib2.quote(name)
    badtypes = sets.Set(['Topic'])
    url = r"https://www.googleapis.com/freebase/v1/search?indent=true&filter=%28all+name" +\
            "%3A%22" + name + "%22%29&output=%28type%29"
    try:
        response = json.load(urllib2.urlopen(url))
    except:
        print 'Failed in freebase for %s' % name
        return None, []
    try:
        notable = response['result'][0]['notable']['name']
    except:
        notable = None
    types = [x['name'] for x in response['result'][0]['output']['type']["/type/object/type"]]
    types = sets.Set(types)
    types = sets.Set([t for t in types if 'topic' not in t.lower()])
    types = sets.Set([t for t in types if 'ontology' not in t.lower()])
    return notable, types

def reject_result(result, kwargs):
    if len(result['description']) < 10:
        print "Short description"
        return True
    title = result['title'].lower()
    if 'blacklist' in kwargs:
        if '_' in result:
            for word in title.split('_'):
                for black in kwargs['blacklist']:
                    if black in word or black==word:
                        print "skipping", black, word
                        return True
        else:
            word = title
            for black in kwargs['blacklist']:
                if black in word or black==word:
                    print "skipping", black, word
                    return True
    return False
