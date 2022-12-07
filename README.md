[GitHub](https://github.com/shigebeyond/MiniumBoot) | [Gitee](https://gitee.com/shigebeyond/MiniumBoot)

# MiniumBoot - yaml驱动Minium测试

## 概述
Minium是微信小程序的自动化测试工具，但是要写python代码；

考虑到部分测试伙伴python能力不足，因此扩展Minium，支持通过yaml配置测试步骤;

框架通过编写简单的yaml, 就可以执行一系列复杂的微信小程序操作步骤, 如点击/输入/移动/上下滑/左右滑/放大缩小/提取变量/打印变量等，极大的简化了伙伴编写自动化测试脚本的工作量与工作难度，大幅提高人效；

框架通过提供类似python`for`/`if`/`break`语义的步骤动作，赋予伙伴极大的开发能力与灵活性，能适用于广泛的测试场景。

框架提供`include`机制，用来加载并执行其他的步骤yaml，一方面是功能解耦，方便分工，一方面是功能复用，提高效率与质量，从而推进测试整体的工程化。

## 特性
1. 基于 Minium 1.2.8, Minium要求使用python3.8以上;
2. 支持通过yaml来配置执行的步骤，简化了自动化测试开发:
每个步骤可以有多个动作，但单个步骤中动作名不能相同（yaml语法要求）;
动作代表小程序上的一种操作，如tap/swipe/scoll等等;
3. 支持复杂的手势: 移动/上下滑/左右滑/放大缩小/多个点组成的移动轨迹等;
4. 支持提取器
5. 支持校验器
6. 支持类似python`for`/`if`/`break`语义的步骤动作，灵活适应各种场景
7. 支持`include`引用其他的yaml配置文件，以便解耦与复用

## todo
1. 支持更多的动作

## 安装
1. 安装 minium
```
pip3 install https://minitest.weixin.qq.com/minium/Python/dist/minium-latest.zip
```

2. 安装 MiniumBoot
```
pip3 install MiniumBoot
```

安装后会生成命令`MiniumBoot`;

注： 对于深度deepin-linux系统，生成的命令放在目录`~/.local/bin`，建议将该目录添加到环境变量`PATH`中，如
```
export PATH="$PATH:/home/shi/.local/bin"
```

## 使用
1. 修改配置文件(yml)中的 `init_driver` 动作的参数, 如平台、项目路径、开发者工具cli路径等

2. 使用
```
# 1 执行单个文件
MiniumBoot 步骤配置文件.yml

# 2 执行多个文件
MiniumBoot 步骤配置文件1.yml 步骤配置文件2.yml ...

# 3 执行单个目录, 即执行该目录下所有的yml文件
MiniumBoot 步骤配置目录

# 4 执行单个目录下的指定模式的文件
MiniumBoot 步骤配置目录/step-*.yml
```

## 步骤配置文件及demo
用于指定多个步骤, 示例见源码 [example](https://github.com/shigebeyond/MiniumBoot/tree/main/example) 目录下的文件;

顶级的元素是步骤;

每个步骤里有多个动作(如sleep)，如果动作有重名，就另外新开一个步骤写动作，这是由yaml语法限制导致的，但不影响步骤执行。

[demo](https://github.com/shigebeyond/MiniumBoot/blob/main/example/)

[demo视频](https://www.zhihu.com/zvideo/1542517561199009793)

## 查找元素的方法
参考[Page.get_element()](https://minitest.weixin.qq.com/#/minium/Python/api/Page?id=get_element)
1. id: 根据 name 属性值来查找
2. css: 根据 css selector 来查找 
3. xpath: 根据 xpath 来查找

## 配置详解
支持通过yaml来配置执行的步骤;

每个步骤可以有多个动作，但单个步骤中动作名不能相同（yaml语法要求）;

动作代表 Minium 上的一种操作，如tap/swipe/scoll等等;

下面详细介绍每个动作:

1. init_driver: 初始化driver, 必须定义在第一个步骤中的第一个动作
```yaml
# 初始化driver
- init_driver:
    debug_mode: debug
    enable_app_log: true
    # windows cli: F:\微信web开发者工具\cli.bat auto --project "F:\project\jym_wechat" --auto-port 9420
    project_path: F:\project\jym_wechat
    dev_tool_path: F:\微信web开发者工具\cli.bat 
    app: wx
    close_ide: false
    test_port: 9420
    assert_capture: true
    use_push: true
    auto_relaunch: true
    request_timeout: 60
    remote_connect_timeout: 300
#    account_info:
#      wx_nick_name: locker
#      open_id: o6zAJs_pwr**********aROZDjiw
    platform: ide # 小程序运行的平台，可选值为：ide, Android, IOS
    # 当 platform = Android 时
#    device_desire:
#      serial: f978cc97 # Android设备号 adb devices查看
#      uiautomator: UiAutomator2
    # 当 platform = IOS 时
#    device_desire:
#      wda_project_path: /Users/sherlock/.npm-global/lib/node_modules/appium/node_modules/appium-webdriveragent
#      os_type: ios
#      device_info:
#        udid: aee531018e668ff1aad*************2924e8
#        model: iPhone 6
#        version: 12.2.5
#        name: sherlock's iPhone
```

2. close_driver: 关闭driver
```yaml
close_driver:
```

3. sleep: 线程睡眠; 
```yaml
sleep: 2 # 线程睡眠2秒
```

4. print: 打印, 支持输出变量/函数; 
```yaml
# 调试打印
print: "总申请数=${dyn_data.total_apply}, 剩余份数=${dyn_data.quantity_remain}"
```

变量格式:
```
$msg 一级变量, 以$为前缀
${data.msg} 多级变量, 用 ${ 与 } 包含
```

函数格式:
```
${random_str(6)} 支持调用函数，目前仅支持以下几个函数: random_str/random_int/random_element/incr
```

函数罗列:
```
random_str(n): 随机字符串，参数n是字符个数
random_int(n): 随机数字，参数n是数字个数
random_element(var): 从list中随机挑选一个元素，参数var是list类型的变量名
incr(key): 自增值，从1开始，参数key表示不同的自增值，不同key会独立自增
```

5. input_by_id: 填充 id 指定的输入框; 
```yaml
input_by_id:
  # 输入框id: 填充的值(支持写变量)
  'name': '18877310999'
```

6. input_by_css: 填充 css selector 指定的输入框; 
```yaml
input_by_css:
  # 输入框css selector模式: 填充的值(支持写变量)
  '#account': '18877310999'
```

7. input_by_xpath: 填充 xpath 指定的输入框; 
```yaml
input_by_xpath:
  # 输入框xpath路径: 填充的值(支持写变量)
  "//input[@id='account']": '18877310999'
```

8. hide_keyboard: 隐藏键盘
```yaml
hide_keyboard:
```

9. page_scroll: 滚动页面(传y坐标/位置在屏幕中比例)
```yaml
# 滚动到绝对位置
page_scroll: 200 # y坐标, 单位px
page_scroll: 20% # 位置在屏幕中比例
# 滚动到相对位置：相对于上一次位置的相对位移
page_scroll: +200 # y位移
page_scroll: -20% # 位移在屏幕中比例
```

10. page_scroll_top: 滚动到页面顶部
```yaml
page_scroll_top: 
```

11. page_scroll_bottom: 滚动到页面底部
```yaml
page_scroll_bottom: 
```

12. scroll_by: 滚动某元素(传元素+坐标), 注意在基础库v2.23.4版本后支持
```yaml
scroll_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
    # 移动的位置/位移
    pos: 100,200 # 绝对位置(坐标)
    pos: +100,-200 # 相对位移
    pos: +30%,50% # 元素高度的比例
```

13. scroll_up_by: 向上滚动元素, 注意在基础库v2.23.4版本后支持
```yaml
scroll_up_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
```
    
14. scroll_down_by: 向下滚动元素, 注意在基础库v2.23.4版本后支持
```yaml
scroll_down_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
```
    
15. scroll_left_by: 向左滚动元素, 注意在基础库v2.23.4版本后支持
```yaml
scroll_left_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
```
    
16. scroll_right_by: 向右滚动元素, 注意在基础库v2.23.4版本后支持
```yaml
scroll_right_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
```

17. swiper_by: 切换 swiper 容器当前的页面
```yaml
swiper_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
    # 页面序号, 从0开始
    index: 2
```

18. long_press_by: 长按某元素
```yaml
long_press_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
```

19. tap: 敲击屏幕(传坐标)
```yaml
tap: 200,200
```

20. tap_by: 敲击元素
```yaml
tap_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    xpath: //view[@id='btn']
    # 耗时秒数, 可省, 可用于模拟长按
    duration: 10
```

21. click_by/click_by_if_exist: 点击元素; 
```yaml
click_by:
  # 元素查找方式(id/css/xpath多选一) : 查找的值
  xpath: //view[@id='btn']
```

如果点击之前要先判断元素是否存在，则换用 click_by_if_exist

22. allow: 处理授权弹窗-允许某权限
```yaml
allow: login # 授权类型
```

| 授权类型 | 描述 |
| ------------ | ------------ | 
| authorize | 处理授权确认弹框 |
| login | 处理微信登陆确认弹框 |
| get_user_info | 处理获取用户信息确认弹框 |
| get_location | 处理获取位置信息确认弹框 |
| get_we_run_data | 处理获取微信运动数据确认弹框 |
| record | 处理录音确认弹框 |
| write_photos_album | 处理保存相册确认弹框 |
| camera | 处理使用摄像头确认弹框 |
| get_user_phone | 处理获取用户手机号码确认弹框 |
| send_subscribe_message | 允许发送订阅消息 |
| get_we_run_data | 处理获取微信运动数据确认弹框 |

23. forbid: 处理授权弹窗-禁止某权限
```yaml
forbid: login # 授权类型
```

授权类型, 参考上一节`allow`动作

24. handle_modal: 点击弹窗的按钮
```yaml
handle_modal: # 按钮文本，可省，默认为"确定"
handle_modal: 确定
handle_modal: 取消
```

25. deactive: 使微信进入后台一段时间, 再切回前台
```yaml
deactive:
```

26. set_orientation: 设置屏幕方向
```yaml
set_orientation: true # 是否竖屏, 否则横屏
```

27. set_location: 设置地理位置
```yaml
set_location: 49,123 # 纬度,经度
```

28. screenshot: 整个窗口截图存为png; 
```yaml
screenshot:
    save_dir: downloads # 保存的目录，默认为 downloads
    save_file: test.png # 保存的文件名，默认为:时间戳.png
```

29. call_wx_method: 调用微信函数, 返回值放到变量`return_val`
```yaml
call_wx_method: scanCode
```

30. call_page_method: 调用页面函数, 返回值放到变量`return_val`
```yaml
call_page_method: getTabBar
```

31. goto: 跳转到指定页面, 但是不能跳到 tabbar 页面
```yaml
goto: /pages/home/index # 页面url
```

32. switch_tab: 跳转到 tabBar 页面, 并关闭其他所有非 tabBar 页面
```yaml
switch_tab: /pages/home/index # 页面url
switch_tab: 1 # 页面序号, 从0开始
```

33. execute_js: 执行js; 
```yaml
execute_js: console.log('hello world')
```

34. back: 返回键; 
```yaml
back: 
```

35. get_clipboard: 读剪切板内容; 
```yaml
get_clipboard: name # 参数为记录剪切板内容的变量名
```

36. set_clipboard: 写剪切板内容; 
```yaml
set_clipboard: hello world $name # 参数是写入内容，可带参数
```

37. push_file:推文件到手机上, 即写手机上文件; 
```yaml
push_file:
    to: /storage/emulated/0/documents/test/a.txt # 写入的手机上的文件
    from: a.txt # 写入内容的本地来源文件
```

38. pull_file:从手机中拉文件, 即读手机上的文件; 
```yaml
pull_file:
    from: /storage/emulated/0/documents/test/a.txt # 读取的手机上的文件
    to: a.txt # 写入的本地文件
print: $content
```

39. pull_down_refresh: 下拉刷新
```yaml
pull_down_refresh:
```

40. vibrate: 震动
```yaml
vibrate: true # 是否长震,否则短震
```

41. scan_code: 扫码
```yaml
scan_code:
```

42. send_sms:发送短信; 
```yaml
send_sms:
    phone: 13475556022
    content: hello $name
```

43. print_system_info: 打印系统信息
```yaml
print_system_info:
```

44. print_all_pages: 打印所有页面
```yaml
print_all_pages:
```

45. print_current_page: 打印当前页面
```yaml
print_current_page:
```

46. for: 循环; 
for动作下包含一系列子步骤，表示循环执行这系列子步骤；变量`for_i`记录是第几次迭代（从1开始）
```yaml
# 循环3次
for(3) :
  # 每次迭代要执行的子步骤
  - swipe_down:
    sleep: 2

# 循环list类型的变量urls
for(urls) :
  # 每次迭代要执行的子步骤
  - swipe_down:
    sleep: 2    

# 无限循环，直到遇到跳出动作
# 有变量for_i记录是第几次迭代（从1开始）
for:
  # 每次迭代要执行的子步骤
  - break_if: for_i>2 # 满足条件则跳出循环
    swipe_down:
    sleep: 2
```

47. once: 只执行一次，等价于 `for(1)`; 
once 结合 moveon_if，可以模拟 python 的 `if` 语法效果
```yaml
once:
  # 每次迭代要执行的子步骤
  - moveon_if: for_i<=2 # 满足条件则往下走，否则跳出循环
    swipe_down:
    sleep: 2
```

48. break_if: 满足条件则跳出循环; 
只能定义在for/once循环的子步骤中
```yaml
break_if: for_i>2 # 条件表达式，python语法
```

49. moveon_if: 满足条件则往下走，否则跳出循环; 
只能定义在for/once循环的子步骤中
```yaml
moveon_if: for_i<=2 # 条件表达式，python语法
```

50. moveon_if_exist_by: 如果检查元素存在 则往下走，否则跳出循环; 
只能定义在for/once循环的子步骤中
```yaml
moveon_if_exist_by:
    id: button1
```

51. break_if_exist_by: 如果检查元素存在 则跳出循环，否则往下走; 
只能定义在for/once循环的子步骤中
```yaml
break_if_exist_by:
    id: button1
```

52. include: 包含其他步骤文件，如记录公共的步骤，或记录配置数据(如用户名密码); 
```yaml
include: part-common.yml
```

53. set_vars: 设置变量; 
```yaml
set_vars:
  name: shi
  password: 123456
  birthday: 5-27
```

54. print_vars: 打印所有变量; 
```yaml
print_vars:
```

55. base_url: 设置基础url
```yaml
base_url: https://www.taobao.com/
```

56. get: 发get请求, 但无跳转; 
```yaml
get:
    url: $dyn_data_url # url,支持写变量
    extract_by_eval:
      dyn_data: "json.loads(response.text[16:-1])" # 变量response是响应对象
```

57. post: 发post请求, 但无跳转; 
```yaml
post:
    url: http://admin.jym1.com/store/add_store # url,支持写变量
    is_ajax: true
    data: # post的参数
      # 参数名:参数值
      store_name: teststore-${random_str(6)}
      store_logo_url: '$img'
```

58. upload: 上传文件; 
```yaml
upload: # 上传文件/图片
    url: http://admin.jym1.com/upload/common_upload_img/store_img
    files: # 上传的多个文件
      # 参数名:文件本地路径
      file: /home/shi/fruit.jpeg
    extract_by_jsonpath:
      img: $.data.url
```

59. download: 下载文件; 
变量`download_file`记录最新下载的单个文件
```yaml
download:
    url: https://img.alicdn.com/tfscom/TB1t84NPuL2gK0jSZPhXXahvXXa.jpg_q90.jpg
    save_dir: downloads # 保存的目录，默认为 downloads
    save_file: test.jpg # 保存的文件名，默认为url中最后一级的文件名
```

60. exec: 执行命令, 可用于执行 HttpBoot/SeleniumBoot/AppiumBoot/MiniumBoot 等命令，以便打通多端的用例流程
```yaml
exec: ls
exec: SeleniumBoot test.yml
```

## 校验器
主要是为了校验页面或响应的内容, 根据不同场景有2种写法
```
1. 针对当前页面, 那么校验器作为普通动作来写
2. 针对 get/post/upload 有发送http请求的动作, 那么校验器在动作内作为普通属性来写
```

不同校验器适用于不同场景
| 校验器 | 当前页面场景 | http请求场景 |
| ------------ | ------------ | ------------ |
| validate_by_id | Y | N |
| validate_by_css | Y | Y |
| validate_by_xpath | Y | Y |
| validate_by_jsonpath | N | Y |

1. validate_by_id:
从当前页面中校验 id 对应的元素的值
```yaml
validate_by_id:
  "cat_demo_text": # 元素的id
    '=': 'Hello world' # 校验符号或函数: 校验的值
```

2. validate_by_css: 
从html响应中校验类名对应的元素的值
```yaml
validate_by_css:
  '#id': # 元素的css selector 模式
    '>': 0 # 校验符号或函数: 校验的值, 即 id 元素的值>0
  '#goods_title':
    contains: 衬衫 # 即 title 元素的值包含'衬衫'
```

3. validate_by_xpath: 
从当前页面或html响应中校验 xpath 路径对应的元素的值
```yaml
validate_by_xpath:
  "//view[@id='goods_id']": # 元素的xpath路径
    '>': 0 # 校验符号或函数: 校验的值, 即 id 元素的值>0
  "//view[@id='goods_title']":
    contains: 衬衫 # 即 title 元素的值包含'衬衫'
```

4. validate_by_jsonpath: 
从json响应中校验 多层属性 的值
```yaml
validate_by_jsonpath:
  '$.data.goods_id':
     '>': 0 # 校验符号或函数: 校验的值, 即 id 元素的值>0
  '$.data.goods_title':
    contains: 衬衫 # 即 title 元素的值包含'衬衫'
```

#### 校验符号或函数
1. `=`: 相同
2. `>`: 大于
3. `<`: 小于
4. `>=`: 大于等于
5. `<=`: 小于等于
6. `contains`: 包含子串
7. `startswith`: 以子串开头
8. `endswith`: 以子串结尾
9. `regex_match`: 正则匹配
10. `exist`: 元素存在
11. `not_exist`: 元素不存在

## 提取器
主要是为了从页面或响应中提取变量, 根据不同场景有2种写法
```
1. 针对当前页面, 那么提取器作为普通动作来写
2. 针对 get/post/upload 有发送http请求的动作, 那么提取器在动作内作为普通属性来写
```

不同校验器适用于不同场景
| 校验器 | 页面场景 | http请求场景 |
| ------------ | ------------ | ------------ |
| extract_by_id | Y | N |
| extract_by_css | Y | Y |
| extract_by_xpath | Y | Y |
| extract_by_jsonpath | N | Y |
| extract_by_eval | Y | Y |

1. extract_by_id:
从当前页面中解析 id 对应的元素的值
```yaml
extract_by_id:
  # 变量名: 元素id
  goods_id: "cat_demo_text"
```

2. extract_by_css:
从当前页面或html响应中解析 css selector 模式指定的元素的值
```yaml
extract_by_css:
  # 变量名: css selector 模式
  goods_id: #goods_id
  url: image::attr(src) # 获得<image>的src属性
```

3. extract_by_xpath:
从当前页面或html响应中解析 xpath 路径指定的元素的值
```yaml
extract_by_xpath:
  # 变量名: xpath路径
  goods_id: //view[@id='goods_id']
  url: //image/@src # 获得<image>的src属性
```

4. extract_by_jsonpath:
从json响应中解析 多层属性 的值
```yaml
extract_by_jsonpath:
  # 变量名: json响应的多层属性
  img: $.data.url
```

5. extract_by_eval:
使用 `eval(表达式)` 执行表达式, 并将执行结果记录到变量中
```yaml
extract_by_eval:
    # 变量名: 表达式（python语法）
    dyn_data: "json.loads(response.text[16:-1])" # 变量response是响应对象
```

## 存疑的动作
> 注: 以下动作是用来触发滑动手势, 是根据minium官方api `move()/touchstart()/touchmove()/touchend()`封装的, 但我测试时发现移动失败, 因此这部分官方api应该是无效的, 等啥时候有效就可以启用

1. swipe: 屏幕横扫(传坐标)
```yaml
swipe: 
    from: 100,100 # 起点坐标
    to: 200,200 # 终点坐标
    duration: 2 # 耗时秒数, 可省
```

2. swipe_up: 上滑(传比例)
```yaml
swipe_up: 0.55 # 移动幅度比例(占屏幕高度的比例)
swipe_up: # 默认移动幅度比例为0.5
```

3. swipe_down: 下滑(传比例)
```yaml
swipe_down: 0.55 # 移动幅度比例(占屏幕高度的比例)
swipe_down: # 默认移动幅度比例为0.5
```

4. swipe_left: 左滑(传y坐标)
```yaml
swipe_left: 100 # y坐标
swipe_left: # 默认y坐标为中间
```

5. swipe_right: 右滑(传y坐标)
```yaml
swipe_right: 100 # y坐标
swipe_right: # 默认y坐标为中间
```

6. swipe_vertical: 垂直方向(上下)滑动(传比例)
```yaml
swipe_vertical: 0.2,0.7 # y轴起点/终点位置在屏幕的比例，如 0.2,0.7，即y轴上从屏幕0.2比例处滑到0.7比例处
```

7. swipe_horizontal: 水平方向(左右)滑动(传比例)
```yaml
swipe_horizontal: 0.2,0.7 # x轴起点/终点位置在屏幕的比例，如 0.2,0.7，即x轴上从屏幕0.2比例处滑到0.7比例处
```

8. move_by: 移动某元素(pos传坐标序列); 
```yaml
move_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //movable-view[@id='line']
    # 坐标序列，坐标之间使用;分割，如x1,y1;x2,y2
    pos: '800,1600;100,1600;100,600;800,600;360,600;360,1100'
```

9. zoom_in: 放大页面
```yaml
zoom_in: 
```

10. zoom_out: 缩小页面
```yaml
zoom_out: 
```

11. zoom_in_by: 放大某元素
```yaml
zoom_in_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
```

12. zoom_out_by: 缩小某元素
```yaml
zoom_out_by:
    # 元素查找方式(id/css/xpath多选一) : 查找的值
    #id: line
    xpath: //view[@id='line']
```
