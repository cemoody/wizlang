import urllib2
import json
import nltk
import unicodedata
import sets
import sys
import re
import time
import difflib
import string
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

@persist_to_file
def get_wiki_name(name, get_response=False):
    """Use the WP API to get the most likely diambiguation"""
    for _ in range(3):
        url = r"http://en.wikipedia.org/w/api.php?action=opensearch&search=" +\
              urllib2.quote(name) + \
              r"&limit=1&format=json"
        response = urllib2.urlopen(url).read()
        odata = json.loads(response)
        if len(odata) > 1:
            break
        else:
            time.sleep(0.1)
    else:
        if get_response:
            return None, None
        else:
            return None
    ptitle = odata[1][0]
    ptitle = unicodedata.normalize('NFKD', ptitle).encode('ascii','ignore')
    if get_response:
        return ptitle, response
    else:
        return ptitle

@persist_to_file
def wiki_canonize(phrase, canon, n=1, use_wiki=True):
    phrase = phrase.replace('\n','').replace('\t','').replace('\r','')
    phrase = phrase.strip()
    wiki = ""
    if use_wiki:
        try:
            wiki = get_wiki_name(phrase)
        except:
            wiki = None
        if wiki is not None:
            phrase = wiki
    phrase = phrase.replace(' ', '_')
    phrase = phrase.strip().lower()
    for i in range(5):
        phrase = phrase.replace('  ', ' ')
    if phrase in canon: return phrase, wiki
    phrase = phrase.replace('-', '_')
    for p in string.punctuation:
        phrase = phrase.replace(p, '')
    if phrase in canon: return phrase, wiki
    phrase = phrase.replace(' ', '_')
    if phrase in canon: return phrase, wiki
    phrases = difflib.get_close_matches(phrase, canon, n)
    phrases = [unicodedata.normalize('NFKD', unicode(phrase)).encode('ascii','ignore') for phrase in phrases]
    return phrases[0], wiki

@persist_to_file
def wiki_decanonize(phrase, c2t, response=True, n=2):
    if phrase in c2t: return c2t[phrase], None
    phrase = phrase.replace('_', ' ')
    if phrase in c2t: return c2t[phrase], None
    phrase = phrase.capitalize()
    if phrase in c2t: return c2t[phrase], None
    wiki, response= get_wiki_name(phrase, get_response=True)
    if wiki is not None:
        return wiki, response 
    else:
        phrases = difflib.get_close_matches(phrase, c2t.values(), n)
        return phrases[0], None

@persist_to_file
def get_wiki_html(name):
    url = r"http://en.wikipedia.org/w/api.php?action=parse&page=" + \
            urllib2.quote(name) +\
            "&format=json&prop=text&section=0&redirects"
    text = urllib2.urlopen(url).read()
    response = json.loads(text)
    return response

@persist_to_file
def get_wiki_spell(name):
    url2  = r"http://en.wikipedia.org/w/api.php?action=opensearch&search="
    url2 += urllib2.quote(name)
    url2 += r"&format=json&callback=spellcheck"
    text = urllib2.urlopen(url2).read()
    text = text.strip(')').replace('spellcheck(','')
    response = json.loads(text)
    return response

@persist_to_file
def pick_wiki(name):
    candidates = get_wiki_spell(name)
    if len(candidates[1]) == 0:
        return None, None
    for candidate in candidates[1]:
        cleaned = process_wiki(candidate)
        text = cleaned['description']
        if 'Look up' in text:
            print 'skipped wiki look up', candidate
            continue
        elif 'may refer to' in text:
            print 'skipped wiki disambiguation', candidate
            continue            
        else:
            break
    return candidate, cleaned

@persist_to_file
def process_wiki(name, length=20, max_char=300, response=None):
    """Remove excess paragraphs, break out the images, etc."""
    #This gets the first section, gets the text of to a number of words
    # and gets the main image
    if response is None:
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
    description = description.replace(' ,', ',')
    description = description.replace(' .', '.')
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

apikey = r"AIzaSyA_9a3q72NzxKeAkkER9zSDJ-l0anluQKQ"
@persist_to_file
def get_freebase_types(name, trying = True):
    types = None
    name = urllib2.quote(name)
    url = r"https://www.googleapis.com/freebase/v1/search?filter=%28all+name%3A%22"
    url += name
    url += r"%22%29&output=%28type%29&key=AIzaSyA_9a3q72NzxKeAkkER9zSDJ-l0anluQKQ&limit=1"
    fh = urllib2.urlopen(url)
    response = json.load(fh)
    notable = response['result'][0]['notable']['name']
    types = [x['name'] for x in response['result'][0]['output']['type']["/type/object/type"]]
    types = [t for t in types if 'topic' not in t.lower()]
    types = [t for t in types if 'ontology' not in t.lower()]
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
