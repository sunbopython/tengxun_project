# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item,Field


class HouseItem(Item):
	# define the fields for your item here like:
	# name = scrapy.Field()
	Name = Field()           # 楼盘名
	ID = Field()
	ND = Field()             # 分类
	url = Field()
	# 
	total_house = Field()    # 总户数
	current_house = Field()  # 当前户数
	#
	alias = Field()          # 别名
	desc_info = Field()      # 楼盘简介+++++++++

	# 基本信息-6
	district = Field()       # 所属区县
	region = Field()         # 所属商圈
	addr = Field()           # 楼盘地址
	state = Field()          # 销售状态
	feature = Field()        # 项目特色
	developer = Field()      # 开发商

	# 销售信息-5
	openning = Field()        # 开盘时间 
	checkin = Field()         # 入住时间 
	priceinfo = Field()       # 价格详情
	discount = Field()        # 打折优惠
	sale_addr = Field()       # 售楼地址
	sale_permit = Field()     # 售楼许可证 

	# 建筑信息-11
	property_year = Field()   # 产权年限
	house_type =  Field()     # 户型
	building_area = Field()   # 建筑面积
	area = Field()            # 占地面积
	building_type = Field()   # 建筑类别
	decoration = Field()      # 装修情况
	floor_condition = Field()  # 楼层状况
	building_and_tree_design = Field() # 建筑和园林设计
	builder = Field()         # 承建商
	agent = Field()           # 代理商
	landscape_design = Field() # 景观设计


	# 物业信息-11
	property_type = Field()    # 物业类别
	Volume_ratio = Field()     # 容积率    
	green_ratio = Field()      # 绿化率
	water = Field()            # 供水
	gas = Field()              # 供气
	heater =  Field()          # 供暖
	net = Field()              # 宽带
	property_company = Field() # 物业公司
	property_consult_company = Field() # 物业顾问公司
	property_fee = Field()     # 物业费
	parking = Field()          # 停车位

	# 交通配套-2+
	traffic_info = Field()          # 交通出行介绍 +++++++
	bus = Field()			   # 公交
	subway = Field()
	# 配套信息
	complement_info = Field()  # 配套介绍++++++
	school = Field()           # 学校
	shopping = Field()         # 购物
	hospital = Field()        # 医院
	life = Field()             # 生活
	fun = Field()              # 娱乐
	food = Field()             # 餐饮

	#pass
