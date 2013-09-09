import urllib2
import json
import beautifulsoup

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

def get_wiki(name):
    """Get the wikipedia text for this article"""
    url = (r"http://en.wikipedia.org/w/api.php?action=parse&page=%s" % name) + 
           r"&format=json&prop=text&section=0"
    response = urllib2.urlopen(url)
    odata = json.load(response)
    if 'error' in odata.keys():
        return None
    return data['parse']['text']

def process_wiki(text):
    """Remove excess paragraphs, break out the images, etc."""
    # Also remove the infobox
    return cleaned

