import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import HTMLParser


try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"


DB = os.path.join(xbmc.translatePath("special://database"), 'sceper.db')
BASE_URL = 'http://www.sceper.eu'
net = Net()
addon = Addon('plugin.video.sceper', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
content = addon.queries.get('content', None)
listitem = addon.queries.get('listitem', None)


def GetTitles(section, url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'sceper get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if int(startPage) > 1:
                pageUrl = url + '/page/' + startPage
        print pageUrl
        html = net.http_GET(pageUrl).content
        start = int(startPage)
        end = start + int(numOfPages)
        last = 2
        match  = re.search("/([\d]+)' class='last'", html)
        if match:
                last = int(match.group(1))

        print str(start) + ' : ' + str(end) + ' : ' + str(last)
        for page in range( start, min(last, end)):
                if ( page != start):
                        pageUrl = url + '/page/' + str(page)
                        html = net.http_GET(pageUrl).content
                ListTitles(section, html)
       	if end < last:
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title':  'Next..'})
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def ListTitles(section, html):
        print ' in ListTitles'
        html = html.encode('utf-8')
        match = re.compile('entry clearfix.+?href="(.+?)">(.+?)<.+?href="(.+?)".+?Download.+?</div>(.+?)</div>', re.DOTALL).findall(html)
        for url, title, img, content in match:
                addon.add_directory({'mode': 'GetLinks', 'url': url, 'content': content}, {'title':  title}, img= img)


def GetLinks(section, url): # Get Links
        print 'GETLINKS FROM URL: '+url
        html = net.http_GET(str(url)).content
        sources = []

        listitem = GetMediaInfo(html)
        print 'LISTITEM: '+str(listitem)
        content = html
        print'CONTENT: '+str(listitem)
        r = re.search('<strong>Links.*</strong>', html)
        if r:
                content = html[r.end():]
                
        r = re.search('commentblock', content)
        if r:
                content = content[:r.start()]

        match = re.compile('href="(.+?)"').findall(content)
        listitem = GetMediaInfo(content)
        for url in match:
                host = GetDomain(url)

                if 'Unknown' in host:
                                continue

                # ignore .rar files
                r = re.search('\.rar[(?:\.html|\.htm)]*', url, re.IGNORECASE)
                if r:
                        continue
                print '*****************************' + host + ' : ' + url
                title = url.rpartition('/')
                title = title[2].replace('.html', '')
                title = title.replace('.htm', '')
                title = title.replace ('-',' ')
                title = title.replace('_',' ')
                name = host+'-'+title
                hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
                sources.append(hosted_media)

                
        find = re.search('commentblock', html)
        if find:
                print 'in comments if'
                html = html[find.end():]
                CLEAN(html)###
                match = re.compile('<a href="(http://.+?)" rel="nofollow"', re.DOTALL).findall(html)
                match1 = re.compile(r'comment-page-numbers(.+?)<!--comments form -->', re.DOTALL).findall(html)
                match = re.compile('<a href="(htt.+?)" rel="nofollow"', re.DOTALL).findall(str(match1))
                print 'MATCH IS: '+str(match)
                print len(match)
                for url in match:
                        host = GetDomain(url)
                        if 'Unknown' in host:
                                continue

                        # ignore .rar files
                        r = re.search('\.rar[(?:\.html|\.htm)]*', url, re.IGNORECASE)
                        if r:
                                continue
                        try:
                                print 'in GetLinks if loop'
                                title = url.rpartition('/')
                                title = title[2].replace('.html', '')
                                title = title.replace('.htm', '')
                                title = title.replace ('-',' ')
                                title = title.replace('_',' ')
                                name = host+'-'+title
                                hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
                                sources.append(hosted_media)
                                print sources
                                print 'URL IS::: '+url
                        except:
                                continue
        source = urlresolver.choose_source(sources)
        if source: stream_url = source.resolve()
        else: stream_url = ''
        xbmc.Player().play(stream_url)




def PlayVideo(url, listitem):
        print 'in PlayVideo %s' % url
        stream_url = urlresolver.HostedMediaFile(url).resolve()
	xbmc.Player().play(stream_url, listitem)

def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain


def GetMediaInfo(html):
        listitem = xbmcgui.ListItem()
        match = re.search('og:title" content="(.+?) \((.+?)\)', html)
        if match:
                print match.group(1) + ' : ' + match.group(2)
                listitem.setInfo('video', {'Title': match.group(1), 'Year': int(match.group(2)) } )
        return listitem

def Categories(section):  #categories

        html = net.http_GET(BASE_URL).content
        addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': BASE_URL + '/category/' + section,
                             'startPage': '1', 'numOfPages': '2'}, {'title':  'All'})

        match = re.compile('class="cat-item.+?/category/' + section + '/(.+?)".+?>(.+?)<').findall(html)
        for cat, title in match:
                url = BASE_URL + '/category/' + section + '/' + cat
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url,
                                     'startPage': '1', 'numOfPages': '2'}, {'title':  title})
        
        addon.add_directory({'mode': 'GetSearchQuery', 'section': section},  {'title':  'Search'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MainMenu():    #homescreen
        addon.add_directory({'mode': 'Categories', 'section': 'movies'},  {'title':  'Movies'})
        addon.add_directory({'mode': 'Categories', 'section': 'tv-shows'},  {'title':  'TV Shows'})
        addon.add_directory({'mode': 'GetTitles', 'section': 'ALL', 'url': BASE_URL + '/category/staff-recommended',
                             'startPage': '1', 'numOfPages': '2'}, {'title':  'Staff Recommended'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))



def BrowseGenre(content):
        match = re.compile('href="(.+?)">(.+?)<').findall(content)
        for url, title in match:
                addon.add_directory({'mode': 'GetLinks', 'url': url, 'startPage': '1', 'numOfPages': '3'}, {'title':  title.encode('utf-8')})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetSearchQuery(section):
	last_search = addon.load_data('search')
	if not last_search: last_search = ''
	keyboard = xbmc.Keyboard()
        keyboard.setHeading('Search TV Shows')
	keyboard.setDefault(last_search)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
                query = keyboard.getText()
                addon.save_data('search',query)
                Search(section, query)
	else:
                return

def Search(section, query):
        url = BASE_URL + '/?s='  + query
        print url
        GetTitles(section, url, startPage= '1', numOfPages= '1')

if mode == 'main': 
	MainMenu()
elif mode == 'BrowseGenre':
	BrowseGenre(content)
elif mode == 'GetTitles': 
	GetTitles(section, url, startPage, numOfPages)
elif mode == 'GetLinks':
	GetLinks(section, url)
elif mode == 'GetSearchQuery':
	GetSearchQuery(section)
elif mode == 'Search':
	Search(query)
elif mode == 'Categories':
	Categories(section)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
elif mode == 'PlayVideo':
	PlayVideo(url, listitem)
