# -*- coding: utf-8 -*-
# Module: default
# Author: Nicolás Furquez
# Created on: 13.08.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib2
from bs4 import BeautifulSoup
import os
import re
import cookielib
import traceback
import requests
try:
    import json
except:
    import simplejson as json

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

addon = xbmcaddon.Addon('plugin.video.veratv')
addon_version = addon.getAddonInfo('version')
debug = 'false'

home = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
FANART = os.path.join(home, 'fanart.jpg')
profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
vera_tv_host = u'http://tv.vera.com.uy'
vera_canal= vera_tv_host + '/canal/'
vera_json_todos_los_canales_url = u'http://tv.vera.com.uy/inicio/get_channels/featured_position_views/1000/0/1'
var_img_url = 'http://veratvimgs.cdn.antel.net.uy/dynamic/content_images/{0}/240/default.jpg'
complete_path=''

class NoRedirection(urllib2.HTTPErrorProcessor):
   def http_response(self, request, response):
       return response
   https_response = http_response


def addon_log(string):
    if debug == 'true':
        xbmc.log("[plugin.video.veratv-%s]: %s" %(addon_version, string))
        #print 'hola'

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring:
    """
    params = get_params()
    #print "ACAAAAAAAAAAAAAAAAAAAa"
    #print params
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params)
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of canales
        list_canales()

def get_params():
        param=[]
        paramstring=sys.argv[2]
        print "paramstring", paramstring
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params[1:]#.replace('?','')
            #print "cleanedparams", cleanedparams
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]
        return param

def get_canales_info():
    '''Metodo que obtiene los canales por Json'''
    r = requests.get(vera_json_todos_los_canales_url)
    return r.json()


def list_canales():
    '''Metodo que genera la lista de canales'''
    info = get_canales_info()
    lista = []
    for r in info:
        nombre_canal = r.get('name')
        id_canal = r.get('content_id')
        desc_canal = r.get('description')
        thumb = var_img_url.format(id_canal)
        url_canal = vera_canal + id_canal
        list_item = xbmcgui.ListItem(label=nombre_canal)
        list_item.setArt({'thumb': thumb,
                          'icon': '',
                          'fanart': ''})
        list_item.setInfo('video', {'title': nombre_canal, "Plot":desc_canal,})
        regexs= {u'get-url': {'expres': u'file: "(.*?)"', 'referer': vera_tv_host, 'name': u'get-url', 'page': u'$doregex[get-ifr]'}, u'get-ifr': {'referer': vera_tv_host, 'expres': u"'src', '(.*extras.*?)'", 'cookiejar': '', 'name': u'get-ifr', 'page': url_canal}}
        url_item ='{0}?action=play&url=$doregex[get-url]&mode=17&regexs={1}&iconimage={2}'.format(_url,json.dumps(regexs),urllib.quote_plus(thumb))
        list_item.setProperty('IsPlayable', 'true')
        lista.append((url_item, list_item, False))
    xbmcplugin.addDirectoryItems(_handle, lista, len(lista))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)



def get_video(url):
    r = urllib.urlopen(url).read()
    soup = BeautifulSoup(r,'html.parser')
    link =  soup.find_all("source", attrs={"type": "video/mp4"})
    #addon_log(link)
    return link[0]["src"]


def play_video(params):
    """
    Play a video by the provided path.

    :param path: str
    """
    regexs=params["regexs"]
    url=None
    name=None
    #mode=None
    #playlist=None
    iconimage=None
    #fanart=FANART
    #playlist=None
    #fav_mode=None
    regexs=None

    try:
        url=urllib.unquote_plus(params["url"]).decode('utf-8')
    except:
        pass
    try:
        name=urllib.unquote_plus(params["name"])
    except:
        pass
    try:
        iconimage=urllib.unquote_plus(params["iconimage"])
    except:
        pass
    try:
        regexs=params["regexs"]
    except:
        pass
    url,setresolved = getRegexParsed(regexs, url)
    print repr(url),setresolved,'imhere'
    if not (regexs and 'notplayable' in regexs and not url):
        if url:
            playsetresolved(url,name,iconimage,setresolved,regexs)
        else:
            xbmc.executebuiltin("XBMC.Notification(VeraTv,Failed to extract regex. - "+"this"+",4000,"+icon+")")


def getRegexParsed(regexs, url,cookieJar=None,forCookieJarOnly=False,recursiveCall=False,cachedPages={}, rawPost=False, cookie_jar_file=None):#0,1,2 = URL, regexOnly, CookieJarOnly
        if not recursiveCall:
            regexs = eval(urllib.unquote(regexs))
        #cachedPages = {}
        #print 'url',url
        doRegexs = re.compile('\$doregex\[([^\]]*)\]').findall(url)
        print 'doRegexs',doRegexs,regexs
        setresolved=True
        #import web_pdb; web_pdb.set_trace()
        for k in doRegexs:
            if k in regexs:
                #print 'processing ' ,k
                m = regexs[k]
                #print m
                cookieJarParam=False
                if  'cookiejar' in m: # so either create or reuse existing jar
                    #print 'cookiejar exists',m['cookiejar']
                    cookieJarParam=m['cookiejar']
                    if  '$doregex' in cookieJarParam:
                        cookieJar=getRegexParsed(regexs, m['cookiejar'],cookieJar,True, True,cachedPages)
                        cookieJarParam=True
                    else:
                        cookieJarParam=True
                #print 'm[cookiejar]',m['cookiejar'],cookieJar
                if cookieJarParam:
                    if cookieJar==None:
                        #print 'create cookie jar'
                        cookie_jar_file=None
                        if 'open[' in m['cookiejar']:
                            cookie_jar_file=m['cookiejar'].split('open[')[1].split(']')[0]
#                            print 'cookieJar from file name',cookie_jar_file

                        cookieJar=getCookieJar(cookie_jar_file)
#                        print 'cookieJar from file',cookieJar
                        if cookie_jar_file:
                            saveCookieJar(cookieJar,cookie_jar_file)
                        #import cookielib
                        #cookieJar = cookielib.LWPCookieJar()
                        #print 'cookieJar new',cookieJar
                    elif 'save[' in m['cookiejar']:
                        cookie_jar_file=m['cookiejar'].split('save[')[1].split(']')[0]
                        complete_path=os.path.join(profile,cookie_jar_file)
#                        print 'complete_path',complete_path
                        saveCookieJar(cookieJar,cookie_jar_file)
                if  m['page'] and '$doregex' in m['page']:
                    pg=getRegexParsed(regexs, m['page'],cookieJar,recursiveCall=True,cachedPages=cachedPages)
                    if len(pg)==0:
                        pg='http://regexfailed'
                    m['page']=pg

                if 'setcookie' in m and m['setcookie'] and '$doregex' in m['setcookie']:
                    m['setcookie']=getRegexParsed(regexs, m['setcookie'],cookieJar,recursiveCall=True,cachedPages=cachedPages)
                if 'appendcookie' in m and m['appendcookie'] and '$doregex' in m['appendcookie']:
                    m['appendcookie']=getRegexParsed(regexs, m['appendcookie'],cookieJar,recursiveCall=True,cachedPages=cachedPages)

                if  'post' in m and '$doregex' in m['post']:
                    m['post']=getRegexParsed(regexs, m['post'],cookieJar,recursiveCall=True,cachedPages=cachedPages)
#                    print 'post is now',m['post']

                if  'rawpost' in m and '$doregex' in m['rawpost']:
                    m['rawpost']=getRegexParsed(regexs, m['rawpost'],cookieJar,recursiveCall=True,cachedPages=cachedPages,rawPost=True)
                    #print 'rawpost is now',m['rawpost']
                link=''
                if m['page'] and m['page'] in cachedPages and not 'ignorecache' in m and forCookieJarOnly==False :
                    #print 'using cache page',m['page']
                    link = cachedPages[m['page']]
                else:
                    #import web_pdb; web_pdb.set_trace()
                    if m['page'] and  not m['page']=='' and  m['page'].startswith('http'):
                        #print 'Ingoring Cache',m['page']
                        page_split=m['page'].split('|')
                        pageUrl=page_split[0]
                        header_in_page=None
                        if len(page_split)>1:
                            header_in_page=page_split[1]
                        current_proxies=urllib2.ProxyHandler(urllib2.getproxies())
                        #print 'getting pageUrl',pageUrl
                        req = urllib2.Request(pageUrl)
                        if 'proxy' in m:
                            proxytouse= m['proxy']
                            if pageUrl[:5]=="https":
                                proxy = urllib2.ProxyHandler({ 'https' : proxytouse})
                                #req.set_proxy(proxytouse, 'https')
                            else:
                                proxy = urllib2.ProxyHandler({ 'http'  : proxytouse})
                                #req.set_proxy(proxytouse, 'http')
                            opener = urllib2.build_opener(proxy)
                            urllib2.install_opener(opener)
                        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
                        proxytouse=None

                        if 'referer' in m:
                            req.add_header('Referer', m['referer'])
                        if 'accept' in m:
                            req.add_header('Accept', m['accept'])
                        if 'agent' in m:
                            req.add_header('User-agent', m['agent'])
                        if 'x-req' in m:
                            req.add_header('X-Requested-With', m['x-req'])
                        if 'x-addr' in m:
                            req.add_header('x-addr', m['x-addr'])
                        if 'x-forward' in m:
                            req.add_header('X-Forwarded-For', m['x-forward'])
                        if 'setcookie' in m:
#                            print 'adding cookie',m['setcookie']
                            req.add_header('Cookie', m['setcookie'])
                        if 'appendcookie' in m:
#                            print 'appending cookie to cookiejar',m['appendcookie']
                            cookiestoApend=m['appendcookie']
                            cookiestoApend=cookiestoApend.split(';')
                            for h in cookiestoApend:
                                n,v=h.split('=')
                                w,n= n.split(':')
                                ck = cookielib.Cookie(version=0, name=n, value=v, port=None, port_specified=False, domain=w, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
                                cookieJar.set_cookie(ck)
                        if 'origin' in m:
                            req.add_header('Origin', m['origin'])
                        if header_in_page:
                            header_in_page=header_in_page.split('&')
                            for h in header_in_page:
                                if h.split('=')==2:
                                    n,v=h.split('=')
                                else:
                                    vals=h.split('=')
                                    n=vals[0]
                                    v='='.join(vals[1:])
                                #n,v=h.split('=')
                                req.add_header(n,v)

                        if not cookieJar==None:
#                            print 'cookieJarVal',cookieJar
                            cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
                            opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
                            opener = urllib2.install_opener(opener)
#                            print 'noredirect','noredirect' in m

                            if 'noredirect' in m:
                                opener = urllib2.build_opener(cookie_handler,NoRedirection, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
                                opener = urllib2.install_opener(opener)
                        elif 'noredirect' in m:
                            opener = urllib2.build_opener(NoRedirection, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
                            opener = urllib2.install_opener(opener)

                        if 'connection' in m:
#                            print '..........................connection//////.',m['connection']
                            from keepalive import HTTPHandler
                            keepalive_handler = HTTPHandler()
                            opener = urllib2.build_opener(keepalive_handler)
                            urllib2.install_opener(opener)

                        #print 'after cookie jar'
                        post=None

                        if 'post' in m:
                            postData=m['post']
                            splitpost=postData.split(',');
                            post={}
                            for p in splitpost:
                                n=p.split(':')[0];
                                v=p.split(':')[1];
                                post[n]=v
                            post = urllib.urlencode(post)

                        if 'rawpost' in m:
                            post=m['rawpost']
                        link=''
                        try:
                            if post:
                                response = urllib2.urlopen(req,post)
                            else:
                                response = urllib2.urlopen(req)
                            if response.info().get('Content-Encoding') == 'gzip':
                                from StringIO import StringIO
                                import gzip
                                buf = StringIO( response.read())
                                f = gzip.GzipFile(fileobj=buf)
                                link = f.read()
                            else:
                                link=response.read()

                            if 'proxy' in m and not current_proxies is None:
                                urllib2.install_opener(urllib2.build_opener(current_proxies))

                            link=javascriptUnEscape(link)
                            #print repr(link)
                            #print link This just print whole webpage in LOG
                            if 'includeheaders' in m:
                                #link+=str(response.headers.get('Set-Cookie'))
                                link+='$$HEADERS_START$$:'
                                for b in response.headers:
                                    link+= b+':'+response.headers.get(b)+'\n'
                                link+='$$HEADERS_END$$:'
    #                        print link
                            response.close()
                        except:
                            pass
                        cachedPages[m['page']] = link
                        #print link
                        #print 'store link for',m['page'],forCookieJarOnly

                        if forCookieJarOnly:
                            return cookieJar# do nothing
                    elif m['page'] and  not m['page'].startswith('http'):
                            link=m['page']
                if  '$doregex' in m['expres']:
                    m['expres']=getRegexParsed(regexs, m['expres'],cookieJar,recursiveCall=True,cachedPages=cachedPages)

                if not m['expres']=='':
                    #print 'doing it ',m['expres']
                    if 'listrepeat' in m:
                        listrepeat=m['listrepeat']
                        ret=re.findall(m['expres'],link)
                        return listrepeat,ret, m,regexs,cookieJar

                    val=''
                    if not link=='':
                        #print 'link',link
                        reg = re.compile(m['expres']).search(link)
                        try:
                            val=reg.group(1).strip()
                        except: traceback.print_exc()
                    elif m['page']=='' or m['page']==None:
                        val=m['expres']

                    if rawPost:
#                            print 'rawpost'
                        val=urllib.quote_plus(val)
                    if 'htmlunescape' in m:
                        #val=urllib.unquote_plus(val)
                        import HTMLParser
                        val=HTMLParser.HTMLParser().unescape(val)
                    try:
                        url = url.replace("$doregex[" + k + "]", val)
                    except: url = url.replace("$doregex[" + k + "]", val.decode("utf-8"))
                    #print 'ur',url
                    #return val
                else:
                    url = url.replace("$doregex[" + k + "]",'')

        if '$GUID$' in url:
            import uuid
            url=url.replace('$GUID$',str(uuid.uuid1()).upper())

        if recursiveCall: return url
        #print 'final url',repr(url)
        if url=="":
            return
        else:
            return url,setresolved

def javascriptUnEscape(str):
    js=re.findall('unescape\(\'(.*?)\'',str)
#    print 'js',js
    if (not js==None) and len(js)>0:
        for j in js:
            #print urllib.unquote(j)
            str=str.replace(j ,urllib.unquote(j))
    return str

def saveCookieJar(cookieJar,COOKIEFILE):
    try:
        complete_path=os.path.join(profile,COOKIEFILE)
        cookieJar.save(complete_path,ignore_discard=True)
    except: pass

def getCookieJar(COOKIEFILE):
    cookieJar=None
    if COOKIEFILE:
        try:
            complete_path=os.path.join(profile,COOKIEFILE)
            cookieJar = cookielib.LWPCookieJar()
            cookieJar.load(complete_path,ignore_discard=True)
        except:
            cookieJar=None
    if not cookieJar:
        cookieJar = cookielib.LWPCookieJar()
    return cookieJar

def playsetresolved(url,name,iconimage,setresolved=True,reg=None):
    print 'playsetresolved',url,setresolved
    if url==None:
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return
    if setresolved:
        addon_log('setresolved=true')
        setres=True
        if '$$LSDirect$$' in url:
            url=url.replace('$$LSDirect$$','')
            setres=False
        if reg and 'notplayable' in reg:
            setres=False

        liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo(type='Video', infoLabels={'Title':name})
        liz.setProperty("IsPlayable","true")
        liz.setPath(url)
        if not setres:
            xbmc.Player().play(url)
        else:
            #addon_log('NO POR ACA')
            #print int(sys.argv[1]), _handle
            xbmcplugin.setResolvedUrl(_handle, True, liz)
    else:
        addon_log('setresolved=false')
        xbmc.executebuiltin('XBMC.RunPlugin('+url+')')

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])