#!/usr/bin/env python3.10
import minium

class MiniTestDriver(minium.MiniTest):

    def test_boot(self):
        print('该方法在运行时会被修改为 MiniumBoot.boot.Boot.run_steps()')