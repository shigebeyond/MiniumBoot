#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from pyutilb.util import *
from lxml import etree
from requests import Response
from jsonpath import jsonpath
from MiniumBoot.driver import MiniTestDriver

# 响应包装器
class ResponseWrap(object):

    def __init__(self, driver: MiniTestDriver, res: Response = None):
        # webdriver
        self.driver = driver
        # 响应
        self.res = res

    # 获得元素值
    def _get_val_by(self, type, path):
        if type == 'css':
            path, prop = split_css_and_prop(path)
            if self.res != None:
                html = etree.fromstring(self.res.text, etree.HTMLParser())
                ele = html.cssselect(path)[0]
            else:
                ele = self.driver.find_element_by('css', path)
            return self.get_prop_or_text(ele, prop)

        if type == 'xpath':
            path, prop = split_xpath_and_prop(path)
            if self.res != None:
                html = etree.fromstring(self.res.text, etree.HTMLParser())
                ele = html.xpath(path)[0]
            else:
                ele = self.driver.find_element_by('xpath', path)
            return self.get_prop_or_text(ele, prop)

        if type == 'jsonpath':
            if self.res != None:
                data = self.res.json()
                return jsonpath(data, path)[0]

            raise Exception(f"无http响应, 不支持查找类型: {type}")

        if type == 'id':
            return self.driver.find_element_by('id', path).get_value_or_text()

        raise Exception(f"不支持查找类型: {type}")

    # 获得元素的属性值或文本
    def get_prop_or_text(self, ele, prop):
        # 1 响应元素
        if isinstance(ele, etree._Element):
            if prop != '':  # 获得属性
                return ele.get(prop)
            return ele.get_value_or_text()
        # 2 页面元素
        if prop != '':  # 获得属性
            return ele.attribute(prop)
        return ele.get_value_or_text()