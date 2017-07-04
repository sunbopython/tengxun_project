# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


from house.dbconnect import connection,connectionServer
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import re

cur,conn = None,None

class HousePipeline(object):

	def __init__(self):
		self.setupDBCon()
		self.createTable()


	def process_item(self, item, spider):
		for key, value in item.items():
			# handle list and useless html tag
			if (isinstance(value,list)):
				if value:
					templist = []
					for obj in value:
						temp = self.stripHTML(obj)  # handle useless tag
						templist.append(temp)
						templist =[i.strip() for i in templist if i] # get rid of empty list element
					item[key]= templist
				else:
					item[key]=""
			else:
				item[key]= self.stripHTML(value)

		self.storeInDb(item)
		return item


	def setupDBCon(self):
		self.cur, self.conn = connection()
		#self.conn.set_charset('utf8')
		#self.cur.execute('SET NAMES utf8;')
		#self.cur.execute('SET CHARACTER SET utf8;')
		#self.cur.execute('SET character_set_connection=utf8;')

	def createTable(self):
		"""Create table """
		self.cur.execute("""DROP TABLE IF EXISTS `Tencent_House`""")
		self.cur.execute("""CREATE TABLE IF NOT EXISTS `Tencent_House`(Id INT NOT NULL AUTO_INCREMENT,\
						Name VARCHAR(255) default NULL COMMENT '楼盘名',\
						url VARCHAR(255)  default NULL  COMMENT 'url',\
						total_house VARCHAR(255) default NULL COMMENT '总户数',\
						current_house VARCHAR(255) default NULL COMMENT '当前户数',\
						alias VARCHAR(255) default NULL COMMENT '别名',\
						desc_info TEXT default NULL COMMENT '楼盘简介',\

						district VARCHAR(255) default NULL COMMENT '所属区县',\
						region VARCHAR(255) default NULL COMMENT '所属商圈',\
						addr VARCHAR(255) default NULL COMMENT '楼盘地址',\
						state VARCHAR(255) default NULL COMMENT '销售状态',\
						feature VARCHAR(255) default NULL COMMENT '项目特色',\
						developer VARCHAR(255) default NULL COMMENT '开发商',\

						openning VARCHAR(255) default NULL COMMENT '开盘时间',\
						checkin VARCHAR(255) default NULL COMMENT '入住时间',\
						priceinfo VARCHAR(255) default NULL COMMENT '价格详情',\
						discount VARCHAR(255) default NULL COMMENT '打折优惠',\
						sale_addr VARCHAR(255) default NULL COMMENT '售楼地址',\
						sale_permit VARCHAR(255) default NULL COMMENT '售楼许可证',\

						property_year VARCHAR(255) default NULL COMMENT '产权年限',\
						house_type VARCHAR(255) default NULL COMMENT '户型',\
						building_area VARCHAR(255) default NULL COMMENT '建筑面积',\
						area VARCHAR(255) default NULL COMMENT '占地面积',\
						building_type  VARCHAR(255) default NULL COMMENT '建筑类别',\
						decoration VARCHAR(255) default NULL COMMENT '装修情况',\
						floor_condition VARCHAR(255) default NULL COMMENT '楼层状况',\
						building_and_tree_design VARCHAR(255) default NULL COMMENT '建筑和园林设计',\
						builder VARCHAR(255) default NULL COMMENT '承建商',\
						agent VARCHAR(255) default NULL COMMENT '代理商',\
						landscape_design VARCHAR(255) default NULL COMMENT '景观设计',\

						property_type VARCHAR(255) default NULL COMMENT '物业类别',\
						Volume_ratio VARCHAR(255) default NULL COMMENT '容积率',\
						green_ratio VARCHAR(255) default NULL COMMENT '绿化率',\
						water VARCHAR(255) default NULL COMMENT '供水',\
						gas VARCHAR(255) default NULL COMMENT '供气',\
						heater VARCHAR(255) default NULL COMMENT '供暖',\
						net VARCHAR(255) default NULL COMMENT '宽带',\
						property_company VARCHAR(255) default NULL COMMENT '物业公司',\
						property_consult_company VARCHAR(255) default NULL COMMENT '物业顾问公司',\
						property_fee VARCHAR(255) default NULL COMMENT '物业费',\
						parking VARCHAR(255) default NULL COMMENT '停车位',\

						traffic_info TEXT default NULL COMMENT '交通出行介绍',\
						bus VARCHAR(255) default NULL COMMENT '公交',\
						subway VARCHAR(255)  default NULL COMMENT '公交',\
						complement_info TEXT default NULL COMMENT '配套介绍',\
						school VARCHAR(255) default NULL COMMENT '学校',\
						shopping VARCHAR(255) default NULL COMMENT '购物',\
						hospital VARCHAR(255)  default NULL COMMENT '医院',\
						life VARCHAR(255)  default NULL COMMENT '生活',\
						fun  VARCHAR(255) default NULL COMMENT '娱乐',\
						food  VARCHAR(255) default NULL COMMENT '餐饮',\
						PRIMARY KEY (id)\
						 )""")
	def storeInDb(self,item):
		self.cur.execute("""INSERT INTO `Tencent_House`(
		`Name`,\
		`url`,\
		`total_house`,\
		`current_house`,\
		`alias`,\
		`desc_info`,\

		`district`,\
		`region`,\
		`addr`,\
		`state`,\
		`feature`,\
		`developer`,\

		`openning`,\
		`checkin`,\
		`priceinfo`,\
		`discount`,\
		`sale_addr`,\
		`sale_permit`,\

		`property_year`,\
		`house_type`,\
		`building_area`,\
		`area`,\
		`building_type`,\
		`decoration`,\
		`floor_condition`,\
		`building_and_tree_design`,\
		`builder`,\
		`agent`,\
		`landscape_design`,\

		`property_type`,\
		`Volume_ratio`,\
		`green_ratio`,\
		`water`,\
		`gas`,\
		`heater`,\
		`net`,\
		`property_company`,\
		`property_consult_company`,\
		`property_fee`,\
		`parking`,\

		`traffic_info`,\
		`bus`,\
		`subway`,\
		`complement_info`,\
		`school`,\
		`shopping`,\
		`hospital`,\
		`life`,\
		`fun`,\
		`food`)
		VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
				%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
				%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
				%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
				%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",\
		(
		item.get('Name'),
		item.get('url'),
		item.get('total_house'),
		item.get('current_house'),
		item.get('alias'),
		item.get('desc_info'),

		item.get('district'),
		item.get('region'),
		item.get('addr'),
		item.get('state'),
		item.get('feature'),
		item.get('developer'),

		item.get('openning'),
		item.get('checkin'),
		item.get('priceinfo'),
		item.get('discount'),
		item.get('sale_addr'),
		item.get('sale_permit'),

		item.get('property_year'),
		item.get('house_type'),
		item.get('building_area'),
		item.get('area'),
		item.get('building_type'),
		item.get('decoration'),
		item.get('floor_condition'),
		item.get('building_and_tree_design'),
		item.get('builder'),
		item.get('agent'),
		item.get('landscape_design'),

		item.get('property_type'),
		item.get('Volume_ratio'),
		item.get('green_ratio'),
		item.get('water'),
		item.get('gas'),
		item.get('heater'),
		item.get('net'),
		item.get('property_company'),
		item.get('property_consult_company'),
		item.get('property_fee'),
		item.get('parking'),

		item.get('traffic_info'),
		item.get('bus'),
		item.get('subway'),
		item.get('complement_info'),
		item.get('school'),
		item.get('shopping'),
		item.get('hospital'),
		item.get('life'),
		item.get('fun'),
		item.get('food')  
		))

		self.conn.commit()

	def stripHTML(self,string):
		soup = BeautifulSoup(string,"lxml")
		return soup.get_text()

	def __del__(self):
		self.closeDB()

	def closeDB(self):
		self.conn.close()