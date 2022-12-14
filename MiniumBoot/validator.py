#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from MiniumBoot.response_wrapper import ResponseWrap
from MiniumBoot.driver import MiniTestDriver
from requests import Response
from pyutilb import log

# 校验器
class Validator(ResponseWrap):

    def __init__(self, driver: MiniTestDriver, res: Response = None):
        super(Validator, self).__init__(driver, res)
        # 校验函数映射
        self.funcs = {
            '=': lambda val, param, ex: ex == None and val == param,
            '>': lambda val, param, ex: ex == None and float(val) > param,
            '<': lambda val, param, ex: ex == None and float(val) < param,
            '>=': lambda val, param, ex: ex == None and float(val) >= param,
            '<=': lambda val, param, ex: ex == None and float(val) <= param,
            'contains': lambda val, param, ex: ex == None and param in val,
            'startswith': lambda val, param, ex: ex == None and val.startswith(param),
            'endswith': lambda val, param, ex: ex == None and val.endswith(param),
            'regex_match': lambda val, param, ex: ex == None and re.search(param, val) != None,
            'exist': lambda val, param, ex: ex == None,
            'not_exist': lambda val, param, ex: ex != None,
        }

    # 执行校验
    def run(self, config):
        if self.res != None:
            if 'validate_by_jsonpath' in config:
                return self.run_type('jsonpath', config['validate_by_jsonpath'])

        if 'validate_by_css' in config:
            return self.run_type('css', config['validate_by_css'])

        if 'validate_by_xpath' in config:
            return self.run_type('xpath', config['validate_by_xpath'])

        if 'validate_by_id' in config:
            return self.run_type('id', config['validate_by_id'])

    # 执行单个类型的校验
    def run_type(self, type, fields):
        for path, rules in fields.items():
            # 校验单个字段
            self.run_field(type, path, rules)

    # 执行单个字段的校验
    def run_field(self, type, path, rules):
        # 获得字段值
        val = ex = None
        try:
            val = self._get_val_by(type, path)
        except Exception as e:
            ex = e
        # 逐个函数校验
        for func, param in rules.items():
            b = self.run_func(func, val, param, ex)
            if b == False:
                raise AssertionError(f"Response element [{path}] not meet validate condition: {val} {func} '{param}'")

    '''
    执行单个函数：就是调用函数
    :param func 函数名
    :param val 校验的值
    :param param 参数
    :param ex 查找元素异常
    '''
    def run_func(self, func, val, param, ex):
        if func not in self.funcs:
            raise Exception(f'Invalid validate function: {func}')
        # 调用校验函数
        log.debug(f"Call validate function: {func}={param}")
        func = self.funcs[func]
        return func(val, param, ex)