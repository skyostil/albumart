"""DOM parsers for Yahoo Search Web Services

This module implements a set of DOM based parsers for the Yahoo Search
Web Services. It's tightly coupled with the yahoo.search.webservices.
"""

from yahoo.search import debug

__version__ = "$Revision: 1.1 $"
__author__ = "Leif Hedstrom <leif@ogre.com>"
__date__ = "Thu Apr 28 21:31:33 PDT 2005"


#
# Exceptions and error handling
#
class Error(Exception):
    """Base class for all Yahoo DOM Parser exceptions."""

class ClassError(Error):
    """This can only occur if the APIs aren't installed or configured
    properly. If it happens, please contact the author."""

class XMLError(Error):
    """This exception can occur if, and only if, Yahoo returns malformed
    XML results."""


#
# Data conversion utilities
#
def string_to_bool(string):
    """Convert a string to a boolean value"""
    string = string.lower()
    if string == "false":
        return False
    elif string == "true":
        return True
    else:
        return bool(string)


#
# Simple wrapper around a dict, to present the dict keys
# as "properties"
#
class _ResultDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError, "Result object has no attribute '%s'" % key


#
# Yahoo Search Web Services result classes/parsers (DOM)
#
class SearchParser(object):
    """Yahoo Search Web Service Results - base class

    This is the base class for all Yahoo Search Web Service result parsers.
    If you build your own result parser (e.g. non-DOM based), please sub-
    class SearchParser.  The following attributes are always available:

        total_results_available
        total_results_returned
        first_result_position

        results


    Results are a list of dictionaries, which can be a custom class as
    required. An interator generator is provided for easy access to the
    list of results. For example, to iterate over all results, you would do
    something like:

        dom = ws.get_results()
        results = ws.parse_results(dom)
        dom.unlink()

        for res in results:
            print res['Url']
            print res.Summary


    As you can see, each result is a customizable dictionary. The default
    results dict supports accessing each key as a "property", like the
    above example (res.Summary).

    You can also get the list of results directly, using the results
    attribute. An optional res_dict argument can be used to provide an
    alternative dictionary implementation to use for the results.

    """
    def __init__(self, service, res_dict=_ResultDict):
        self._service = service

        self._total_results_available = 0
        self._total_results_returned = 0
        self._first_result_position = 0

        self._results = []
        self._res_dict=res_dict
        self._init_res_fields()

    def __iter__(self):
        return iter(self._results)

    def _init_res_fields(self):
        self.res_fields = [('Title', None, None),
                           ('Summary', None, None),
                           ('Url', None, None),
                           ('ClickUrl', None, None)]

    def _get_results(self):
        return self._results
    results = property(_get_results, None, None,
                       "The list of all results")

    def _get_service(self):
        return self._service
    def _set_service(self, service):
        self._service = service
    service = property(_get_service, _set_service, None,
                       "The Search Web Service object for this results parser")

    def parse_results(self, result_set):
        err = "Yahoo Search Result class %s must implement a parse_result()" % (
            self._service.svc_name)
        raise ClassError(err)

    def _get_total_results_available(self):
        return self._total_results_available
    total_results_available = property(_get_total_results_available, None, None,
                                       "The total number of results for the query")
    totalResultsAvailable = property(_get_total_results_available, None, None,
                                     "The total number of results for the query")

    def _get_total_results_returned(self):
        return self._total_results_returned
    total_results_returned = property(_get_total_results_returned, None, None,
                                      "The total number of results for the query")
    totalResultsReturned = property(_get_total_results_returned, None, None,
                                    "The number of results returned")

    def _get_first_result_position(self):
        return self._first_result_position
    first_result_position = property(_get_first_result_position, None, None,
                                     "The first result position")
    firstResultPosition = property(_get_first_result_position, None, None,
                                   "The first result position")


#
# DOM parser implementation of the search parser.
#
class SearchDOMParser(SearchParser):
    """SearchDomParser - Base class for Yahoo Search DOM result parsers

    This is a DOM specific parser that is used as a base class for all
    Yahoo Search result parsers. It obviously must implement the main entry
    entry point, parse_results().
    """
    def parse_results(self, dom):
        """This is a simple DOM parser for all Yahoo Search services. It
        expects to find a top-level node named ResultSet. This is the main
        entry point for the DOM parser, and it requires a properly con-
        structed DOM object (e.g. using minidom).
        """
        self.dom = dom
        try:
            result_set = dom.getElementsByTagName('ResultSet')[0]
        except:
            raise XMLError("DOM object has no ResultSet")
        self._parse_result_set(result_set)


    def _get_text(self, nodelist):
        """Find all text nodes for the nodelist, and concatenate them
        into one resulting strings. This is a helper method for the
        DOM parser.
        """
        rc = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc

    def _tags_to_dict(self, node, tags):
        """Internal method to parse and extract a list of tags from a
        particular node. We return a dict, which can potentially be empty.
        """
        res = self._res_dict()
        for tag in tags:
            n = node.getElementsByTagName(tag[0])
            if n:
                if tag[2]:
                    val = tag[2](self._get_text(n[0].childNodes))
                else:
                    val = self._get_text(n[0].childNodes)
            elif tag[1] is not None:
                val = tag[1]
            else:
                raise XMLError("Result is missing a %s node" % tag[0])
            res[tag[0]] = val
        return res

    def _parse_result_set(self, result_set):
        """Internal method to parse a ResultSet node"""
        
        attributes = result_set.attributes
        if not attributes:
            raise XMLError("ResultSet has no attributes")

        attr = attributes.getNamedItem('totalResultsAvailable')
        if attr:
            self._total_results_available = int(attr.nodeValue)
        else:
            raise XMLError("ResultSet has no totalResultsAvailable attribute")
        attr = attributes.getNamedItem('totalResultsReturned')
        if attr:
            self._total_results_returned = int(attr.nodeValue)
        else:
            raise XMLError("ResultSet has no totalResultsReturned attribute")
        attr = attributes.getNamedItem('firstResultPosition')
        if attr:
            self._first_result_position = int(attr.nodeValue)
        else:
            raise XMLError("ResultSet has no firstRestultPosition attribute")

        self._service._debug_msg("Results = %d / %d / %d",
                                 debug.DEBUG_LEVELS['PARSING'],
                                 self._total_results_available,
                                 self._total_results_returned,
                                 self._first_result_position);

        for res in result_set.getElementsByTagName('Result'):
            self._results.append(self._parse_result(res))

    def _parse_result(self, result):
        """Internal method to parse one Result node"""

        return self._tags_to_dict(result, self.res_fields)


#
# Result parsers for each of the supported Search Web Services
#
class WebSearch(SearchDOMParser):
    """WebSearch - DOM parser for Web Search

    Each result is a dictionary populated with the extracted data from the
    XML results. The following keys are always available:

        Title            - The title of the web page
        Summary          - Summary text associated with the web page
        Url              - The URL for the web page
        ClickUrl         - The URL for linking to the page

    The following attributes are optional, and might not be set:

        MimeType         - The MIME type fo the page
        ModificationDate - The date the page was last modified, Unix time
        Cache            - The URL of the cached result, and its size

    If present, the Cache value is in turn another dictionary, which will
    have the following keys:

        Url             - URL to cached data
        Size            - Size of the cached entry, in bytes


    Example:

        results = ws.parse_results(dom)
        for res in results:
            if res.has_key('Cache'):
                print "Cache URL: ", res['Cache']['Url']
    """
    def _init_res_fields(self):
        super(WebSearch, self)._init_res_fields()
        self.res_fields.extend((('ModificationDate', "", None),
                                ('MimeType', "", None)))

    def _parse_result(self, result):
        res = super(WebSearch, self)._parse_result(result)
        node = result.getElementsByTagName('Cache',)
        if node:
            res['Cache'] = self._tags_to_dict(node[0], (('Url', None, None),
                                                        ('Size', None, None)))
        else:
            res['Cache'] = None
        return res


class NewsSearch(SearchDOMParser):
    """NewsSearch - DOM parser for News Search
    
    Each result is a dictionary populated with the extracted data from the
    XML results. The following keys are always available:

        Title            - Title of the article
        Summary          - Summary of the text associated with the article
        Url              - The URL for the article
        ClickUrl         - The URL for linking to the article
        NewsSource       - The company that distributed the news article
        NewsSourceUrl    - The URL for the news source
        Language         - Language of the News article
        PubslishDate     - Publish date of the article

    The following attributes are optional, and might not be set:

        ModificationDate - Date entry was modified
        Thumbnail        - The URL of the thumbnail file

    If present, the Thumbnail value is in turn another dictionary, which will
    have these keys:

        Url             - URL of the thumbnail

        Height          - Height of the thumbnail in pixels (optional)
        Width           - Width of the thumbnail in pixels (optional)
    """
    def _init_res_fields(self):
        super(NewsSearch, self)._init_res_fields()
        self.res_fields.extend((('NewsSource', None, None),
                                ('NewsSourceUrl', None, None),
                                ('Language', None, None),
                                ('PublishDate', None, None),
                                ('ModificationDate', "", None)))

    def _parse_result(self, result):
        res = super(NewsSearch, self)._parse_result(result)
        node = result.getElementsByTagName('Thumbnail')
        if node:
            res['Thumbnail'] = self._tags_to_dict(node[0], (('Url', None, None),
                                                            ('Height', 0, int),
                                                            ('Width', 0, int)))
        else:
            res['Thumbnail'] = None
        return res


class VideoSearch(SearchDOMParser):
    """VideoSearch - DOM parser for Video Search

    Each result is a dictionary populated with the extracted data from the
    XML results. The following keys are always available:

        Title            - The title of the video file
        Summary          - Summary text associated with the video file
        Url              - The URL for the video file or stream
        ClickUrl         - The URL for linking to the video file
        RefererUrl       - The URL of the web page hosting the content
        FileSize         - The size of the file, in bytes
        FileFormat       - One of avi, flash, mpeg, msmedia, quicktime
                           or realmedia
        Duration         - The duration of the video file in seconds
        Channels         - Channels in the audio stream
        Streaming        - Whether the video file is streaming or not

    The following attributes are optional, and might not be set:

        Height           - The height of the keyframe Yahoo! extracted
                           from the video, in pixels
        Width            - The width of the keyframe Yahoo! extracted
                           from the video, in pixels
        Thumbnail        - The URL of the thumbnail file
        Publisher        - The creator of the video file
        Restrictions     - Provides any restrictions for this media
                           object. Restrictions include noframe and
                           noinline.
        Copyright        - The copyright owner

    If present, the Thumbnail value is in turn another dictionary, which will
    have these keys:

        Url             - URL of the thumbnail

        Height          - Height of the thumbnail in pixels (optional)
        Width           - Width of the thumbnail in pixels (optional)


    Example:

        results = ws.parse_results(dom)
        for res in results:
            print "%s - %s bytes" % (res.Title, res.FileSize)
    """
    def _init_res_fields(self):
        super(VideoSearch, self)._init_res_fields()
        self.res_fields.extend((('RefererUrl', None, None),
                                ('FileSize', None, int),
                                ('FileFormat', None, None),
                                ('Height', 0, int),
                                ('Width', 0, int),
                                ('Streaming', None, string_to_bool),
                                ('Duration', None, float),
                                ('Channels', "", None),
                                ('Publisher', "", None),
                                ('Restrictions', "", None),
                                ('Copyright', "", None)))

    def _parse_result(self, result):
        res = super(VideoSearch, self)._parse_result(result)
        node = result.getElementsByTagName('Thumbnail')
        if node:
            res['Thumbnail'] = self._tags_to_dict(node[0], (('Url', None, None),
                                                            ('Height', 0, int),
                                                            ('Width', 0, int)))
        else:
            res['Thumbnail'] = None
        return res


class LocalSearch(SearchDOMParser):
    """LocalSearch - DOM parser for Local Search

    This subclass of the SearchParser extends the parser with support for
    the Result Set Map Url. This adds an extra attribute

        result_set_map_url

    This attribute holds a URL pointing to a Yahoo Locals map with all the
    results shown on the map.

    Each result is a dictionary populated with the extracted data from the
    XML results. The following keys are always available:

        Title            - Name of the result
        Address          - Street address of the result
        City             - City in which the result is located
        State            - State in which the result is located
        Phone            - Phone number of the business, if known
        Distance         - The distance to the business or service
        Url              - The URL for the local file or stream
        ClickUrl         - The URL for linking to the detailed page
        MapUrl           - The URL of a map for the address

    The following attributes are optional, and might not be set:

        Rating           - End-user ratings for the business or service
        BusinessUrl      - The URL fo the business website, if known
        BusinessClickUrl - The URL for linking to the business
                           website, if known

    Example:

        results = ws.parse_results(dom)
        for res in results:
            print "%s  is %s %s away" % (res.Title, res.Distance[0], res.Distance[1])
    """
    def __init__(self, service, res_dict=_ResultDict):
        super(LocalSearch, self).__init__(service, res_dict)
        self._result_set_map_url = ""
        
    def parse_results(self, dom):
        """Specialized DOM parser for LocalSearch, to allow for the Map
        URL in the result.
        """
        super(LocalSearch, self).parse_results(dom)
        try:
            url_node = dom.getElementsByTagName('ResultSetMapUrl')
            self._result_set_map_url = self._get_text(url_node[0].childNodes)
        except:
            raise XMLError("DOM object has no ResultSetMapUrl")

    def _get_result_set_map_url(self):
        return self._result_set_map_url
    result_set_map_url = property(_get_result_set_map_url, None, None,
                                  "The Yahoo Locals map with all the results")
    ResultSetMapUrl = property(_get_result_set_map_url, None, None,
                               "The Yahoo Locals map with all the results")

    def _init_res_fields(self):
        # Local search is special, and doesn't have all the standard
        # result fields ...
        self.res_fields = ((('Title', None, None),
                            ('Address', None, None),
                            ('City', None, None),
                            ('State', None, None),
                            ('Phone', None, None),
                            ('Rating', "", None),
                            ('Url', None, None),
                            ('ClickUrl', None, None),
                            ('MapUrl', None, None),
                            ('BusinessUrl', "", None),
                            ('BusinessClickUrl', "", None)))
                                
    def _parse_result(self, result):
        res = super(LocalSearch, self)._parse_result(result)
        node = result.getElementsByTagName('Distance',)
        if node:
            unit = node[0].getAttribute('unit')
            if unit == "":
                unit = "miles"
            res['Distance'] = (self._get_text(node[0].childNodes), unit)
        else:
            raise XMLError("LocalSearch DOM object has no Distance")
        return res


class ImageSearch(SearchDOMParser):
    """ImageSearch - DOM parser for Image Search

    Each result is a dictionary populated with the extracted data from the
    XML results. The following keys are always available:

        Title            - The title of the image file
        Summary          - Summary text associated with the image file
        Url              - The URL for the image file or stream
        ClickUrl         - The URL for linking to the image file
        RefererUrl       - The URL of the web page hosting the content
        FileSize         - The size of the file, in bytes
        FileFormat       - One of bmp, gif, jpg or png
        Thumbnail        - The URL of the thumbnail file

    The following attributes are optional, and might not be set:

        Height           - The height of the image in pixels
        Width            - The width of the image in pixels
        Publisher        - The creator of the image file
        Restrictions     - Provides any restrictions for this media
                           object. Restrictions include noframe and
                           noinline.
        Copyright        - The copyright owner

    The Thumbnail is in turn another dictionary, which will have the
    following keys:

        Url             - URL of the thumbnail

        Height          - Height of the thumbnail, in pixels (optional)
        Width           - Width of the thumbnail, in pixels (optional)

    Example:

        results = ws.parse_results(dom)
        for res in results:
            print "%s - %s bytes" % (res.Title, res.FileSize)
    """
    def _init_res_fields(self):
        super(ImageSearch, self)._init_res_fields()
        self.res_fields.extend((('RefererUrl', None, None),
                                ('FileSize', None, int),
                                ('FileFormat', None, None),
                                ('Height', 0, int),
                                ('Width', 0, int),
                                ('Publisher', "", None),
                                ('Restrictions', "", None),
                                ('Copyright', "", None)))

    def _parse_result(self, result):
        res = super(ImageSearch, self)._parse_result(result)
        node = result.getElementsByTagName('Thumbnail',)
        if node:
            res['Thumbnail'] = self._tags_to_dict(node[0], (('Url', None, None),
                                                            ('Height', 0, int),
                                                            ('Width', 0, int)))
        else:
            raise XMLError("ImageSearch DOM object has no Thumbnail")
        return res


class RelatedSuggestion(SearchDOMParser):
    """RelatedSuggestion - DOM parser for Web Related Suggestions
    
    Simple related suggestions web service, returning a list of the
    candidate result strings. Note that the results from this service
    is slightly different compared to the other services, since each
    result can only be a string.
    """
    def _parse_result_set(self, result_set):
        cnt = 0
        for result in result_set.getElementsByTagName('Result'):
            cnt += 1
            self._results.append(self._get_text(result.childNodes))
        
        self._total_results_available = cnt
        self._total_results_returned = cnt
        if cnt > 0:
            self._first_result_position = 1


class SpellingSuggestion(SearchDOMParser):
    """SpellingSuggestion - DOM parser for Web Spelling Suggestions
    
    Simple spell checking web service, there can be only zero or one
    result from the query. Also note that the results from the search
    are slightly different compared to the other services, the one
    (possible) result is just simple string (not a dictionary).
    """
    def _parse_result_set(self, result_set):
        cnt = 0
        for result in result_set.getElementsByTagName('Result'):
            cnt += 1
            self._results.append(self._get_text(result.childNodes))
        
        self._total_results_available = cnt
        self._total_results_returned = cnt
        if cnt > 0:
            self._first_result_position = 1


class TermExtraction(SearchDOMParser):
    """TermExtraction - DOM parser for Term Extraction queries
    
    Return the list of words and phrases related to the context and
    the optional query string. The results from this search are slightly
    different compared to other services, it's just a simple list of
    words and phrases.

    """
    def _parse_result_set(self, result_set):
        cnt = 0
        for result in result_set.getElementsByTagName('Result'):
            cnt += 1
            self._results.append(self._get_text(result.childNodes))
        
        self._total_results_available = cnt
        self._total_results_returned = cnt
        if cnt > 0:
            self._first_result_position = 1


class ListFolders(SearchDOMParser):
    """ListFolders - DOM parser for MyWeb Public Folders

    Each result is a dictionary populated with the extracted data from the
    XML results. The following keys are always available:

        Title            - The title of the folder
        UrlCount         - The number of URLs stored in this folder


    Example:

        results = ws.parse_results(dom)
        for res in results:
            print "%s [%d]" % (res.Title, res.UrlCount)

    """
    def _init_res_fields(self):
        self.res_fields = [('Title', None, None),
                           ('UrlCount', None, int),
                           ]


class ListUrls(SearchDOMParser):
    """ListUrls - DOM parser for MyWeb Stored URLs

    Each result is a dictionary populated with the extracted data from the
    XML results. The following keys are always available:

        Title            - The title of the folder
        Summary          - Summary text associated with the web page
        Url              - The URL for the web page
        ClickUrl         - The URL for linking to the page
        Note             - Any note the Yahoo! user has chosen to annotate
                           the URL with
        StoreDate        - The date the URL was stored, in unix timestamp format


    Example:

        results = ws.parse_results(dom)
        for res in results:
            print "%s - %s" % (res.Title, res.Url)

    """
    def _init_res_fields(self):
        self.res_fields = [('Title', None, None),
                           ('Summary', None, None),
                           ('Url', None, None),
                           ('ClickUrl', None, None),
                           ('Note', None, None),
                           ('StoreDate', None, None),
                           ]



#
# local variables:
# mode: python
# indent-tabs-mode: nil
# py-indent-offset: 4
# end:
