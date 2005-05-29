"""Yahoo Search Web Services

This module implements a set of classes and functions to work with the
Yahoo Search Web Services. All results from these services are properly
formatted XML, and this package facilitates for proper parsing of these
result sets. Some of the features include:

    * Extendandable API, with replaceable backend XML parsers, and
      I/O interface.
    * Type and value checking on search parameters, including
      automatic type conversion (when appropriate and possible)
    * Flexible return format, including DOM objects, or fully
      parsed result objects


You can either instantiate a search object directly, or use the factory
function create_search() in this module (see below). The supported classes
of searches are:
    
    VideoSearch	- Video Search
    ImageSearch	- Image Search
    WebSearch	- Web Search
    NewsSearch	- News Search
    LocalSearch	- Local Search

    RelatedSuggestion	- Web Search Related Suggestion
    SpellingSuggestion	- Web Search Spelling Suggestion

    TermExtraction - Term Extraction service
    ContextSearch  - Web Search with a context


The different sub-classes of Search supports different sets of query
parameters. They all require an application ID parameter (app_id). The
following tables describes all other allowed parameters for each of the
supported services:

                Web   Related  Spelling  Context   Term
               -----  -------  --------  -------  ------
    query       [X]     [X]       [X]      [X]      [X]
    type        [X]      .         .       [X]
    results     [X]     [X]        .       [X]
    start       [X]      .         .       [X]

    format      [X]      .         .       [X]
    adult_ok    [X]      .         .       [X]
    similar_ok  [X]      .         .       [X]
    language    [X]      .         .       [X]
    country     [X]      .         .       [X]
    context      .       .         .       [X]      [X]



                Image  Video  News   Local
                -----  -----  -----  -----
    query        [X]    [X]    [X]    [X]
    type         [X]    [X]    [X]     . 
    results      [X]    [X]    [X]    [X]
    start        [X]    [X]    [X]    [X]

    format       [X]    [X]     .      .
    adult_ok     [X]    [X]     .      .
    language      .      .      .     [X]
    country       .      .      .      .
    sort          .      .     [X]    [X]
    coloration   [X]     .      .      .

    radius        .      .      .     [X]
    street        .      .      .     [X]
    city          .      .      .     [X]
    state         .      .      .     [X]
    zip           .      .      .     [X]
    location      .      .      .     [X]
    longitude     .      .      .     [X]
    latitude      .      .      .     [X]


    
                List Folders  List URLs
                ------------  ---------
    folder           .           [X]
    yahooid         [X]          [X]
    results         [X]          [X]
    start           [X]          [X]



Each of these parameter is implemented as an attribute of each
respective class. For example, you can set parameters like:

    from yahoo.search.webservices import WebSearch

    app_id = "something"
    srch = WebSearch(app_id)
    srch.query = "Leif Hedstrom"
    srch.results = 40

or, if you are using the factory function:
    
    from yahoo.search.webservices import create_search

    app_id = "something"
    srch = create_search("Web", app_id, query="Leif Hedstrom", results=40)

or, the last alternative, a combination of the previous two:

    from yahoo.search.webservices import WebSearch

    app_id = "something"
    srch = WebSearch(app_id, query="Leif Hedstrom", results=40)

To retrieve a certain parameter value, simply access it as any normal
attribute:

    print "Searched for ", srch.query


For more information on these parameters, and their allowed values, please
see the official Yahoo Search Services documentation (XXX missing URL?)

Once the webservice object has been created, you can retrieve a parsed
object (typically a DOM object) using the get_results() method:

    dom = srch.get_results()

This DOM object contains all results, and can be used as is. For easier
use of the results, you can use the built-in results factory, which will
traverse the entire DOM object, and create a list of results objects.

    results = srch.parse_results(dom)

or, by using the implicit call to get_results():

    results = srch.parse_results()
    
The default XML parser and results factories should be adequate for most
users, so use the parse_results() when possible. However, both the XML
parser and the results parser can easily be overriden.


EXAMPLE:
    #!/usr/bin/python

    import sys
    from yahoo.search.webservices import create_search

    service = argv[1]
    query = " ".join(sys.argv[2:])
    app_id = "something"
    x = create_search(service, app_id, query=query, results=5)
    if x is None:
        x = create_search("Web", app_id, query=query, results=5)

    dom = srch.get_results()
    results = srch.parse_results(dom)

    for res in results:
        url = res.Url
        summary = res['Summary']
        print "%s -> %s" (summary, url)
"""


from yahoo.search import domparsers
from yahoo.search import debug

import urllib
import urllib2
import types
import string
import re

__version__ = "$Revision: 1.1 $"
__author__ = "Leif Hedstrom <leif@ogre.com>"
__date__ = "Thu Apr 28 21:38:39 PDT 2005"


#
# List of all supported languages
#
LANGUAGES = {'default':'english', 'ar':'arabic', 'bg':'bulgarian',
             'ca':'catalan', 'szh':'chinese-simplified',
             'tzh':'chinese-traditional', 'hr':'croatian', 'cs':'czech',
             'da':'danish', 'nl':'dutch', 'en':'english', 'et':'estonian',
             'fi':'finnish', 'fr':'french', 'de':'german', 'el':'greek',
             'he':'hebrew', 'hu':'hungarian', 'is':'icelandic',
             'id':'indonesian', 'it':'italian', 'ja':'japanese', 'ko':'korean',
             'lv':'latvian', 'lt':'lithuanian', 'no':'norwegian', 'fa':'persian',
             'pl':'polish', 'pt':'portuguese', 'ro':'romanian', 'ru':'russian',
             'sk':'slovak', 'sr':'serbian', 'sl':'slovenian', 'es':'spanish',
             'sv':'swedish', 'th':'thai', 'tr':'turkish'}

COUNTRIES = {'default':'any', 'any':'any', 'ar':'Argentina', 'au':'Australia',
             'at':'Austria', 'be':'Belgium', 'br':'Brazil', 'ca':'Canada',
             'cn':'China', 'cz':'Czechoslovakia', 'dk':'Denmark', 'fi':'Finland',
             'fr':'France', 'de':'Germany', 'it':'Italy', 'jp':'Japan',
             'kr':'Korea', 'nl':'Netherlands', 'no':'Norway', 'pl':'Poland',
             'rf':'Russian Federation', 'es':'Spain','se':'Swdeden',
             'ch':'Switzerland', 'tw':'Taiwan', 'uk':'United Kingdom',
             'us':'United States'}

CC_LICENSES = {'cc_any' : 'Any',
               'cc_commercial' : 'Commercial',
               'cc_modifiable' : 'Modifiable'}

APPID_REGEX = re.compile("^[a-zA-Z0-9 _()\[\]*+\-=,.:\\\@]{8,40}$")

#
# Exceptions and error handling
#
class Error(Exception):
    """Base class for all Yahoo Web Services exceptions."""

class ParameterError(Error):
    """A parameter is missing, or has bad value"""
    pass

class ServerError(Error):
    """The Yahoo server is unavailable."""
    pass

class ClassError(Error):
    """This can only occur if the APIs aren't installed or configured
    properly. If it happens, please contact the author."""

class SearchError(Error):
    """An exception/error occured in the search."""
    def __init__(self, err):
        # ToDo XXX: Do we need to call Error.__init() here ?
        self.msg = "unknown error"
        for line in err.readlines():
            start = line.find("<Message>")
            if start > -1:
                stop = line.find("</Message>")
                if stop > -1:
                    self.msg = line[start+9:stop]

    def __str__(self):
        return self.msg


#
# First a couple of base classes for the Search services. Most of them
# are almost identical, so good candidates to sub-class one of these.
#
class _Search(debug.Debuggable):
    """Yahoo Search WebService - base class

    This class implements the core functionality of all Yahoo Search
    Services.
    """
    NAME = "Search"
    SERVICE = "Search"
    PROTOCOL = "http"
    SERVER = "api.search.yahoo.com"
    VERSION = "V1"
    METHOD = "GET"
    _NEXT_QID = 1
    _RESULT_FACTORY = None

    def __init__(self, app_id, opener=None, xml_parser=None,
                 result_factory=None, debug=0, **args):
        """The app_id is a required argument, the Yahoo search services
        will not accept requests without a proper app_id. A valid app_id
        is a combination of 8 - 40 characters, matching the regexp
        "^[a-zA-Z0-9 _()\[\]*+\-=,.:\\\@]{8,40}$"). Please visit
        http://developer.yahoo.net/ to request an App ID for your own
        software or application.
            
        Four optional arguments can also be passed to the constructor:
        
            opener         - Opener for urllib2
            xml_parser     - Function to parse XML (default: minidom)
            result_factory - Result factory class (default: none)
            debug          - Debug level (if any)

        All other "named" arguments are passed into as a dictionary to the
        set_params() method.

        The result factory is specific to the particular web service used,
        e.g. the different Yahoo Search services will each implement their
        own factory class.

        Both of these settings can be controlled via their respective
        install method (see below).
        """
        super(_Search, self).__init__(debug)
        self._service = {'name' : self.NAME,
                         'protocol' :  self.PROTOCOL,
                         'server' : self.SERVER,
                         'version' : self.VERSION,
                         'service' : self.SERVICE}

        self._app_id = app_id
        self._valid_params = {}
        self._urllib_opener = opener
        self._xml_parser = xml_parser
        if result_factory:
            self._result_factory = result_factory
        else: 
            self._result_factory = self._RESULT_FACTORY

        if self._xml_parser is None:
            import xml.dom.minidom
            self._xml_parser = xml.dom.minidom.parse

        self._qid = self._NEXT_QID
        self._NEXT_QID += 1

        self._init_valid_params()
        self.reset()
        if args:
            self.set_params(args)

    # Implement the attribute handlers, to avoid confusion
    def __setattr__(self, name, value):
        if (hasattr(getattr(self.__class__, name, None), '__set__') or
              name[0] == '_'):
            super(_Search, self).__setattr__(name, value)
        else:
            self.set_param(name, value)

    def __getattr__(self, name):
        if (hasattr(getattr(self.__class__, name, None), '__get__') or
              name[0] == '_'):
            return super(_Search, self).__getattr__(name)
        else:
            return self.get_param(name)

    def _init_valid_params(self):
        err = "Yahoo Search Service class %s must implement a _init_valid_params()" % (
            self.svc_name)
        raise ClassError, err

    def reset(self):
        self._params = {}

    def _get_svc_name(self):
        return self._service['name']
    def _set_svc_name(self, value):
        self._service['name'] = value
    svc_name = property(_get_svc_name, _set_svc_name, None,
                        "Descriptive name of the service")

    def _get_svc_protocol(self):
        return self._service['protocol']
    def _set_svc_protocol(self, value):
        self._service['protocol'] = value
    svc_protocol = property(_get_svc_protocol, _set_svc_protocol, None,
                            "Service protocol (e.g. HTTP)")

    def _get_svc_service(self):
        return self._service['service']
    def _set_svc_service(self, value):
        self._service['service'] = value
    svc_service = property(_get_svc_service, _set_svc_service, None, "Service path")

    def _get_svc_server(self):
        return self._service['server']
    def _set_svc_server(self, value):
        self._service['server'] = value
    svc_server = property(_get_svc_server, _set_svc_server, None,
                          "Service server name or IP")

    def _get_svc_version(self):
        return self._service['version']
    def _set_svc_version(self, value):
        self._service['version'] = value
    svc_version = property(_get_svc_version, _set_svc_version, None,
                           "Service version string")

    def _get_app_id(self):
        return self._app_id
    def _set_app_id(self, app_id):
        if (isinstance(app_id, types.StringTypes) and
            (APPID_REGEX.match(app_id) is not None)):
            self._app_id = app_id
        else:
            raise ValueError, "`app_id' can only contain a-zA-Z0-9 _()\[\]*+\-=,.:\\\@"
    app_id = property(_get_app_id, _set_app_id, None,
                      "Application ID (issued by Yahoo)")
    appid = property(_get_app_id, _set_app_id, None,
                     "Application ID (issued by Yahoo)")

    # Manage service parameters
    def set_params(self, args):
        """Set one or several query parameters from a dictionary"""
        for (param, value) in args.items():
            self.set_param(param, value)

    def get_param(self, param):
        """Get the value of a query parameter, or the default value if unset"""
        if not self._valid_params.has_key(param):
            err = "`%s' is not a valid parameter for `%s'" % (param,
                                                              self._service['name'])
            raise ParameterError, err
        if self._params.has_key(param):
            return self._params[param]
        else:
            return self._valid_params[param][1]

    def set_param(self, param, value):
        """Set the value of a query parameter"""
        if not self._valid_params.has_key(param):
            err = "`%s' is not a valid parameter for `%s'" % (param,
                                                              self._service['name'])
            raise ParameterError, err
        pinfo = self._valid_params[param]
        if value is None:
            err = "`%s' can not have an undefined value" % (param)
            raise ValueError, err

        # Do explicit type conversions (if possible)
        if pinfo[2] is not None:
            try:
                if isinstance(value, (types.ListType, types.TupleType)):
                    value = map(lambda x: pinfo[2](x), value)
                    # ToDo XXX: Should we make sure each value is unique?
                else:
                    value = pinfo[2](value)
            except:
                pass
        # Check the type validity of the value
        err = False
        if isinstance(value, (types.ListType, types.TupleType)):
            for val in value:
                if not isinstance(val, pinfo[0]):
                    err = True
                    break
        elif not isinstance(value, pinfo[0]):
            err = True
        if err:
            raise TypeError, "`%s' only takes values of type %s" % (param, str(pinfo[0]))

        # Check validity of the value (if possible)
        err = False
        if callable(pinfo[3]):
            if isinstance(value, (types.ListType, types.TupleType)):
                for val in value:
                    if not pinfo[3](val):
                        err = True
                        break
            else:
                if not pinfo[3](value):
                    err = True
        elif isinstance(pinfo[3], (types.TupleType, types.ListType)):
            if isinstance(value, (types.ListType, types.TupleType)):
                for val in value:
                    if not val in pinfo[3]:
                        err = True
                        break
            elif not value in pinfo[3]:
                err = True
        if err:
            raise ValueError, "`%s' only handles values in: %s" % (param, str(pinfo[3]))

        # Update the parameter only if it's different from the default
        if value != pinfo[1]:
            self._params[param] = value
        elif self._params.has_key(param):
            self._params.pop(param)

    def get_valid_params(self):
        """Return a list of all valid parameters for this search"""
        return self._valid_params.keys()

    # Manage (install) the Opener, XML parser and result factory (parser)
    def install_opener(self, opener):
        """Install a URL opener (for use with urllib2), overriding the
        default opener. This is rarely required.
        """
        self._urllib_opener = opener
        
    def install_xml_parser(self, xml_parser):
        """Install an XML parser that will be used for all results for this
        object. The parser is expected to "read" the data from the supplied
        stream argument. To uninstall the parser (e.g. to make sure we
        return raw XML data) simply call this method with an argument of
        None.
        """
        self._xml_parser = xml_parser

    def install_result_factory(self, result_factory):
        """Install a python class (not an instance!) that should be used as a
        factory for creating result(s) objects.
        """
        self._result_factory = result_factory

    # Methods working on connection handling etc.
    def encode_params(self):
        params = self._params.copy()
        params.update({'appid' : self._app_id})
        return urllib.urlencode(params, 1)

    def get_url(self, with_params=True):
        """Return the URL for this request object"""
        
        url = "%s://%s/%s/%s/%s" % (self._service['protocol'],
                                    self._service['server'],
                                    self._service['service'],
                                    self._service['version'],
                                    self._service['name'])
        if with_params:
            return "%s?%s" % (url, self.encode_params())
        else:
            return url

    def open(self, opener=None):
        """Open a connection to the webservice server, and request the URL.
        The return value is a "stream", which can be read calling the
        read(), readline() or readlines() methods.
        """
        if opener is not None:
            urllib2.install_opener(opener)
        elif self._urllib_opener is not None:
            urllib2.install_opener(opener)

        if self.METHOD == "POST":
            url = self.get_url(with_params=False)
            data = self.encode_params()
        else:
            url = self.get_url(with_params=True)
            data = None
        self._debug_msg("Opening URL = %s", debug.DEBUG_LEVELS['HTTP'], url)
        if data:
            self._debug_msg("POSTing data = %s", debug.DEBUG_LEVELS['HTTP'], data)

        # XXX ToDo: This needs to be properly implemented?
        try:
            resp = urllib2.urlopen(url, data)
        except urllib2.HTTPError, err:
            if err.code == 503:
                raise ServerError("Internal WebService error, temporarily unavailable")
            else:
                raise SearchError(err)
            raise ServerError("WebService server unavailable")
        return resp

    def get_results(self, stream=None, xml_parser=None, close=True):
        """Read the stream (if provided) and either return the raw XML, or
        send the data to the provided XML parser for further processing.
        If no stream is provided, it will call the open() method using the
        default opener. The stream will be closed upon return from this
        method, unless the close=False is passed as an argument.
        """
        self._debug_msg("VALID_PARAMS = %s", debug.DEBUG_LEVELS['PARAMS'],
                        self._valid_params.keys())
        if stream is None:
            stream = self.open()
        if xml_parser is None:
            xml_parser = self._xml_parser
        res = xml_parser(stream)
        self._debug_msg("XML results are:\n%s", debug.DEBUG_LEVELS['RAWXML'],
                        res.toprettyxml())
        if close:
            stream.close()
        return res

    def parse_results(self, xml=None):
        """Get the result from the request, and instantiate the appropriate
        result class. This class will be populated with all the data from
        the XML object.
        """
        if self._result_factory is None:
            return None

        if xml is None:
            xml = self.get_results()
        res = self._result_factory(service=self)
        res.parse_results(xml)
        return res


    def _get_debug_level(self):
        return self._debug_level
    def _set_debug_level(self, level):
        self._debug_level = level
    debug_level = property(_get_debug_level, _set_debug_level, None,
                           "Set and modify the debug level")


#
# Basic parameters, supported by all regular search classes
#
class _BasicParams(object):
    """Yahoo Search WebService - common basic params

    Setup the basic CGI parameters that all (normal) search services
    supports. This is used by most services (classes) to provision for
    the basic parameters they all use.
    """
    def _init_valid_params(self):
        self._valid_params.update({
            "query" : (types.StringTypes, None, None, None),
            "results" : (types.IntType, 10, int, range(1, 51)),
            "start" : (types.IntType, 1, int, lambda x: x > -1 and x < 1001),
            })


#
# Common search parameters, shared by several classes, but not all.
#
class _CommonParams(_BasicParams):
    """Several search services share a few non-basic parameters, so
    this sub-class of _BasicParams saves some typing.
    """
    def _init_valid_params(self):
        super(_CommonParams, self)._init_valid_params()
        self._valid_params.update({
            "type" : (types.StringTypes, "any", string.lower,
                      ("all", "any", "phrase")),
            "format" : (types.StringTypes, "any", string.lower,
                        ("all", "any")),
            "adult_ok" : (types.IntType, None, int, (1,)),
            })


#
# My Web parameters, shared
#
class _MyWebParams(object):
    """My Web Params - common parameters

    Setup the basic CGI parameters that all My Web services supports.
    """
    def _init_valid_params(self):
        self._valid_params = {
            "yahooid" : (types.StringTypes, None, None, None),
            "results" : (types.IntType, 10, int, range(1, 51)),
            "start" : (types.IntType, 1, int, lambda x: x > -1 and x < 1001),
            }


#
# These are the interesting classes, one for each of the major
# search services
#
class VideoSearch(_CommonParams, _Search):
    """VideoSearch - perform a Yahoo Video Search

    This class implements the Video Search web service APIs. Allowed
    parameters are:
    
        query        - The query to search for
        type         - The kind of search to submit (all, any or phrase)
        results      - The number of results to return
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        format       - Specifies the kind of video file to search for
        adult_ok     - The service filters out adult content by default.
                       Enter a 1 to allow adult content

    Full documentation for this service is available at:

        http://developer.yahoo.net/video/V1/videoSearch.html
    """
    NAME = "videoSearch"
    SERVICE = "VideoSearchService"
    _RESULT_FACTORY = domparsers.VideoSearch

    def _init_valid_params(self):
        super(VideoSearch, self)._init_valid_params()
        self._valid_params.update({
            "format" : (types.StringTypes, "any", string.lower,
                        ("all", "all", "avi", "flash", "mpeg", "msmedia",
                         "quicktime", "realmedia")),
            })


class ImageSearch(_CommonParams, _Search):
    """ImageSearch - perform a Yahoo Image Search

    This class implements the Image Search web service APIs. Allowed
    parameters are:
    
        query        - The query to search for
        type         - The kind of search to submit (all, any or phrase)
        results      - The number of results to return
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        format       - Specifies the kind of image file to search for
        adult_ok     - The service filters out adult content by default.
                       Enter a 1 to allow adult content
        coloration   - The coloration type of the images (default, bw or
                       color)

    Full documentation for this service is available at:

        http://developer.yahoo.net/image/V1/imageSearch.html
    """
    NAME = "imageSearch"
    SERVICE = "ImageSearchService"
    _RESULT_FACTORY = domparsers.ImageSearch

    def _init_valid_params(self):
        super(ImageSearch, self)._init_valid_params()
        self._valid_params.update({
            "format" : (types.StringTypes, "any", string.lower,
                        ("all", "any", "bmp", "gif", "jpeg", "png")),
            "coloration" : (types.StringTypes, "default", string.lower,
                            ("default", "bw", "color", "colour"))
            })


class WebSearch(_CommonParams, _Search):
    """WebSearch - perform a Yahoo Web Search

    This class implements the Web Search web service APIs. Allowed
    parameters are:
    
        query        - The query to search for
        type         - The kind of search to submit (all, any or phrase)
        results      - The number of results to return
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        format       - Specifies the kind of web file to search for
        adult_ok     - The service filters out adult content by default.
                       Enter a 1 to allow adult content
        similar_ok   - Specifies whether to allow multiple results with
                       similar content. Enter a 1 to allow similar content
        language     - The language the results are written in
        country      - he country code for the country the website is
                       located in.
        license      - The Creative Commons license that the contents are
                       licensed under. You may submit multiple values (e.g.
                       license=cc_commercial&license=cc_modifiable).
        

    Full documentation for this service is available at:

        http://developer.yahoo.net/web/V1/webSearch.html
    """
    NAME = "webSearch"
    SERVICE = "WebSearchService"
    _RESULT_FACTORY = domparsers.WebSearch

    def _init_valid_params(self):
        super(WebSearch, self)._init_valid_params()
        self._valid_params.update({
            "similar_ok" : (types.IntType, None, int, (1,)),
            "format" : (types.StringTypes, "any", string.lower,
                        ("all", "any", "html", "pdf", "ppt", "msword",
                         "rss", "txt")),
            "language" : (types.StringTypes, "en", string.lower,
                          LANGUAGES.keys()),
            "country" : (types.StringTypes, "default", string.lower,
                         COUNTRIES.keys()),
            "license" : (types.StringTypes, [], string.lower,
                         CC_LICENSES.keys())
            })


class ContextSearch(WebSearch):
    """ContextSearch - perform a Yahoo Web Search with a context

    This class implements the Contextual Web Search service APIs, which is
    very similar to a regular web search. Allowed parameters are:
    
        query        - The query to search for
        context      - The context to extract meaning from (UTF-8 encoded)
        type         - The kind of search to submit (all, any or phrase)
        results      - The number of results to return
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        format       - Specifies the kind of web file to search for
        adult_ok     - The service filters out adult content by default.
                       Enter a 1 to allow adult content
        similar_ok   - Specifies whether to allow multiple results with
                       similar content. Enter a 1 to allow similar content
        language     - The language the results are written in
        country      - he country code for the country the website is
                       located in.
        license      - The Creative Commons license that the contents are
                       licensed under. You may submit multiple values (e.g.
                       license=cc_commercial&license=cc_modifiable).
        

    Full documentation for this service is available at:

        http://developer.yahoo.net/web/V1/contextSearch.html
    """
    NAME = "contextSearch"
    METHOD = "POST"

    def _init_valid_params(self):
        super(ContextSearch, self)._init_valid_params()
        self._valid_params.update({
            "context" : (types.StringTypes, None, None, None),
            })


class RelatedSuggestion(_Search):
    """RelatedSuggestion - perform a Yahoo Web Related Suggestions search

    This class implements the Web Search Related Suggestion web service
    APIs. The only allowed parameters are:

        query        - The query to get related searches from
        results      - The number of results to return

    Full documentation for this service is available at:

        http://developer.yahoo.net/web/V1/relatedSuggestion.html
    """
    NAME = "relatedSuggestion"
    SERVICE = "WebSearchService"
    _RESULT_FACTORY = domparsers.RelatedSuggestion

    def _init_valid_params(self):
        self._valid_params.update({
            "query" : (types.StringTypes, None, None, None),
            "results" : (types.IntType, 10, int, range(1, 51)),
            })


class SpellingSuggestion(_Search):
    """SpellingSuggestion - perform a Yahoo Web Spelling Suggestion search

    This class implements the Web Search Spelling Suggestion web service
    APIs. The only allowed parameter is:

        query        - The query to get spelling suggestions for

    Full documentation for this service is available at:

        http://developer.yahoo.net/web/V1/spellingSuggestion.html
    """
    NAME = "spellingSuggestion"
    SERVICE = "WebSearchService"
    _RESULT_FACTORY = domparsers.SpellingSuggestion

    def _init_valid_params(self):
        self._valid_params.update({
            "query" : (types.StringTypes, None, None, None),
            })


class TermExtraction(_Search):
    """TermExtraction - Extract words or phrases from a larger content

    This class implements the Web Search Spelling Suggestion web service
    APIs. The only allowed parameter is:

        query        - An optional query to help with the extraction
                       process
        context      - The context to extract terms from (UTF-8 encoded)


    The Term Extraction service provides a list of significant words or
    phrases extracted from a larger content. It is one of the technologies
    used in Y!Q. Full documentation for this service is available at:

        http://developer.yahoo.net/content/V1/termExtraction.html
    """
    NAME = "termExtraction"
    SERVICE = "ContentAnalysisService"
    METHOD = "POST"
    _RESULT_FACTORY = domparsers.TermExtraction

    def _init_valid_params(self):
        self._valid_params.update({
            "query" : (types.StringTypes, "", None, None),
            "context" : (types.StringTypes, None, None, None),
            })


class NewsSearch(_BasicParams, _Search):
    """NewsSearch - perform a Yahoo News Search

    This class implements the News Search web service APIs. Allowed
    parameters are:
    
        query        - The query to search for
        type         - The kind of search to submit (all, any or phrase)
        results      - The number of results to return
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        sort         - Sort articles by relevance ('rank') or most-recent
                       ('date'). Default is by relevance
        language     - The language the results are written in

    Full documentation for this service is available at:

        http://developer.yahoo.net/news/V1/newsSearch.html
    """
    NAME = "newsSearch"
    SERVICE = "NewsSearchService"
    _RESULT_FACTORY = domparsers.NewsSearch

    def _init_valid_params(self):
        super(NewsSearch, self)._init_valid_params()
        self._valid_params.update({
            "type" : (types.StringTypes, "any", string.lower,
                      ("all", "any", "phrase")),
            "sort" : (types.StringTypes, "rank", string.lower, ("date", "rank")),
            "language" : (types.StringTypes, "en", string.lower,
                          LANGUAGES.keys()),
            })


class LocalSearch(_BasicParams, _Search):
    """LocalSearch - perform a Yahoo Local Search

    This class implements the Local Search web service APIs. Allowed
    parameters are:
    
        query        - The query to search for
        results      - The number of results to return (1-20)
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        radius       - How far from the specified location to search for
                       the query terms
        sort         - Sorts the results by the chosen criteria
        street       - Street name. The number is optional
        city         - City name
        state        - The United States state. You can spell out the
                       full state name or you can use the two-letter
                       abbreviation
        zip          - The five-digit zip code, or the five-digit code
                       plus four-digit extension
        location     - Free form field for location (see below)
        latitude     - Latitude of the starting location (-90.0 - 90.0)
        longitude    - Longitude of the starting location (-180.0 - 180.0)


    If both latitude and longitude are specified, they will take priority
    over all other location data. If only one of latitude or longitude is
    specified, both will be ignored.
                        
    Full documentation for this service is available at:

        http://developer.yahoo.net/local/V1/localSearch.html
    """
    NAME = "localSearch"
    SERVICE = "LocalSearchService"
    SERVER = "api.local.yahoo.com"
    _RESULT_FACTORY = domparsers.LocalSearch

    def _init_valid_params(self):
        super(LocalSearch, self)._init_valid_params()
        self._valid_params.update({
            "results" : (types.IntType, 10, int, range(1, 21)),
            "sort" : (types.StringTypes, "relevance", string.lower,
                      ("relevance", "title", "distance", "rating")),
            "radius" : (types.FloatType, None, float, None),
            "street" : (types.StringTypes, None, None, None),
            "city" : (types.StringTypes, None, None, None),
            "state" : (types.StringTypes, None, None, None),
            "zip" : (types.StringTypes, None, None, None),
            "location" : (types.StringTypes, None, None, None),
            "latitude" : (types.FloatType, None, float,
                          lambda x: x > (-90) and x < 90,
                          "-90 < val < 90"),
            "longitude" : (types.FloatType, None, float,
                           lambda x: x > (-180) and x < 180,
                           "-180 < val < 180"),
            })


class ListFolders(_MyWebParams, _Search):
    """List Folders - Retrieving public folders

    This class implements the My Web service to retrieve public folders.
    Allowed parameters are:
    
        yahooid      - The Yahoo! user who owns the folder being accessed
        results      - The number of results to return
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        

    Full documentation for this service is available at:

        http://developer.yahoo.net/myweb/V1/listFolders.html
    """
    NAME = "listFolders"
    SERVICE = "MyWebService"
    _RESULT_FACTORY = domparsers.ListFolders


class ListUrls(_MyWebParams, _Search):
    """List Urls - Retrieving public URL stores

    This class implements the My Web service to retrieve URLs from a
    public folder. Allowed parameters are:
    
        folder       - The folder to retreive queries from. The folder
                       must be set to "Public" in order to be accessed.
        yahooid      - The Yahoo! user who owns the folder being accessed
        results      - The number of results to return
        start        - The starting result position to return (1-based).
                       The finishing position (start + results - 1) cannot
                       exceed 1000.
        

    Full documentation for this service is available at:

        http://developer.yahoo.net/myweb/V1/listUrls.html
    """
    NAME = "listUrls"
    SERVICE = "MyWebService"
    _RESULT_FACTORY = domparsers.ListUrls

    def _init_valid_params(self):
        super(ListUrls, self)._init_valid_params()
        self._valid_params.update({
            "folder" : (types.StringTypes, None, None, None),
            })


#
# This is a "convenience" dictionary, providing a (very) short
# description of all available Search classes. The factory function
# uses this dictionary to make a "simple" interface to instantiate
# and configure a search object in one call.
#
SERVICES = {'video' : (VideoSearch, "Video Search"),
            'image' : (ImageSearch, "Image Search"),
            'web' : (WebSearch, "Web Search"),
            'context' : (ContextSearch, "Contextual Web Search"),
            'news' : (NewsSearch, "News Search"),
            'local' : (LocalSearch, "Local Search"),
            'related' : (RelatedSuggestion, "Web Search Related Suggestion"),
            'spelling' : (SpellingSuggestion, "Web Search Spelling Suggestion"),
            'term' : (TermExtraction, "Term extraction service"),
            'listfolders' : (ListFolders, "Retrieving public MyWeb folders"),
            'listurls' : (ListUrls, "Retrieving public MyWeb URL stores"),
            }

def create_search(name, app_id, xml_parser=None, result_factory=None, debug=0, **args):
    """Create a Yahoo Web Services object, and configure it

    This is a simple "factory" function to instantiate and configure
    a Yahoo Web Services object. For example:

        app_id = "something"
        srch = create_search("Web", app_id, query="Leif Hedstrom", results=4)
        dom = srch.get_results()

    The first argument is one of the following "classes" of searches:

        Web	    - Web search
        Context     - Contextual Web search
        Video	    - Video search
        Image	    - Image search
        News	    - News search
        Local	    - Local search
        Related	    - Web search Related Suggestions
        Spelling    - Web search Spelling Suggestions
        Term        - Term extraction service
        ListFolders - Retrieving public MyWeb folders
        ListUrls    - Retrieving public MyWeb URL stores

    The second argument, app_id (or appid), is an application specific
    identifier, provided by Yahoo. The web services will not accept
    requests without a proper AppID.

    All other arguments must be valid named arguments, and the allowed
    set of parameters depends on the specific class of search being
    instantiated. See <XXX TODO: URL here?> for a comprehensive list and
    documentation of allowed parameters for all types of searches.
    """

    name = name.lower()
    if not SERVICES.has_key(name):
        return None

    obj = SERVICES[name][0](app_id, xml_parser=xml_parser,
                            result_factory=result_factory, debug=debug)
    if obj and args:
        obj.set_params(args)
    return obj



#
# The rest of this module is a PyUnit regression test suite. It's still
# work in progress, but it'll get there, eventually...
#
import unittest

#
# These are "shared" tests, across all the services
#
class __ServiceTestCase(object):
    SERVICE = None
    NUM_PARAMS = 999

    def setUp(self):
        try:
            self.srch = self.SERVICE('YahooDemo')
        except:
            self.srch = None
    
    # First some very basic tests
    def testInstantiation(self):
        """Instantiate a search object"""
        self.assertNotEqual(self.srch, None)

    def testValidParams(self):
        """Verify that the allowed parameters are correct"""
        params = self.srch.get_valid_params()
        self.assertEqual(len(params), self.NUM_PARAMS)

    def testQueryParam(self):
        """Verify that the query parameter is accepted"""
        self.srch.query = "Yahoo"
        self.assertEqual(self.srch.query, "Yahoo")

    def testUnknownParam(self):
        """Make sure an exception is raised on bad parameters"""
        self.assertRaises(ParameterError, self.srch.set_param, "FooBar", "Fum")

    # Now test a simple query, this will be overriden where appropriate
    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.query = "Yahoo"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertFalse(res.total_results_available == 0)
        self.assertTrue(res.first_result_position > 0)

    def testProperties(self):
        self.assertEqual(self.srch.appid, 'YahooDemo')
        self.assertEqual(self.srch.app_id, 'YahooDemo')


#
# Test for video search
#
class __VideoSearchTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = VideoSearch
    NUM_PARAMS = 6


#
# Test for image search
#
class __ImageSearchTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = ImageSearch
    NUM_PARAMS = 7

#
# Test for web search
#
class __WebSearchTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = WebSearch
    NUM_PARAMS = 10

    def testBadParamValues(self):
        self.assertRaises(ValueError, self.srch.set_param, "results", "100")
        self.assertRaises(ValueError, self.srch.set_param, "start", -1)
        self.assertRaises(ValueError, self.srch.set_param, "similar_ok", 3)
        self.assertRaises(ValueError, self.srch.set_param, "format", "foo")
        self.assertRaises(ValueError, self.srch.set_param, "language", "Here")
        self.assertRaises(ValueError, self.srch.set_param, "country", "there")
        self.assertRaises(ValueError, self.srch.set_param, "license", "cc_none")


#
# Test for context search
#
class __ContextSearchTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = ContextSearch
    NUM_PARAMS = 11

    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.query = "Yahoo"
        self.srch.context = "Web Search APIs developers"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertFalse(res.total_results_available == 0)
        self.assertTrue(res.first_result_position > 0)

#
# Test for related suggestion
#
class __RelatedSuggestionTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = RelatedSuggestion
    NUM_PARAMS = 2

    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.query = "yahoo"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertTrue(res.total_results_available == 10)
        self.assertTrue(res.first_result_position == 1)


#
# Test for spelling suggestion
#
class __SpellingSuggestionTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = SpellingSuggestion
    NUM_PARAMS = 1

    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.query = "yahok"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertTrue(res.total_results_available == 1)
        self.assertTrue(res.first_result_position == 1)

#
# Test for news search
#
class __NewsSearchTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = NewsSearch
    NUM_PARAMS = 6


#
# Test for local search
#
class __LocalSearchTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = LocalSearch
    NUM_PARAMS = 12

    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.query = "yahoo"
        self.srch.zip = "94019"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertFalse(res.total_results_available == 0)
        self.assertTrue(res.first_result_position > 0)

#
# Test for Term extractions
#
class __TermExtractionTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = TermExtraction
    NUM_PARAMS = 2

    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.query = "Yahoo"
        self.srch.context = "Web Search APIs developers"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertFalse(res.total_results_available == 0)
        self.assertTrue(res.first_result_position > 0)


#
# Test for MyWeb List Folders
#
class __ListFoldersTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = ListFolders
    NUM_PARAMS = 3

    # This is weird, but wth ...
    def testQueryParam(self):
        """Verify that the yahooid parameter is accepted"""
        self.srch.yahooid = "Yahoo"
        self.assertEqual(self.srch.yahooid, "Yahoo")

    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.yahooid = "janesmith306"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertFalse(res.total_results_available == 0)
        self.assertTrue(res.first_result_position > 0)


#
# Tests for MyWeb List URLs
#
class __ListUrlsTestCase(__ServiceTestCase, unittest.TestCase):
    SERVICE = ListUrls
    NUM_PARAMS = 4

    def testQueryParam(self):
        """Verify that the yahooid parameter is accepted"""
        self.srch.yahooid = "Yahoo"
        self.assertEqual(self.srch.yahooid, "Yahoo")

    def testSimpleQuery(self):
        """Test one simple query, make sure the XML is returned"""
        import xml.dom.minidom
        self.srch.yahooid = "janesmith306"
        self.srch.folder = "Shared"
        dom = self.srch.get_results()
        self.assertTrue(isinstance(dom, xml.dom.minidom.Document))
        res = self.srch.parse_results(dom)
        self.assertFalse(res.total_results_available == 0)
        self.assertTrue(res.first_result_position > 0)


#
# Finally, run all the tests
#
if __name__ == '__main__':
    unittest.main()



#
# local variables:
# mode: python
# indent-tabs-mode: nil
# py-indent-offset: 4
# end:
