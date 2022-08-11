#!/usr/bin/env python3.10
import minium

class MiniTestDriver(minium.MiniTest):

    def test_boot(self):
        print('该方法在运行时会被修改为 MiniumBoot.boot.Boot.run_steps()')

    # 根据指定类型，查找元素
    def find_element_by(self, type, path):
        # https://minitest.weixin.qq.com/#/minium/Python/api/Page?id=get_element
        if type == 'id':
            return self.page.get_element('#' + path)
        if type == 'css':
            return self.page.get_element(path)
        if type == 'xpath':
            return self.page.get_element('', xpath = path)

        raise Exception(f"无效查找类型: {type}")