# coding: utf-8
"""
Author  jerryAn
Time    2016.05.04
"""

import random
import os
from queue import Queue
import logging
from datetime import datetime, timedelta
import time
from twisted.web._newclient import ResponseNeverReceived,ParseError
from twisted.internet.error import TimeoutError,ConnectionRefusedError, ConnectError,ConnectionLost,TCPTimedOutError
from scrapy.utils.response import response_status_message
from scrapy.exceptions import IgnoreRequest


class ProxyMiddleware(object):
    """ Customized Proxy Middleware

        No matter success or fail, change proxy for every request 
        

        Attributes:
            proxyfile: str, a txt file which consists of proxy
            proxyfileModificationTime: 
            agent_list: agent(proxy) list
            black_list: faild agent(proxy) list

    """
    DONT_RETRY_ERRORS = (TimeoutError,ConnectionRefusedError,TCPTimedOutError,
                        ResponseNeverReceived, ConnectError)

    proxyfile = "house/utils/validProxy.txt"
    proxyfileModificationTime = None 
    agent_list = []
    black_list = []   # store the failed agent proxies in a queue (size=300)

    def __init__(self):
        #self.readBlackfile()  # read black list file first
        self.readProxyfile()
        self.show_agent_condition()  # show initial agent condition 
        
    def readProxyfile(self):
        """get proxy from proxy file and read them to agent_list"""       
        logging.info("Starting getting fresh proxies")
        with open(self.proxyfile) as f:
            for line in f:
                agent = Agent(line.strip('\n'))
                if agent not in self.agent_list and agent not in self.black_list:
                    self.agent_list.append(agent)
        self.proxyfilelastModificationTime = os.path.getmtime(self.proxyfile) 

    def add_black_list_proxy(self,ag):
        """add black list proxy to its stack list, size=300 """
        if len(self.black_list)<300:
            self.black_list.append(ag)
        else:
            for i in range(self.black_list.__len__()-300+1):
                self.black_list.pop(0)  #delete the first proxy 
            self.black_list.append(ag)
            
    def show_agent_condition(self):
        """ show life condition of current agent
        """
        logging.info('[*******] %d Current unique proxy condition' % len(self.agent_list))
        logging.info('      Proxy              | Success  |     Total.Request      | Percentage      | label')
        for _ag in self.agent_list:
            ag_str = "{}        {}              {}                {:.2%}       {}".format(str(_ag.proxy),str(_ag.success),str(_ag.total),_ag.percentage,_ag.label)
            logging.info(ag_str)

    def update_agent_list(self):
        """ If the proxyfile has been modified, 
            1) Remove invalid proxy from agent_list, 
            2) Show current agent condition, 
            3) Add more proxy from proxyfile into this list
        """
        if os.path.getmtime(self.proxyfile) != self.proxyfilelastModificationTime:                               
            logging.info("Agent pool updating !!")
            # remove invalid proxy labeled by "invalid" 
            for ag in self.agent_list:
                if not ag.is_valid():
                    logging.info("This proxy {} (success {}) need to be eliminated, \
                                withdraw parameter percentage:{}".format(ag.proxy,ag.success,ag.percentage))
                    self.add_black_list_proxy(ag)
                    self.agent_list.remove(ag)

            # add more proxy into the pool  
            self.show_agent_condition()       # show current agent condition
            self.readProxyfile()

    def maintaining_agent(self):
        """ If available agent number of agent_list is below some level such as 100, 
            we fill up the agent list

            If available agent number of agent_list is 0, we sleep for 30s until getting fresh proxy
        """
        # in case the proxy list is too small!
        healthy_threshold = 100
        valid_agent_number_in_agentlist = len(list(filter(lambda x: x.is_valid(),self.agent_list)))
        if valid_agent_number_in_agentlist < healthy_threshold:
            self.update_agent_list()

        # in case the proxy has been used up!
        while not list(filter(lambda x: x.is_valid(),self.agent_list)):
            logging.info("Proxy list has been used up! here comes long long waiting!!!")
            time.sleep(30)   
            self.update_agent_list()

    def process_request(self, request, spider):
        """ attach agent(proxy) info to request object"""
        self.maintaining_agent()
        request.meta['agent'] = random.choice(list(filter(lambda x: x.is_valid(),self.agent_list)))
        request.meta['proxy'] = request.meta['agent'].proxy

        logging.info("Request %(request)s using proxy:%(proxy)s",
                        {'request':request, 'proxy':request.meta['proxy']})

    def _new_request_from_response(self,request):
        """ Make new request from old request"""
        new_request = request.copy() 
        new_request.dont_filter = True
        return new_request

    def process_response(self, request, response, spider):
        """ Check response.status, decide whether to change proxy
          If status is not 200, proxy should be changed because of invalidity.
          Make a same request using the new proxy.
        """
        agent = request.meta.get('agent')
        reason = response_status_message(response.status)
        if response.status == 200:
            logging.info("Good proxy:{} for processing {}".format(request.meta['proxy'],response))
            agent.stronger()
            return response
        elif response.status == 403:
            agent.set_invalid()
            logging.info("Proxy: {} meet {} ".format(agent.proxy,reason))
            return self._new_request_from_response(request)

        elif response.status in [404,500,502]:
            if str.encode("腾讯房产") in response.body:  # a byte-like object is required
                logging.info("Good proxy:{} for processing {}, even though return an undefined 404 page. Because it is an real 404 page".format(request.meta['proxy'],response))
                agent.stronger()
                return response
            else:   
                 # sometimes the proxy return a fake 404 pages,
                 # how to handle it? 
                 # switch to no proxy?
                 # give it 6 chances
                proxy_changing_times_for_this_404_or_500_page = request.meta.get('404_times',0) + 1
                if proxy_changing_times_for_this_404_or_500_page < 5:
                    logging.info("Proxy {} meet faked {} ".format(agent.proxy,reason))
                    agent.weaken()
                    request.meta['404_times'] = proxy_changing_times_for_this_404_or_500_page
                    return self._new_request_from_response(request)

        elif response.status not in [200,403, 404, 408, 500, 502, 503, 504]: #spider.website_possible_httpstatus_list:
            agent.weaken()
            # make new request
            return self._new_request_from_response(request)

        return response

    def process_exception(self, request, exception, spider):
        """Handle some connection error, make another request when these error happens
        """
        agent = request.meta.get('agent')
        if isinstance(exception,self.DONT_RETRY_ERRORS):
            agent.weaken()
            return self._new_request_from_response(request)

            
class Agent(object):
    """ Specify single proxy agent object

        Atttribute:
            proxy: 
            success: this proxy's life value (just like solder's blood value in game),\
                    it minus one if failed and plus one if successed
            percentage: proxy's percentage of successful useage, successful-times/total-using-times,default 100%
            absolute_threshold:
            percentage_threshold:
            label: valid or invalid
            last_condition: the success condition of last useage

    """
    def __init__(self,proxy,success=100,percentage=1,absolute_threshold=90,percentage_threshold=0.60):
        self.proxy = "http://" + str(proxy)  # for example: "http://45.78.34.180:8080"
        self.success = int(success) 
        self.percentage = percentage
        self.total = int(self.success/self.percentage)
        self.absolute_threshold = absolute_threshold
        self.percentage_threshold = percentage_threshold 
        self._set_label()
        self._set_last_condition()  

    def _set_label(self):
        """set label accord to other argu
        """
        if self.success < self.absolute_threshold or \
                self.percentage < self.percentage_threshold:
            self.label = "invalid" 
        else:
            self.label = 'valid'

    def _set_last_condition(self,condition=True):
        """ Set last success use condition of the agent: True or False
        """
        self.last_condition = True if condition else False

    def weaken(self):
        """ After a failed usage
        """  
        self.total = self.total + 1
        self.success = self.success - 1
        self.percentage = self.success/self.total
        self._set_last_condition(condition=False)
        self._set_label()

    def stronger(self):         
        """ After a successful usage
        """       
        self.total = self.total + 1
        self.success = self.success + 1
        self.percentage = self.success/self.total
        self._set_last_condition(condition=True)
        self._set_label()

    def set_invalid(self):
        """direct way to change validation
        """
        self.last_condition = False
        self.label = "invalid"

    def is_invalid(self):
        """bool"""
        return self.label == "invalid"

    def is_valid(self):
        """bool"""
        return self.label == "valid"

    def __eq__(self,other):
        """"""
        return self.proxy == other.proxy

class TopProxyMiddleware(ProxyMiddleware):
    """
        Make statistics for the proxies during certain period, then random choose one from the top 10(default) valid proxies to use
    """
    topindex = 8 #The best 8.

    def process_request(self, request, spider):
        """ 
			Make request random choose one in top 8 proxies
        """
        self.maintaining_agent()
        tenthLargestPencentageValue = sorted(self.agent_list,key = lambda i: i.percentage)[-self.topindex].percentage 
        request.meta['agent'] = random.choice(list(filter(lambda x: x.is_valid() and x.percentage>=tenthLargestPencentageValue,self.agent_list)))
        request.meta['proxy'] = request.meta['agent'].proxy

        logging.info("Request %(request)s using proxy:%(proxy)s",
                        {'request':request, 'proxy':request.meta['proxy']})