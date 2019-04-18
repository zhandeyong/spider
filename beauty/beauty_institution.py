# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date     : 2018/8/6
# @Author   : Deyong ZHAN

import pandas as pd
import re
import requests
import random
import time

from bs4 import BeautifulSoup
from selenium import webdriver


def get_html_text(url):
    """
    爬取网页信息（静态）
    :param url: str, 网页地址
    :return:
    """
    # 设置请求头
    headers = {
    'host':'y.soyoung.com',
    'connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return ""


def get_dynamic_html_text(url):
    """
    爬取网页信息（动态)
    :param url: str, 网页地址
    :return: str, 网页信息
    """
    try:
        opt = webdriver.FirefoxOptions()
        # fireFoxoptions.headless = True
        opt.add_argument('--headless')  # 无头浏览模式
        brower = webdriver.Firefox(firefox_options=opt)
        brower.get(url)
        return brower.page_source
        # return BeautifulSoup(brower.page_source, 'html.parser')
    finally:
        try:
            brower.close()
        except:
            pass


def get_beauty_hospital(url):
    """
    获取新氧网页上大陆地区的医美医院
    :param url: str, 医美医院网页地址
    :return: DataFrame
    """
    html = get_html_text(url)
    soup = BeautifulSoup(html, 'html.parser')
    # 获取总页面数
    num_tmp = soup.find_all('div', attrs={'class': 'page'})  #
    num = int(re.findall(r'(\w*[0-9]+)\w*', str(num_tmp))[1])
    hospitals = pd.DataFrame()
    for i in range(1, num+1):
        time.sleep(random.randint(1, 5))  # 每次爬虫随机停顿1~5秒
        url_page = url + 'page/' + str(i) + '/'
        soup_hospital = BeautifulSoup(get_html_text(url_page), 'html.parser')
        # 所需内容样式为: <div class="name"><a href="/hospital/20064/" title="北京世熙医疗美容">北京世熙医疗美容</a>……</div>
        soup_tmp = BeautifulSoup(str(soup_hospital.find_all('div', attrs={'class': 'name'})), 'lxml')  # 先获取父级标签div
        hospital = pd.DataFrame(soup_tmp.find_all('a', attrs={'href': re.compile('^/hospital')}))  # 再获取所需标签a
        if len(hospital) > 0:
            hospital['hospital'] = hospital[0].apply(lambda x: x.text)
            del hospital[0]
            hospitals = hospitals.append(hospital)
        else:
            continue
    if len(hospitals) > 0:
        hospitals.drop_duplicates(inplace=True)
        hospitals.reset_index(drop=True, inplace=True)
    return hospitals


if __name__ == '__main__':
    # 首先获取各地区的链接地址
    page = get_dynamic_html_text(url='https://y.soyoung.com/hospital/s0p0l0m0i0t0a0h0o0c2/')  # 大陆地区医美医院
    page_soup = BeautifulSoup(page, 'html.parser')
    # 所需信息的样式为<a data-index="6" data-id="1" data-unopen="true" href="/hospital/s0p0l0m0i0t0a1h0o0c2/">北京市</a>
    df_url = pd.DataFrame(page_soup.find_all('a', attrs={'data-index': '6'}))
    df_url['location'] = df_url[0].apply(lambda x: x.text)
    df_url['url'] = df_url[0].apply(lambda x: 'https://y.soyoung.com' + x.get('href'))
    df_url = df_url[df_url['location'] != '不限'][['location', 'url']].reset_index(drop=True)
    # df_url.to_excel('./datasets/大陆地区各城市医美医院链接地址.xlsx', index=False)
    # df_url = pd.read_excel('./datasets/大陆地区各城市医美医院链接地址.xlsx')

    # 爬取各地区的医美医院
    df_hospitals = pd.DataFrame()
    for j in range(len(df_url)):
        location = df_url['location'][j]
        url_loc = df_url['url'][j]
        df_hospital = get_beauty_hospital(url_loc)
        print("%s 共爬取 %d 家" % (location, len(df_hospital)))
        if len(df_hospital) > 0:
            df_hospital.insert(0, 'location', location)
            df_hospitals = df_hospitals.append(df_hospital, ignore_index=True)
    df_hospitals.to_csv('./datasets/大陆地区各城市医美医院名单.txt', index=False)
