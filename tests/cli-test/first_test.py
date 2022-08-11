#!/usr/bin/env python3.10
import minium
import time

class FirstTest(minium.MiniTest):

    def test_get_system_info(self):
        sys_info = self.mini.get_system_info()
        self.assertIn("SDKVersion", sys_info)

    def test_touch_start_move_end(self):
        """
        通过构造 touch_start -> touch_move, -> touch_end 事件模拟元素移动过程
        """
        page = self.app.current_page
        element = page.get_element("/page/view[3]/view[1]/image")
        rect = element.rect  # 获取元素原始的坐标
        x_offset = 30  # 设置元素需要横向移动的距离
        y_offset = 70  # 设置元素需要纵向向移动的距离
        move_delay = 350  # touch事件触发间隔, 单位毫秒
        offset = element.offset
        size = element.size
        page_offset = element.page_offset
        # 计算原始的事件参数
        ori_changed_touch = ori_touch = {
            "identifier": 0,
            "pageX": offset["left"] + size["width"] // 2,
            "pageY": offset["top"] + size["height"] // 2,
            "clientX": offset["left"] + size["width"] // 2 - page_offset.x,
            "clientY": offset["top"] + size["height"] // 2 - page_offset.y,
        }
        element.touch_start(touches=[ori_touch], changed_touches=[ori_changed_touch])
        time.sleep(move_delay / 2000)
        # 计算变化的事件参数
        changed_touch = touch = {
            "identifier": 0,
            "pageX": offset["left"] + size["width"] // 2 + x_offset,
            "pageY": offset["top"] + size["height"] // 2 + y_offset,
            "clientX": offset["left"] + size["width"] // 2 - page_offset.x + x_offset,
            "clientY": offset["top"] + size["height"] // 2 - page_offset.y + y_offset,
        }
        element.touch_move(touches=[touch], changed_touches=[changed_touch])
        time.sleep(move_delay / 2000)
        element.touch_end(changed_touches=[changed_touch])
        time.sleep(move_delay / 1000)
        # 验证
        time.sleep(1000)