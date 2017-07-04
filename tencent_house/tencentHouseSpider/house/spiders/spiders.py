#!/usr/bin/python3
# -*- coding: utf-8 -*-
# yield Request(url="http://db.house.qq.com/bj_"+each+"/",callback=self._parseHouse,meta={'ND':str(ND)}) 为修改城市的代码，其中bj为北京市

from scrapy.http import Request,FormRequest
from scrapy.spiders import CrawlSpider, Spider
from house.items import HouseItem
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import codecs
import math
import re


def restore_escape_character(x):
	# handle bytes streams
	return codecs.getdecoder("unicode_escape")(x)[0]


class House(Spider):
	name = 'tencent_house'
	start_urls = ['http://db.house.qq.com/index.php']

	def start_requests(self):
		# max_page = response.xpath('//div[@class="tInfo hd"]/span/em/text()').extract()
		for url in self.start_urls:
			
			# http://db.house.qq.com/index.php?mod=search&act=newsearch&city=bj&showtype=1&page_no=39&mod=search&city=bj
			showtype='2'
			sm='0'
			# print(int(max_page))
			for pageNo in range(1,math.ceil(9335/10)+1):  #-showtype_1-unit_1-all_-page_1032-ND2_
				yield FormRequest(url, method='GET',formdata={'mod':'search',
												'act':'newsearch',
												'city':'bj',
												'showtype':showtype,
												'sm':sm,
												'page_no':str(pageNo),
												}, dont_filter=True)# allow_redirects=False

			# #目前以下数字（在售、在租、售罄等）需要手动去start_urls观看并填写
			# for ND in range(1,5):
			# #for ND in range(4,5):   #locking for test
			# 	if ND==1:
			# 		showtype='1'
			# 		for pageNo in range(1,math.ceil(641/10)+1):  # 641个在售项目
			# 			yield FormRequest(url, method='GET',formdata={'mod':'search',
			# 											'act':'newsearch',
			# 											'city':'bj',
			# 											'showtype':showtype,
			# 											'unit':'1',
			# 											'all':'',
			# 											'page_no':str(pageNo),
			# 											'ND':str(ND)
			# 											}, dont_filter=True, meta={'ND':str(ND)})
			# 	elif(ND==2):
			# 		showtype='2'
			# 		for pageNo in range(1,math.ceil(186/10)+1):   # 186个在租项目
			# 			yield FormRequest(url, method='GET',formdata={'mod':'search',
			# 											'act':'newsearch',
			# 											'city':'bj',
			# 											'showtype':showtype,
			# 											'unit':'1',
			# 											'all':'',
			# 											'page_no':str(pageNo),
			# 											'ND':str(ND)
			# 											}, dont_filter=True,meta={'ND':str(ND)})
			# 	elif(ND==3):
			# 		showtype='2'
			# 		for pageNo in range(1,math.ceil(9553/10)+1):  # 9553 个售罄项目
			# 			yield FormRequest(url, method='GET',formdata={'mod':'search',
			# 											'act':'newsearch',
			# 											'city':'bj',
			# 											'showtype':showtype,
			# 											'unit':'1',
			# 											'all':'',
			# 											'page_no':str(pageNo),
			# 											'ND':str(ND)
			# 											}, dont_filter=True,meta={'ND':str(ND)})
			# 	elif(ND==4):
			# 		showtype='2'
			# 		for pageNo in range(1,math.ceil(26/10)+1):  # 26 个在租项目
			# 			yield FormRequest(url, method='GET',formdata={'mod':'search',
			# 											'act':'newsearch',
			# 											'city':'bj',
			# 											'showtype':showtype,
			# 											'unit':'1',
			# 											'all':'',
			# 											'page_no':str(pageNo),
			# 											'ND':str(ND)
			# 											}, dont_filter=True,meta={'ND':str(ND)})

	def parse(self,response):
		# resultstr is str which includes usefull house ID
		# ND = response.meta['ND']
		resultstr = restore_escape_character(response.body.decode('gb2312',errors='ignore'))
		Num_list = re.findall(r'data-hid="([0-9]+)',resultstr)
		for each in Num_list:
			yield Request(url="http://db.house.qq.com/bj_"+each+"/",callback=self._parseHouse)

	def _parseHouse(self,response):
		item = HouseItem()
		# item['ND'] = response.meta['ND']
		item = self._get_houses_numbers(item,response)
		if not re.match(r'http://m',response.url):
			return Request(url= response.url+"info.html",callback=self.parseHouse,meta={'item':item})
		elif re.match(r'http://m',response.url):
			return Request(url=response.url, callback=self.parseHouse,meta={'item':item})
	def _get_houses_numbers(self,item,response):
		# total rooms and current rooms
		soup = BeautifulSoup(response.body.decode('gb2312',errors='ignore'),"lxml")
		if soup.find('span',text=re.compile(r'总\xa0户\xa0数')):
			item['total_house'] = soup.find('span',text=re.compile(r'总\xa0户\xa0数')).parent()[1].text or response.xpath("//div[contains(@class,'p-houseinfo v-box')]/p[7]/span[2]/text()").extract()
		if soup.find('span',text=re.compile(r'当前户数')):
			item['current_house'] = soup.find('span',text=re.compile(r'当前户数')).parent()[1].text or 'NULL'
		return item

	def parseHouse(self,response):
		item = response.meta['item']
		numb = re.search(r'[0-9]+',response.url)
		item['url']= 'http://db.house.qq.com/bj_'+ numb.group() +'/info.html'
		item['Name'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'elite')]/div[1]/h2/text()").extract() or response.xpath("//div[@class='l-page']/div[@class='p-houseinfo v-box']/h2/text()").extract())
		item['alias'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'elite')]/div[1]/h2/following-sibling::node()/text()").extract()) or '无别名'
		item['desc_info'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'floorIntro')]/div[2]/div/div/i").extract() or response.xpath("//div[contains(@class,'p-dynamics v-box')]/a[2]/text()[1]").extract(),index=-1)
		item = self.parseBasics(item,response) 
		item = self.parseSaleinfo(item,response)
		item = self.parseBuilding(item,response)
		item = self.parseProperty(item,response)
		item = self.parserJtpt(item,response)
		if re.match(r'http://m',response.url):
			item = self.prasefirst(item, response)
			item = self.parseModdle(item, response)
			item = self.parseTraffic(item, response)
		return item
	
	def prasefirst(self, item, response):
		"""匹配手机端基本信息"""
		item['priceinfo'] = self._ifNotEmptyGetIndex(response.xpath("//div/p[@class='price']/span/text()").extract() or response.xpath("//div/p[@class='price']/text()").extract())
		item['openning'] = self._ifNotEmptyGetIndex(response.xpath("//div/p[@class='status']/span[1]/text()").extract())
		item['state'] = self._ifNotEmptyGetIndex(response.xpath("//div/p[@class='status']/span[2]/text()").extract())
		item['addr'] = self._ifNotEmptyGetIndex(response.xpath("//div/a[@class='addr']/span/text()").extract())
		return item

	def parseBasics(self,item,response):
		"""basics info"""
		for index, details in enumerate(response.xpath("//div[contains(@class,'basics')]/div[2]/ul/li")):
			titleDetails = details.xpath('span/text()').extract()
			if(titleDetails):
				item = self.mapBasicsDetails(response,self._ifNotEmptyGetIndex(titleDetails),item,index)
		return item

	def parseSaleinfo(self,item,response):
		"""sales info"""
		for index, details in enumerate(response.xpath("//div[contains(@class,'saleIntro')]/div[2]/ul/li")):
			titleDetails = details.xpath('span/text()').extract()
			if(titleDetails):
				item = self.mapSalesDetails(response,self._ifNotEmptyGetIndex(titleDetails),item,index)
		return item 

	def parseBuilding(self,item,response):
		"""building info"""
		for index, details in enumerate(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li")):
			titleDetails = details.xpath('span/text()').extract()
			if(titleDetails):
				item = self.mapBuildingDetails(response,self._ifNotEmptyGetIndex(titleDetails),item,index)
		return item

	def parseProperty(self,item,response):
		"""property info"""
		for index, details in enumerate(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li")):
			titleDetails = details.xpath('span/text()').extract()
			if(titleDetails):
				item = self.mapPropertyDetails(response,self._ifNotEmptyGetIndex(titleDetails),item,index)
		return item

	def parserJtpt(self,item,response):
		"""jiao tong pei tao"""
		item["traffic_info"] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][1]/div/div").extract(),index=-1)
		item["complement_info"] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/div").extract(),index=-1)
		# first part
		for index, details in enumerate(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][1]/div/ul/li")):
			titleDetails = details.xpath('span/text()').extract()
			if(titleDetails):
				item = self.mapJtptDetails1(response,self._ifNotEmptyGetIndex(titleDetails),item,index)
		# second part
		for index2, details2 in enumerate(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/ul/li")):
			titleDetails2 = details2.xpath('span/text()').extract()
			if(titleDetails2):
				item = self.mapJtptDetails2(response,self._ifNotEmptyGetIndex(titleDetails2),item,index2)

		return item
	def parseModdle(self, item, response):
		for index, details in enumerate(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr']")):
			titleDetails = details.xpath('span[1]/text()').extract()
			if(titleDetails):
				item = self.mapModdleDetails(response,self._ifNotEmptyGetIndex(titleDetails),item,index)
		return item

	def parseTraffic(self, item, response):

		numb = re.search(r'[0-9]+',response.url)
		new_url = 'http://m.db.house.qq.com/' + 'arround' + '/bj_' + numb.group() + '/'
		print(new_url)
		return Request(new_url, callback=self._parseTraffic, meta={'item':item})

	def _parseTraffic(self, response):
		item = response.meta['item']
		for index, details in enumerate(response.xpath("//div[@class='wrap']/section/article")):
			titleDetails = details.xpath("label/text()").extract()
			if(titleDetails):
				item = self.mapTrafficDetails(response, self._ifNotEmptyGetIndex(titleDetails), item, index)
		return item

	def mapTrafficDetails(self, response, titleDetails, item, index):
		"""匹配手机端页面交通生活"""
		index += 1
		if (titleDetails):
			if ('公交：' in titleDetails):
				item['bus'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
			elif ('地铁：' in titleDetails):
				item['subway'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
			elif ('学校：' in titleDetails):
				item['school'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
			elif ('购物：' in titleDetails):
				item['shopping'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
			elif ('医院：' in titleDetails):	
				item['hospital'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
			elif ('生活：' in titleDetails):
				item['life'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
			elif ('娱乐：' in titleDetails):
				item['fun'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
			elif ('餐饮' in titleDetails):
				item['food'] = self._ifNotEmptyGetIndex(response.xpath("//div[@class='wrap']/section/article["+ str(index) +"]/span/text()").extract())
		return item
	def mapModdleDetails(self, response, titleDetails, item, index):
		"""匹配手机端页面的详情"""
		index += 1
		if (titleDetails):
			if ("开盘时间" in titleDetails):
				item['openning'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("入住时间" in titleDetails):
				item['checkin'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("物业类别" in titleDetails):
				item['property_type'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("产权年限" in titleDetails):
				item['property_year'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("装修状况" in titleDetails):
				item['decoration'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("建筑类别" in titleDetails):
				item['building_type'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("建筑面积" in titleDetails):
				item['building_area'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("占地面积" in titleDetails):
				item['area'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("绿化率" in titleDetails):
				item['green_ratio'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("容积率" in titleDetails):
				item['Volume_ratio'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("开发商" in titleDetails):
				item['developer'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())
			elif ("物业公司" in titleDetails):
				item['property_consult_company'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'l-page')]/div[contains(@class,'p-houseinfo v-box')]/p[@class='intr'][" + str(index) + "]/span[2]").extract())

		return item 

	def mapBasicsDetails(self,response,titleDetails,item,index):
		"""匹配基本信息"""
		index +=1
		if(titleDetails):
			if ("所属区县" in titleDetails):
				item['district']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'basics')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("所属商圈" in titleDetails):
				item['region']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'basics')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("楼盘地址" in titleDetails):
				item['addr'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'basics')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("销售状态" in titleDetails):
				item['state'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'basics')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("项目特色" in titleDetails):
				item['feature']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'basics')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("开发商" in titleDetails):
				item['developer']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'basics')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
		return item

	def mapSalesDetails(self,response,titleDetails,item,index):
		"""匹配销售信息"""
		index +=1
		if(titleDetails):
			if ("开盘时间" in titleDetails):
				item['openning']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'saleIntro')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("入住时间" in titleDetails):
				item['checkin']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'saleIntro')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("价格详情" in titleDetails):
				item['priceinfo'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'saleIntro')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("打折优惠" in titleDetails):
				item['discount'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'saleIntro')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("售楼地址" in titleDetails):
				item['sale_addr']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'saleIntro')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("售楼许可证" in titleDetails):
				item['sale_permit']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'saleIntro')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
		return item

	def mapBuildingDetails(self,response,titleDetails,item,index):
		"""匹配建筑信息"""
		index +=1
		if(titleDetails):
			if ("产权年限" in titleDetails):
				item['property_year']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("户型" in titleDetails):
				item['house_type']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("建筑面积" in titleDetails):
				item['building_area'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("占地面积" in titleDetails):
				item['area'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("建筑类别" in titleDetails):
				item['building_type']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("装修情况" in titleDetails):
				item['decoration']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("楼层状况" in titleDetails):
				item['floor_condition'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("建筑及园林设计" in titleDetails):
				item['building_and_tree_design'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("承建商" in titleDetails):
				item['builder']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("代理商" in titleDetails):
				item['agent'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("景观设计" in titleDetails):
				item['landscape_design']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'building')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
		return item
	

	def mapPropertyDetails(self,response,titleDetails,item,index):
		"""匹配物业信息"""
		index +=1
		if(titleDetails):
			if ("物业类别" in titleDetails):
				item['property_type']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("容积率" in titleDetails):
				item['Volume_ratio']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("绿化率" in titleDetails):
				item['green_ratio'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("供水" in titleDetails):
				item['water'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("供气" in titleDetails):
				item['gas']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("供暖" in titleDetails):
				item['heater']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("宽带" in titleDetails):
				item['net'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("物业公司" in titleDetails):
				item['property_company'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("物业顾问公司" in titleDetails):
				item['property_consult_company']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("物业费" in titleDetails):
				item['property_fee'] = self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
			elif("停车位" in titleDetails):
				item['parking']= self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'property')]/div[2]/ul/li["+str(index)+"]/p/text()").extract())
		return item

	def mapJtptDetails1(self,response,titleDetails,item,index):
		"""匹配交通配套1"""
		index +=1
		if(titleDetails):
			if ("公交" in titleDetails):
				item['bus']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][1]/div/ul/li["+str(index)+"]/p").extract())
			elif("地铁" in titleDetails):
				item['subway']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][1]/div/ul/li["+str(index)+"]/p").extract())
		return item

	def mapJtptDetails2(self,response,titleDetails,item,index):
		"""匹配交通配套2"""
		index +=1
		if(titleDetails):
			if ("学校" in titleDetails):
				item['school']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/ul/li["+str(index)+"]/p").extract())
			elif("购物" in titleDetails):
				item['shopping']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/ul/li["+str(index)+"]/p").extract())
			elif("医院" in titleDetails):
				item['hospital']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/ul/li["+str(index)+"]/p").extract())
			elif("生活" in titleDetails):
				item['life']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/ul/li["+str(index)+"]/p").extract())
			elif("娱乐" in titleDetails):
				item['fun']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/ul/li["+str(index)+"]/p").extract())
			elif("餐饮" in titleDetails):
				item['food']=self._ifNotEmptyGetIndex(response.xpath("//div[contains(@class,'jtpt')]/div[contains(@class,'bd')][2]/div/ul/li["+str(index)+"]/p").extract())
		return item

	def _ifNotEmptyGetIndex(self,somelist,index=0):
		"""check to see it's not empty"""
		if somelist: 
			return somelist[index]
		else:
			return somelist