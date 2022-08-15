#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import sys
import os
import json
import fnmatch
from pathlib import Path
import requests
from pyutilb import log, ocr_youdao
from pyutilb.util import *
import base64
from MiniumBoot.validator import Validator
from MiniumBoot.extractor import Extractor
import minium
from minium.framework import loader
from minium.framework.miniconfig import MiniConfig
from minium.framework.assertbase import AssertBase
from at.core.adbwrap import AdbWrap
from minium.native.wx_native.androidnative import WXAndroidNative
from driver import MiniTestDriver

# 扩展BaseElement方法
def get_value_or_text(self):
    r = self.value
    if r != None and r != '':
        return r
    return self.inner_text
minium.BaseElement.get_value_or_text = get_value_or_text

# 跳出循环的异常
class BreakException(Exception):
    def __init__(self, condition):
        self.condition = condition # 跳转条件

# Minium基于yaml的启动器
class Boot(object):

    def __init__(self):
        super().__init__()
        # 延迟初始化driver
        self.driver = None
        # 当前页面的校验器, 依赖于driver
        self.validator = None
        # 当前页面的提取器, 依赖于driver
        self.extractor = None
        # 加载的 TestSuite
        self.suite = None
        # 项目代码中的app.json数据
        self.appjson = None
        # 延迟初始化的app包
        self.package = None
        # 步骤文件所在的目录
        self.step_dir = None
        # 已下载过的url对应的文件，key是url，value是文件
        self.downloaded_files = {}
        # 基础url
        self._base_url = None
        # 动作映射函数
        self.actions = {
            'init_driver': self.init_driver,
            'close_driver': self.close_driver,
            'sleep': self.sleep,
            'print': self.print,
            'input_by_id': self.input_by_id,
            'input_by_css': self.input_by_css,
            'input_by_xpath': self.input_by_xpath,
            'hide_keyboard': self.hide_keyboard,
            'page_scroll': self.page_scroll,
            'scroll_by': self.scroll_by,
            'scroll_up_by': self.scroll_up_by,
            'scroll_down_by': self.scroll_down_by,
            'scroll_left_by': self.scroll_left_by,
            'scroll_right_by': self.scroll_right_by,
            'swiper_by': self.swiper_by,
            'tap': self.tap,
            'tap_by': self.tap_by,
            'click_by': self.click_by,
            'click_by_if_exist': self.click_by_if_exist,
            'allow': self.allow,
            'forbid': self.forbid,
            'handle_modal': self.handle_modal,
            'deactive': self.deactive,
            'set_orientation': self.set_orientation,
            'set_location': self.set_location,
            'screenshot': self.screenshot,
            'execute_js': self.execute_js,
            'call_wx_method': self.call_wx_method,
            'goto': self.goto,
            'switch_tab': self.switch_tab,
            'back': self.back,
            'get_clipboard': self.get_clipboard,
            'set_clipboard': self.set_clipboard,
            'push_file': self.push_file,
            'pull_file': self.pull_file,
            'pull_down_refresh': self.pull_down_refresh,
            'vibrate': self.vibrate,
            'scan_code': self.scan_code,
            'send_sms': self.send_sms,
            'print_system_info': self.print_system_info,
            'print_all_pages': self.print_all_pages,
            'print_current_page': self.print_current_page,
            'for': self.do_for,
            'once': self.once,
            'break_if': self.break_if,
            'moveon_if': self.moveon_if,
            'moveon_if_exist_by': self.moveon_if_exist_by,
            'break_if_not_exist_by': self.break_if_not_exist_by,
            'include': self.include,
            'set_vars': self.set_vars,
            'print_vars': self.print_vars,
            'base_url': self.base_url,
            'get': self.get,
            'post': self.post,
            'upload': self.upload,
            'download': self.download,
            'validate_by_jsonpath': self.validate_by_jsonpath,
            'validate_by_css': self.validate_by_css,
            'validate_by_xpath': self.validate_by_xpath,
            'validate_by_id': self.validate_by_id,
            'extract_by_jsonpath': self.extract_by_jsonpath,
            'extract_by_css': self.extract_by_css,
            'extract_by_xpath': self.extract_by_xpath,
            'extract_by_id': self.extract_by_id,
            'extract_by_eval': self.extract_by_eval,

            # 以下步骤是根据官方api封装, 但发现api无用
            'swipe': self.swipe,
            'swipe_up': self.swipe_up,
            'swipe_down': self.swipe_down,
            'swipe_left': self.swipe_left,
            'swipe_right': self.swipe_right,
            'swipe_vertical': self.swipe_vertical,
            'swipe_horizontal': self.swipe_horizontal,
            'move_by': self.move_by,
            'zoom_in': self.zoom_in,
            'zoom_out': self.zoom_out,
            'zoom_in_by': self.zoom_in_by,
            'zoom_out_by': self.zoom_out_by,
        }
        set_var('boot', self)
        # 当前文件
        self.step_file = None
        # 视频/音频文件
        self.video_ele = None

    '''
    执行入口
    :param step_files 步骤配置文件或目录的列表
    '''
    def run(self, step_files):
        for path in step_files:
            # 1 模式文件
            if '*' in path:
                dir, pattern = path.rsplit(os.sep, 1)  # 从后面分割，分割为目录+模式
                if not os.path.exists(dir):
                    raise Exception(f'步骤配置目录不存在: {dir}')
                self.run_1dir(dir, pattern)
                return

            # 2 不存在
            if not os.path.exists(path):
                raise Exception(f'步骤配置文件或目录不存在: {path}')

            # 3 目录: 遍历执行子文件
            if os.path.isdir(path):
                self.run_1dir(path)
                return

            # 4 纯文件
            self.run_1file(path)

    # 执行单个步骤目录: 遍历执行子文件
    # :param path 目录
    # :param pattern 文件名模式
    def run_1dir(self, dir, pattern ='*.yml'):
        # 遍历目录: https://blog.csdn.net/allway2/article/details/124176562
        files = os.listdir(dir)
        files.sort() # 按文件名排序
        for file in files:
            if fnmatch.fnmatch(file, pattern): # 匹配文件名模式
                file = os.path.join(dir, file)
                if os.path.isfile(file):
                    self.run_1file(file)

    # 执行单个步骤文件
    # :param step_file 步骤配置文件路径
    # :param include 是否inlude动作触发
    def run_1file(self, step_file, include = False):
        # 获得步骤文件的绝对路径
        if include: # 补上绝对路径
            if not os.path.isabs(step_file):
                step_file = self.step_dir + os.sep + step_file
        else: # 记录目录
            step_file = os.path.abspath(step_file)
            self.step_dir = os.path.dirname(step_file)

        log.debug(f"加载并执行步骤文件: {step_file}")
        # 获得步骤
        steps = read_yaml(step_file)
        if self.step_file == None and self.driver == None: # 首次执行: 初始化driver + 再运行单元测试
            self.init_and_run_test(steps)
        else: # 执行多个步骤
            self.step_file = step_file
            self.run_steps(steps)

    # 首次执行: 先初始化driver, 再运行单元测试
    def init_and_run_test(self, steps):
        if len(steps) == 0 or 'init_driver' not in steps[0]:
            raise Exception('未找到第一个动作: init_driver')
        # 1 初始化driver
        params = steps[0]['init_driver']
        self.init_driver(params)

        # 修改 MiniTestDriver.test_boot
        boot = self
        def test_boot(driver):
            boot.run_steps(steps)
        MiniTestDriver.test_boot = test_boot

        # 运行测试用例 tests 用例对象, 为 TestSuits: MiniTestDriver.test_boot
        result = minium.MiniResult()
        self.suite.run(result)

        # 输出结果
        result.print_shot_msg()
        result.dumps(AssertBase.CONFIG.outputs) # 用例运行的结果存放目录


    # 执行多个步骤
    def run_steps(self, steps):
        # 逐个步骤调用多个动作
        for step in steps:
            for action, param in step.items():
                self.run_action(action, param)

    '''
    执行单个动作：就是调用动作名对应的函数
    :param action 动作名
    :param param 参数
    '''
    def run_action(self, action, param):
        if 'for(' in action:
            n = int(action[4:-1])
            self.do_for(param, n)
            return

        if action not in self.actions:
            raise Exception(f'无效动作: [{action}]')

        # 调用动作对应的函数
        log.debug(f"处理动作: {action}={param}")
        func = self.actions[action]
        func(param)

    # --------- 动作处理的函数 --------
    # 初始化driver
    def init_driver(self, config):
        # 防止重复调用
        if self.driver != None:
            return

        '''
        # demo
        config = {
            "debug_mode": "debug",
            "enable_app_log": true,
            "project_path": "/Users/sherlock/github/miniprogram-demo",
            "dev_tool_path": "/Applications/wechatwebdevtools.app/Contents/MacOS/cli",
            "platform": "ide",
            "app": "wx",
            "close_ide": false,
            "test_port": 9421,
            "assert_capture": true,
            "use_push": true,
            "auto_relaunch": true,
            "remote_connect_timeout": 10,
            "account_info": {
                "wx_nick_name": "locker",
                "open_id": "o6zAJs_pwr**********aROZDjiw"
            },
            # android
            "device_desire": {
                "serial": "f978cc97", # Android设备号, adb devices查看
                "uiautomator": "UiAutomator2",
            }
            # ios
            "device_desire": {
                "wda_project_path": "/Users/sherlock/.npm-global/lib/node_modules/appium/node_modules/appium-webdriveragent",
                "os_type": "ios",
                "device_info": {
                    "udid": "aee531018e668ff1aad*************2924e8",
                    "model": "iPhone 6",
                    "version": "12.2.5",
                    "name": "sherlock's iPhone"
                }
            }
        }
        '''
        # app.json
        path = config['project_path'] + os.sep + 'miniprogram' + os.sep + 'app.json'
        self.appjson = read_json(path)

        # TestSuite
        self.suite = minium.framework.loader.load_from_case_name('driver', 'test_boot')
        # driver.MiniTestDriver
        self.driver = self.suite._tests[0]

        # 当前页面的校验器, 依赖于driver
        self.validator = Validator(self.driver)
        # 当前页面的提取器, 依赖于driver
        self.extractor = Extractor(self.driver)

        # 设置类属性 AssertBase.CONFIG，即用例类的属性  MiniTest.CONFIG
        AssertBase.CONFIG = MiniConfig(config)
        AssertBase.setUpConfig()

    # 关闭driver
    def close_driver(self):
        if self.driver != None:
            if self.driver.mini != None:
                self.driver.mini.shutdown()
            self.driver = None

    @property
    def native(self):
        return self.driver.native

    @property
    def adb(self) -> AdbWrap:
        n = self.driver.native
        if isinstance(n, WXAndroidNative):
            return n.at.adb

        return None

    @property
    def app(self) -> minium.App:
        return self.driver.app

    @property
    def page(self) -> minium.Page:
        return self.driver.page

    @property
    def mini(self):
        return self.driver.mini

    # for循环
    # :param steps 每个迭代中要执行的步骤
    # :param n 循环次数
    def do_for(self, steps, n = None):
        label = f"for({n})"
        if n == None:
            n = sys.maxsize # 最大int，等于无限循环次数
            label = f"for(∞)"
        log.debug(f"-- 开始循环: {label} -- ")
        try:
            for i in range(n):
                # i+1表示迭代次数比较容易理解
                log.debug(f"第{i+1}次迭代")
                set_var('for_i', i+1)
                self.run_steps(steps)
        except BreakException as e:  # 跳出循环
            log.debug(f"-- 跳出循环: {label}, 跳出条件: {e.condition} -- ")
        else:
            log.debug(f"-- 终点循环: {label} -- ")

    # 执行一次子步骤，相当于 for(1)
    def once(self, steps):
        self.do_for(steps, 1)

    # 检查并继续for循环
    def moveon_if(self, expr):
        # break_if(条件取反)
        self.break_if(f"not ({expr})")

    # 跳出for循环
    def break_if(self, expr):
        val = eval(expr, globals(), bvars)  # 丢失本地与全局变量, 如引用不了json模块
        if bool(val):
            raise BreakException(expr)

    # 检查并继续for循环
    def moveon_if_exist_by(self, config):
        self.break_if_not_exist_by(config)

    # 跳出for循环
    def break_if_not_exist_by(self, config):
        if not self.exist_by_any(config):
            raise BreakException(config)

    # 加载并执行其他步骤文件
    def include(self, step_file):
        self.run_1file(step_file, True)

    # 设置变量
    def set_vars(self, vars):
        for k, v in vars.items():
            v = replace_var(v)  # 替换变量
            set_var(k, v)

    # 打印变量
    def print_vars(self, _):
        log.info(f"打印变量: {bvars}")

    # 睡眠
    def sleep(self, seconds):
        seconds = replace_var(seconds)  # 替换变量
        time.sleep(int(seconds))

    # 打印
    def print(self, msg):
        msg = replace_var(msg)  # 替换变量
        log.info(msg)

    # 解析响应
    def _analyze_response(self, res, config):
        # 添加固定变量:响应
        set_var('response', res)
        # 校验器
        v = Validator(self.driver, res)
        v.run(config)
        # 提取器
        e = Extractor(self.driver, res)
        e.run(config)

    # 根据id来填充输入框
    # :param input_data 表单数据, key是输入框的路径, value是填入的值
    def input_by_id(self, input_data):
        return self._input_by_type_and_data('id', input_data)

    # 根据css来填充输入框
    # :param input_data 表单数据, key是输入框的路径, value是填入的值
    def input_by_css(self, input_data):
        return self._input_by_type_and_data('css', input_data)

    # 根据xpath来填充输入框
    # :param input_data 表单数据, key是输入框的路径, value是填入的值
    def input_by_xpath(self, input_data):
        return self._input_by_type_and_data('xpath', input_data)

    # 根据类型与数据来填充输入框
    # :param type 选择器的类型:id/css/xpath
    # :param input_data 表单数据, key是输入框的路径, value是填入的值
    def _input_by_type_and_data(self, type, input_data):
        for name, value in input_data.items():
            log.debug(f"替换变量： {name} = {value}")
            value = replace_var(value)  # 替换变量

            # 找到输入框
            try:
                ele = self.find_by(type, name)
            except Exception as ex:  # 找不到元素
                log.error(f"找不到输入元素{name}", exc_info = ex)
                continue

            # 输入
            if ele._tag_name == "switch":
                ele.switch(bool(value))
            elif ele._tag_name == 'slider':
                ele.slide_to(value)
            elif ele._tag_name == 'picker':
                ele.click()  # 阻止picker弹起
                ele.pick(value)  # 用trigger模拟pick完成的动作
            else:#elif ele._tag_name == 'input':
                # ele.trigger("input", {"value": value})  # 直接触发事件，但是不会影响UI变化
                ele.input(str(value)) # UI有变化

    # 隐藏键盘
    def hide_keyboard(self, _):
        self.native.hide_keyboard()

    # 根据指定类型，查找元素
    def find_by(self, type, path):
        return self.driver.find_element_by(type, path)

    # 根据任一类型，查找元素
    def find_by_any(self, config):
        types = ['id', 'css', 'xpath']
        for type in types:
            if type in config:
                path = config[type]
                if type == 'xpath': # xpath支持变量
                    path = replace_var(path)
                return self.find_by(type, path)
        raise Exception(f"没有查找类型: {config}")

    # 根据任一类型，检查元素是否存在
    def exist_by_any(self, config):
        selector = config
        return self.page.element_is_exists(selector, max_timeout=5)

    def calculate_new_scroll_pos(self, xy, wh, old_xy):
        '''
        # 计算新的滚动位置
        :param xy: x或y坐标/屏幕比例+增减
        :param wh: 宽或高
        :param old_xy: 旧的x或y坐标
        :return:
        '''
        # 无变化
        if xy == None or xy == '':
            return old_xy

        # 字符串或负数
        if isinstance(xy, str) or xy < 0:
            xy = str(xy)  # 处理负数
            # 加减符
            op = ''
            if xy.startswith('+') or xy.startswith('-'):
                op = xy[0]
                xy = xy[1:]
            # 根据位置在屏幕中比例，计算坐标值
            if xy.endswith('%'):
                ratio = float(xy[:-1]) / 100
                xy = wh * ratio
            else:
                xy = int(xy)
            # 加减值
            if op != '':
                # 起始值
                y0 = old_xy
                if op == '+':  # 加
                    xy = y0 + xy
                else:  # 减
                    xy = y0 - xy
        # 最小也只能为0
        if xy < 0:
            xy = 0
        return xy

    # 滚动页面(传y坐标/位置在屏幕中比例)
    # :param y
    def page_scroll(self, y):
        page = self.page
        # 计算新的滚动位置
        y = self.calculate_new_scroll_pos(y, page.inner_size["height"], page.scroll_y)
        page.scroll_to(y)

    # 滚动元素(传元素+坐标)
    # :param config {id, css, path, pos}
    def scroll_by(self, config):
        ele = self.find_by_any(config)
        x, y = config['pos'].split(",", 1)
        # 计算新的滚动位置
        x = self.calculate_new_scroll_pos(x, ele.size['width'], ele.scroll_left)
        y = self.calculate_new_scroll_pos(y, ele.size['height'], ele.scroll_top)
        ele.scroll_to(x, y)

    # 向上滚动元素
    def scroll_up_by(self, config):
        config['pos'] = ',-50%'
        self.scroll_by(config)

    # 向下滚动元素
    def scroll_down_by(self, config):
        config['pos'] = ',+50%'
        self.scroll_by(config)

    # 向左滚动元素
    def scroll_left_by(self, config):
        config['pos'] = '+50%,'
        self.scroll_by(config)

    # 向右滚动元素
    def scroll_right_by(self, config):
        config['pos'] = '-50%,'
        self.scroll_by(config)

    # 切换(传元素+页面序号): 切换 swiper 容器当前的页面
    # :param config {id, css, path, index}
    def swiper_by(self, config):
        ele = self.find_by_any(config)
        # 切换到第二个tab
        ele.swipe_to(config['index'])

    # 长按
    # :param config {id, css, xpath}
    def long_press_by(self, config):
        ele = self.find_by_any(config)
        ele.long_press()

    # 敲击屏幕(传坐标)
    def tap(self, pos):
        x, y = pos.split(",", 1)  # 坐标
        self.native.click_coordinate(x, y)

    # 点击元素
    # :param config {id, css, xpath}
    def tap_by(self, config):
        self.click_by(config)

    # 点击元素
    # :param config {id, css, xpath}
    def click_by(self, config):
        ele = self.find_by_any(config)
        ele.click()

    # 如果按钮存在，则点击
    # :param config {id, css, xpath}
    def click_by_if_exist(self, config):
        try:
            ele = self.find_by_any(config)
        except:
            ele = None
        if ele != None:
            ele.click()

    # 处理授权弹窗: 允许
    def allow(self, perm):
        method = self.get_perm_allow_method(perm)
        method(True)

    # 处理授权弹窗: 禁止
    def forbid(self, perm):
        method = self.get_perm_allow_method(perm)
        method(False)

    # 获得授权的方法
    def get_perm_allow_method(self, perm):
        '''
            authorize: 处理授权确认弹框
            login: 处理微信登陆确认弹框
            get_user_info: 处理获取用户信息确认弹框
            get_location: 处理获取位置信息确认弹框
            get_we_run_data: 处理获取微信运动数据确认弹框
            record: 处理录音确认弹框
            write_photos_album: 处理保存相册确认弹框
            camera: 处理使用摄像头确认弹框
            get_user_phone: 处理获取用户手机号码确认弹框
            send_subscribe_message: 允许发送订阅消息
            get_we_run_data: 处理获取微信运动数据确认弹框
            '''
        perms = [
            'authorize',
            'login',
            'get_user_info',
            'get_location',
            'get_we_run_data',
            'record',
            'write_photos_album',
            'camera',
            'get_user_phone',
            'send_subscribe_message',
            'get_we_run_data',
        ]
        if perm not in perms:
            raise Exception(f"无效权限: {perm}")
        # 获得对应方法，如 login 权限对应授权方法为 self.native.allow_login()
        method = f"allow_{perm}"
        self.native[method]

    # 点击弹窗的按钮
    # :param btn_text 按钮文本或bool
    def handle_modal(self, btn_text = "确定"):
        if isinstance(btn_text, bool):
            if btn_text:
                btn_text = '确定'
            else:
                btn_text = '取消'
        self.native.handle_modal(btn_text)

    # 使微信进入后台一段时间, 再切回前台
    def deactive(self):
        self.native.deactivate(10)

    # 旋转
    # :param is_portrait 是否竖屏
    def set_orientation(self, is_portrait):
        '''
        PORTRAIT 竖屏模式
        LANDSCAPE 宽屏模式
        '''
        if self.driver.orientation == 'PORTRAIT':
            target = 'LANDSCAPE'
        else:
            target = 'PORTRAIT'
        self.native.orientation(target)

    # 设置地理位置
    # :param loc 地理位置,格式为`纬度,经度`
    def set_location(self, loc):
        parts = loc.split(",", 2)
        lat = parts[0]  # 纬度
        lon = parts[1]  # 经度
        # 模拟位置
        mock_location = {"latitude": lat, "longitude": lon, "speed": -1, "accuracy": 65,
                         "verticalAccuracy": 65, "horizontalAccuracy": 65, "errMsg": "getLocation:ok"}
        self.app.mock_wx_method("getLocation", result=mock_location)

    # 整个窗口截图存为png
    # :param config {save_dir, save_file}
    def screenshot(self, config):
        # 文件名
        default_file = str(time.time()).split(".")[0] + ".png"
        save_file = self._prepare_save_file(config, default_file)
        # self.driver.capture(save_file) # 不能指定存储目录
        self.app.screen_shot(save_file)

    # 执行js
    def execute_js(self, js):
        args = []
        ret = self.app.evaluate(js, args, sync=True)
        ret = ret.get("result", {}).get("result")

    # 调用微信函数
    def call_wx_method(self, method, args = None):
        if args == None and isinstance(method, list):
            args = method[1:]
            method = method[0]
        ret = self.app.call_wx_method(method, args)
        return ret.get("result", {}).get("result")

    # 跳转到指定页面, 但是不能跳到 tabbar 页面
    def goto(self, url):
        self.app.navigate_to(url)
        self.print_current_page()

    # 跳转到 tabBar 页面, 并关闭其他所有非 tabBar 页面
    def switch_tab(self, url_or_index):
        # 如果是索引，则转为url
        if isinstance(url_or_index, int):
            i = url_or_index
            tabs = self.appjson['tabBar']['list']
            if len(tabs) <= i:
                raise Exception(f'索引是{i}, 超过 tabBar 页面数')
            url = '/' + tabs[i]['pagePath']
        else:
            url = url_or_index
        self.app.switch_tab(url)

    # 返回键
    def back(self, _):
        self.app.navigate_back()

    # 读剪切板
    # :param var 记录剪切板内容的变量名
    def get_clipboard(self, var_name):
        txt = self.call_wx_method('getClipboardData')
        set_var(var_name, txt)

    # 写剪切板
    # :param txt 写入内容
    def set_clipboard(self, txt):
        txt = replace_var(txt)
        self.call_wx_method('setClipboardData', [{'data': txt}])

    # 推文件到手机上, 即写手机上文件
    # :param config {to,from} to是android路径
    def push_file(self, config):
        to = replace_var(config['to'])
        _from = replace_var(config['from'])
        # 写文件
        self.adb.compare_push(_from, to)

    # 从手机中拉文件, 即读手机上的文件
    # :param config {from,to} from是android路径
    def pull_file(self, config):
        _from = replace_var(config['from'])
        to = replace_var(config['to'])
        self.adb.pull(_from, to)

    # 下拉刷新
    def pull_down_refresh(self, _):
        self.call_wx_method("startPullDownRefresh")
        time.sleep(0.3)
        self.call_wx_method("stopPullDownRefresh")

    # 震动
    def vibrate(self, is_long):
        if is_long:
            self.call_wx_method("vibrateShort", [{'type': 'medium'}])
        else:
            self.call_wx_method("vibrateLong", [{'type': 'medium'}])

    # 扫码
    def scan_code(self, _):
        self.call_wx_method("scanCode")

    # 发送短信
    def send_sms(self, config):
        phone = replace_var(config['phone'])
        content = replace_var(config['content'])
        self.call_wx_method("sendSms", [{"phoneNumber": phone, "content": content}])

    # 打印系统信息
    def print_system_info(self, _):
        info = self.mini.get_system_info()
        log.debug('system_info: ' + json.dumps(info))

    # 打印所有页面
    def print_all_pages(self, _):
        log.debug('all pages: ' + ', '.join(self.app.get_all_pages_path()))

    # 打印当前页面
    def print_current_page(self, _):
        # page = self.app.get_current_page()
        page = self.page
        log.debug('current_page: ' + str(page) + ', data: ' + json.dumps(page.data))

    ##################################### http请求 ###########################################
    # 设置基础url
    def base_url(self, url):
        self._base_url = url

    # 拼接url
    def _get_url(self, config):
        url = config['url']
        url = replace_var(url)  # 替换变量
        # 添加基url
        if (self._base_url is not None) and ("http" not in url):
            url = self._base_url + url
        return url

    # get请求
    # :param config {url, is_ajax, data, validate_by_jsonpath, validate_by_css, validate_by_xpath, extract_by_jsonpath, extract_by_css, extract_by_xpath, extract_by_eval}
    def get(self, config = {}):
        url = self._get_url(config)
        data = replace_var(config['data'], False)
        headers = {}
        if 'is_ajax' in config and config['is_ajax']:
            headers = {
                'X-Requested-With': 'XMLHttpRequest'
            }
        res = requests.get(url, headers=headers, data=data)
        # log.debug(res.text)
        # 解析响应
        self._analyze_response(res, config)

    # post请求
    # :param config {url, is_ajax, data, validate_by_jsonpath, validate_by_css, validate_by_xpath, extract_by_jsonpath, extract_by_css, extract_by_xpath, extract_by_eval}
    def post(self, config = {}):
        url = self._get_url(config)
        data = replace_var(config['data'], False)
        headers = {}
        if 'is_ajax' in config and config['is_ajax']:
            headers = {
                'X-Requested-With': 'XMLHttpRequest'
            }
        res = requests.post(url, headers=headers, data=data)
        # 解析响应
        self._analyze_response(res, config)

    # 上传文件
    # :param config {url, files, validate_by_jsonpath, validate_by_css, validate_by_xpath, extract_by_jsonpath, extract_by_css, extract_by_xpath, extract_by_eval}
    def upload(self, config = {}):
        url = self._get_url(config)
        # 文件
        files = {}
        for name, path in config['files'].items():
            path = replace_var(path)
            files[name] = open(path, 'rb')
        # 发请求
        res = requests.post(url, files=files)
        # 解析响应
        self._analyze_response(res, config)

    # 下载文件
    # :param config {url, save_dir, save_file}
    def download(self, config={}):
        url = self._get_url(config)
        # 文件名
        save_file = self._prepare_save_file(config, url)
        # 真正的下载
        self._do_download(url, save_file)
        return save_file

    # 获得文件名
    # config['save_dir'] + config['save_file'] 或 url中的默认文件名
    def _prepare_save_file(self, config, url):
        # 获得保存的目录
        if 'save_dir' in config:
            save_dir = config['save_dir']
        else:
            save_dir = 'downloads'
        # 获得保存的文件名
        if 'save_file' in config:
            save_file = config['save_file']
        else:
            save_file = os.path.basename(url)
        save_file = os.path.abspath(save_dir + os.sep + save_file)  # 转绝对路径
        # 准备目录
        dir, name = os.path.split(save_file)
        if not os.path.exists(dir):
            os.makedirs(dir)
        # 检查重复
        if os.path.exists(save_file):
            for i in range(100000000000000):
                if '.' in save_file:
                    path, ext = save_file.rsplit(".", 1) # 从后面分割，分割为路径+扩展名
                    newname = f"{path}-{i}.{ext}"
                else:
                    newname = f"{save_file}-{i}"
                if not os.path.exists(newname):
                    return newname
            raise Exception('目录太多文件，建议新建目录')

        return save_file

    # 执行下载文件
    def _do_download(self, url, save_file):
        if url in self.downloaded_files:
            return self.downloaded_files[url]

        # 发请求
        res = requests.get(url)
        # 保存响应的文件
        write_byte_file(save_file, res.content)
        # 设置变量
        set_var('download_file', save_file)
        self.downloaded_files[url] = save_file
        log.debug(f"下载文件: url为{url}, 另存为{save_file}")
        return save_file

    # 播放视频/音频
    # :param config
    def play_by(self, config):
        self.video_ele = self.find_by_any(config)
        self.video_ele.play()

    # 暂停视频/音频
    def pause(self, _):
        self.video_ele.pause()

    # 停止视频/音频
    def stop(self, _):
        self.video_ele.stop()

    # 全屏or取消全屏
    # :param f 是否全屏
    def full_screen(self, f):
        if f:
            self.video_ele.request_full_screen()
        else:
            self.video_ele.exit_full_screen()

    def validate_by_jsonpath(self, fields):
        return self.validator.run_type('jsonpath', fields)

    def validate_by_css(self, fields):
        return self.validator.run_type('css', fields)

    def validate_by_xpath(self, fields):
        return self.validator.run_type('xpath', fields)

    def validate_by_id(self, fields):
        return self.validator.run_type('id', fields)

    def extract_by_jsonpath(self, fields):
        return self.extractor.run_type('jsonpath', fields)

    def extract_by_css(self, fields):
        return self.extractor.run_type('css', fields)

    def extract_by_xpath(self, fields):
        return self.extractor.run_type('xpath', fields)

    def extract_by_id(self, fields):
        return self.extractor.run_type('id', fields)

    def extract_by_eval(self, fields):
        return self.extractor.run_eval(fields)

    ##################################### 以下步骤是根据官方api封装, 但发现api无用 ###########################################
    # 获得根元素
    def get_root_element(self):
        # xpath: https://www.runoob.com/xpath/xpath-syntax.html
        # ele = self.page.get_element_by_xpath('/') # 报错的
        ele = self.page.get_element_by_xpath('.')
        return ele

    # 屏幕横扫(传坐标)
    # :param config {from, to, duration}
    def swipe(self, config):
        x1, y1 = config['from'].split(",", 1) # 起点位置
        x2, y2 = config['to'].split(",", 1) # 终点位置
        duration = 0
        if 'duration' in config:
            duration = float(config['duration'])
        self.do_swipe(x1, y1, x2, y2, duration)

    # 真正的横扫
    def do_swipe(self, x1, y1, x2, y2, duration):
        ele = self.get_root_element()
        # ele = self.find_by('xpath', '/page/view[3]/view[1]/image')

        # 两个手指移动到开始
        touch1 = self.build_touch(x1, y1, ele)
        ele.touch_start(touches=[touch1], changed_touches=[touch1])

        # 两个手指移动到结尾
        time.sleep(duration/2)
        touch2 = self.build_touch(x2, y2, ele)
        ele.touch_move(touches=[touch2], changed_touches=[touch2])

        time.sleep(duration/2)
        ele.touch_end(changed_touches=[touch2])

    # 上滑(传比例)
    # :param 移动幅度比例
    def swipe_up(self, move_ratio):
        if move_ratio == None:
            move_ratio = 0.5
        end = (1 - move_ratio) / 2
        start = 1 - end
        # self.swipe_vertical(f'0.75,0.25')
        self.swipe_vertical(f'{start},{end}')

    # 下滑(传比例)
    # :param 移动幅度比例
    def swipe_down(self, move_ratio):
        if move_ratio == None:
            move_ratio = 0.5
        start = (1 - move_ratio) / 2
        end = 1 - start
        # self.swipe_vertical('0.25,0.75')
        self.swipe_vertical(f'{start},{end}')

    # 左滑(传y坐标)
    # :param y y坐标，固定不变，默认为中间
    def swipe_left(self, y = None):
        self.swipe_horizontal('0.75,0.25', y)

    # 右滑(传y坐标)
    # :param y y坐标，固定不变，默认为中间
    def swipe_right(self, y = None):
        self.swipe_horizontal('0.25,0.75', y)

    # 垂直方向(上下)滑动
    # :param y_range_ratios y轴起点/终点位置在屏幕的比例，如 0.2,0.7，即y轴上从屏幕0.2比例处滑到0.7比例处
    # :param xm x坐标，固定不变，默认为中间
    def swipe_vertical(self, y_range_ratios, xm = None):
        # 获取屏幕的宽高
        size = self.page.inner_size
        w = size["width"]
        h = size["height"]
        # x不变：水平居中
        if xm == None:
            xm = int(w * 0.5)
        # y:按比例计算坐标
        y1_ratio, y2_ratio = y_range_ratios.split(",", 1) # y轴起点/终点位置在屏幕的比例
        y1 = int(h * float(y1_ratio))
        y2 = int(h * float(y2_ratio))
        duration = 0.1
        self.do_swipe(xm, y1, xm, y2, duration)

    # 水平方向(左右)滑动
    # :param x_range_ratios x轴起点/终点位置在屏幕的比例，如 0.2,0.7，即x轴上从屏幕0.2比例处滑到0.7比例处
    # :param ym y坐标，固定不变，默认为中间
    def swipe_horizontal(self, x_range_ratios, ym = None):
        # 获取屏幕的宽高
        size = self.page.inner_size
        w = size["width"]
        h = size["height"]
        # y不变：水平居中
        if ym == None:
            ym = int(h * 0.5)
        # x:按比例计算坐标
        x1_ratio, x2_ratio = x_range_ratios.split(",", 1)  # x轴起点/终点位置在屏幕的比例
        x1 = int(w * float(x1_ratio))
        x2 = int(w * float(x2_ratio))
        duration = 0.1
        self.do_swipe(x1, ym, x2, ym, duration)

    # 移动元素(传元素+坐标序列)
    # :param {id, css, path, pos} 其中pos坐标序列 如x1,y1;x2,y2
    def move_by(self, config):
        # 检查元素
        ele = self.find_by_any(config)

        # 位移
        positions = config['pos']
        positions = positions.split(";")
        for pos in positions:
            x, y = pos.split(",", 1)  # 坐标
            x = int(x)
            y = int(y)
            # 用move(通用)或move_to(仅支持movable-view)方法
            # ele.move_to(x, y)
            ele.move(x, y, 500, smooth=True)

    # 放大页面
    def zoom_in(self, _):
        ele = self.get_root_element()
        self.do_zoom(ele, True)

    # 缩小页面
    def zoom_out(self, _):
        ele = self.get_root_element()
        self.do_zoom(ele, False)

    # 放大某元素
    def zoom_in_by(self, config):
        ele = self.find_by_any(config)
        self.do_zoom(ele, True)

    # 缩小某元素
    def zoom_out_by(self, config):
        ele = self.find_by_any(config)
        self.do_zoom(ele, False)

    # 构建touch对象
    def build_touch(self, x, y, ele):
        page_offset = ele.page_offset
        ox = page_offset.x
        oy = page_offset.y
        return {
            "identifier": 0,
            "pageX": x,
            "pageY": y,
            "clientX": x - ox,
            "clientY": y - oy,
        }

    # 真正的缩放
    def do_zoom(self, ele, is_up):
        offset = ele.offset
        size = ele.size
        width = size["width"]
        height = size["height"]

        xm = offset["left"] + width * 0.5
        ys = offset["top"]
        start1, start2, end1, end2 = self.get_zoom_y_range_ratios(is_up)

        # 两个手指移动到开始
        start_touch1 = self.build_touch(xm, ys + height * start1, ele)
        start_touch2 = self.build_touch(xm, ys + height * start2, ele)
        ele.touch_start(touches=[start_touch1, start_touch2], changed_touches=[start_touch1, start_touch2])

        # 两个手指移动到结尾
        time.sleep(0.1)
        end_touch1 = self.build_touch(xm, ys + height * end1, ele)
        end_touch2 = self.build_touch(xm, ys + height * end2, ele)
        ele.touch_move(touches=[end_touch1, end_touch2], changed_touches=[end_touch1, end_touch2])

        time.sleep(0.1)
        ele.touch_end(changed_touches=[end_touch1, end_touch2])

    # 获得缩放时2个手指的y轴起点/终点位置在屏幕的比例，分别是: 两个手指的起点y比例, 两个手指的终点y比例
    def get_zoom_y_range_ratios(self, is_up):
        if is_up: # 放大：从中间到两边
            return 0.5, 0.5, 9.9, 0.1

        # 缩小: 从两边到中间
        return 9.9, 0.1, 0.5, 0.5


# cli入口
def main():
    # 基于yaml的执行器
    boot = Boot()
    try:
        # 步骤配置的yaml
        if len(sys.argv) > 1:
            step_files = sys.argv[1:]
        else:
            raise Exception("未指定步骤配置文件或目录")
        # 执行yaml配置的步骤
        boot.run(step_files)
    except Exception as ex:
        page = ''
        src = ''
        if boot.driver != None:
            page = boot.app.current_page
            src = boot.driver.page_source
            # report_to_sauce(boot.driver.session_id)
            # take_screenshot_and_logcat(boot.driver, device_logger, calling_request)
        # log.error(f"异常环境:当前步骤文件为 {step_file}, 当前page为 {page}, 当前层级为 {src}", exc_info = ex)
        log.error(f"异常环境:当前步骤文件为 {boot.step_file}, 当前page为 {page}", exc_info = ex)
        raise ex
    finally:
        boot
        #boot.close_driver()

if __name__ == '__main__':
    main()