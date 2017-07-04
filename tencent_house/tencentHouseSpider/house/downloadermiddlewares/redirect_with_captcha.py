import logging
import random
import re
import time
from six.moves.urllib.parse import urljoin
from scrapy.http import FormRequest,Request
from scrapy.downloadermiddlewares.redirect import RedirectMiddleware
from scrapy.utils.python import to_native_str
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.http import Request

logger = logging.getLogger(__name__)

class house_Redirect(RedirectMiddleware):
    """Handle redirection of requests based on response status and meta-refresh html tag"""

    def _new_request_from_response(self,request):
        """ Make new request from old request"""
        new_request = request.copy() 
        new_request.dont_filter = True
        return new_request

    def process_response(self, request, response, spider):
        #To determine whether the status code in the definition of the yuan ancestral
        #and in conjunction with the corresponding URL to record to error.txt

        if (request.meta.get('dont_redirect', False) or
                response.status in getattr(spider, 'handle_httpstatus_list', []) or
                response.status in request.meta.get('handle_httpstatus_list', []) or
                request.meta.get('handle_httpstatus_all', False)):
            return response

        allowed_status = (301, 302, 303, 307)
        if 'Location' not in response.headers or response.status not in allowed_status:
            return response

        if response.status == 302 or 301:
            location_url = response.headers['location'] 
            logging.debug("Redirecting (%(status)s) to %(redirected)s from %(request)s",
                     {'status': response.status, 'redirected': location_url, 'request': request.url},
                     extra={'spider': spider})
            error = 'status:(' + str(response.status) + ') ' + str(request.url) + ' ' + str(location_url) + ' Using--:' + str(request.meta['proxy']) + '\n'
            file_text = open('302_error.txt', 'a+')
            file_text.write(error)
            file_text.close()

        # HTTP header is ascii or latin1, redirected url will be percent-encoded utf-8
        location = to_native_str(response.headers['location'].decode('latin1'))#latin1 西欧的一种编码格式基于ascill

        redirected_url = urljoin(request.url, location)# 构造一个新的URL
        if response.status in (301, 307) or request.method == 'HEAD':# 这为什么没有状态码302
            redirected = request.replace(url=redirected_url)
            return self._redirect(redirected, request, spider, response.status)

        # redirected url has two kinds of redirected url if it related to captcha input
        # the first type of url has captcha string in it
        # the second type of url has not, and is the objective url which we care more about
        
        redirected = self._redirect_request_using_get(request, redirected_url)
        return self._redirect(redirected, request, spider, response.status)


        # if re.search('captcha',redirected_url):
        #     redirected = self._redirect_request_using_post(request,redirected_url)
        #     # 含有captcha的重定向URL
        # else:
        #     redirected = self._redirect_request_using_get(request,redirected_url)

        # return self._redirect(redirected, request, spider, response.status)


    def _redirect_request_using_get(self, request, redirect_url):
        
        redirected = Request(url=redirect_url,
                             method='GET',
                             meta=request.meta,
                             callback=request.callback,
                             headers=request.headers,
                             body='')
        request.dont_filter=True
        redirected.meta.pop('proxy_need_change',None)
        redirected.headers.pop('Content-Type', None)
        redirected.headers.pop('Content-Length', None)
        return redirected

    # def _redirect(self, redirected, request, spider, reason):
    #     ttl = request.meta.setdefault('redirect_ttl', self.max_redirect_times)#最大的重定向次数
    #     redirects = request.meta.get('redirect_times', 0) + 1

    #     if ttl and redirects <= self.max_redirect_times:
    #         redirected.meta['redirect_times'] = redirects
    #         redirected.meta['redirect_ttl'] = ttl - 1
    #         redirected.meta['redirect_urls'] = request.meta.get('redirect_urls', []) + \
    #             [request.url]
    #         # if it has only two layers of redirects, we get rid of the third or more
    #         if redirected.meta['redirect_urls'].__len__()>2:
    #             redirected.meta['redirect_urls'].clear()
    #         redirected.dont_filter = request.dont_filter
    #         redirected.priority = request.priority + self.priority_adjust
            
    #         logger.debug("Redirecting (%(reason)s) to %(redirected)s from %(request)s",
    #                      {'reason': reason, 'redirected': redirected, 'request': request},
    #                      extra={'spider': spider})
    #         return redirected
    #     else:
    #         logger.debug("Discarding %(request)s: max redirections reached",
    #                      {'request': request}, extra={'spider': spider})
    #         raise IgnoreRequest("max redirections reached")