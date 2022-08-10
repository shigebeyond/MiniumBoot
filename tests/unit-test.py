#!/usr/bin/env python3.10
import minium
class JymTest(minium.MiniTest):
    def test_get_system_info(self):
        sys_info = self.mini.get_system_info()
        self.logger.info(f'SDKVersion is: {sys_info.get("SDKVersion")}')  # 可以使用self.logger打印一些log
        self.assertIn("SDKVersion", sys_info)
        self.capture()

if __name__ == "__main__":
    import unittest
    loaded_suite = unittest.TestLoader().loadTestsFromTestCase(JymTest)
    result = unittest.TextTestRunner().run(loaded_suite)
    print(result)