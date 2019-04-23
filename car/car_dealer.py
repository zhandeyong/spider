# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date     : 2019/4/16
# @Author   : Deyong ZHAN

import pandas as pd
import random
import re
import requests
import time

from bs4 import BeautifulSoup


def get_html_text(url="http://seller.cheshi.com/beijing/"):
    # 获取网页函数
    # 可通过浏览器F12-网络-消息头查看参数设置
    headers = {
    'host':'seller.cheshi.com',  # 指明服务器域名
    'connection':'keep-alive',  # 当前事务完成后，是否关闭网络连接，keep-alive为不关闭
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    "Accept-Encoding":'gzip, deflate',
    'Accept-Language':'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    # "Content-type":"application/x-www-form-urlencoded",
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return ""


def get_brand_and_location():
    """
    爬取品牌信息及地区信息函数
    分析地址 http://seller.cheshi.com/beijing/brand_545/每个4s店页面地址由地区编号和品牌编号组成，
    为了爬取所有汽车品牌在全国各地的所有4S店，需要先获取所有汽车品牌、品牌编号以及地区编号
    :return: DataFrame, DataFrame： 汽车品牌数据集，地区信息数据集
    """
    html = get_html_text()
    soup = BeautifulSoup(html, 'html.parser')
    # F12-查看器查看内容样式
    # 汽车品牌及编码的内容样式是：<a class="city_name" href="/beijing/brand_545/" id="lefttree_brand_545">AC SCHNITZER</a>
    brand = pd.DataFrame(soup.find_all('a', attrs={'class': 'city_name', 'id': re.compile('^lefttree_brand')}))  # a标签及相应的标签属性
    brand['brand'] = brand[0].apply(lambda x: x.text)  # text部分即为所需的品牌名称
    brand['brand_id'] = brand[0].apply(lambda x: str(x['id'].split('_')[-1]))  # id部分包含所需品牌编码，通过下划线分隔提取
    del brand[0]
    brand.drop_duplicates(inplace=True)
    brand.reset_index(drop=True, inplace=True)
    # 地区名称及编码的内容样式是：<a href="/beijing/brand_1/" target="_self">北京</a>
    location = pd.DataFrame(soup.find_all('a', attrs={'href': re.compile('^/'), 'target': '_self'}))  # href部分包含所有地域的编码
    location['location'] = location[0].apply(lambda x: x.text)  # text部分为地域名称
    location['location_id'] = location[0].apply(lambda x: x['href'].split('/')[1])  # href部分包含地域编码，通过'/'分隔提取
    del location[0]
    location.drop_duplicates(inplace=True)
    location.reset_index(drop=True, inplace=True)
    return brand, location


def get_4s(brand_id, location_id):
    """
    根据汽车品牌编号和地区编号，获取相应的所有4S店经销商名称
    :param brand_id: str, 汽车品牌编号
    :param location_id: str, 地区编号
    :return: DataFrame
    """
    dealers = pd.DataFrame()
    url = 'http://seller.cheshi.com/' + location_id +'/brand_'+ str(brand_id) +'/'
    html = get_html_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    try:
        # 先确定一共有几页，内容样式为<span class="disabled">共1页</span>
        num = int(soup.find_all('span', attrs={'class': 'disabled'})[0].text[1])
        for i in range(num):  # 遍历每一页取值
            time.sleep(random.randint(1, 3))
            url_brand = 'http://seller.cheshi.com/' + location_id +'/brand_'+ str(brand_id) +'/p_' + str(i+1) + '/'
            html_brand = get_html_text(url_brand)
            soup_brand = BeautifulSoup(html_brand, 'html.parser')
            # 4s店名称内容样式：<h5><a href="http://seller.cheshi.com/539750/" target="_blank">北京全福源汽车投资管理有限公司</a><h5>
            dealer = pd.DataFrame(soup_brand.find_all('h5'))
            if len(dealer) > 0:
                dealer['dealer'] = dealer[0].apply(lambda x: x.text)  # text部分为所需的4s店名称
                dealer['url'] = url_brand  # 保留相应的url，便于检查
                del dealer[0]
                dealers = dealers.append(dealer)
        if len(dealers) > 0:
            dealers.drop_duplicates(inplace=True)
            dealers.reset_index(drop=True, inplace=True)
        return dealers
    except:
        return pd.DataFrame()


if __name__ == '__main__':
    df_brand, df_location = get_brand_and_location()
    df_brand[df_brand['brand'].duplicated(keep=False)].sort_values('brand')  # 检查品牌名称是否有相同
    df_dealers = pd.DataFrame()
    # '奇瑞捷豹路虎', '长城', '郑州日产'品牌名称相同但品牌编码不同
    # '长城': 140长城， 596WEY
    # '郑州日产': 530东风， 249日产
    # '奇瑞捷豹路虎'：585捷豹， 556路虎
    # 循环爬取所有4s店，第一层遍历各品牌，第二次遍历各省份
    for i in range(len(df_brand)):
        bran = df_brand.loc[i]['brand']
        bran_id = df_brand.loc[i]['brand_id']
        print('==========%d %s ==========' % (i, bran))
        for j in range(31):  # 0-30行为所需的省份信息
            time.sleep(random.randint(1, 3))
            loc = df_location.loc[j]['location']
            loc_id = df_location.loc[j]['location_id']
            df_dealer = get_4s(bran_id, loc_id)
            print('\t%s %s 共爬取 %d 家' % (bran, loc, len(df_dealer)))
            if len(df_dealer) > 0:
                df_dealer.insert(0, 'brand', bran)
                df_dealer.insert(1, 'province', loc)
                df_dealers = df_dealers.append(df_dealer, ignore_index=True)
    print(df_dealers.shape)
    print(df_dealers.head())
    # 部门4s店名称中含有. 1 2需要进一步清理
    # df_dealers['dealer'] = df_dealers['dealer'].apply(lambda x: re.split('[.12]', x)[0])
    # df_dealers.drop_duplicates(subset=['brand', 'province', 'dealer'], inplace=True)
    df_dealers.to_csv('./全国各省份汽车品牌4s店经销商名单.txt', index=False)


