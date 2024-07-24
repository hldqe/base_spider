default_stage_template = {
    "request": {  # 当前阶段请求
        "type": "",  # api/browser
        "url": "",
        "method": "",  # get/post...
        "iteration_times": 1,  # 当前阶段多个页面，迭代次数
        "headers": {},
        "params": {
            "query": {},
            "json": {},
            "form": {},
        },
        "playwright_config": {},
        "dont_filter": True,
        "extract": {},
    },
    "response": {  # 当前阶段响应
        "type": "",  # json/html/browser
        "before_parse": [],
        "fields": [],  # 解析字段的列表 [default_field_template]
        "save_fields": [],  # 保存字段的列表 上边所有解析后的字段最终需要保存的字段名称
        "extract": {},
    },
}

default_field_template = {
    "name": "",  # 字段名称
    "value": "",  # 字段值，其中可变值使用{}包裹  # {jsonpath:path} {xpath://table} {css:ul>li} {regex:[0-9]+} {var:var_name} {function:function_name(args)}
    "type": "",  # 字段类型  # str、json、date、file等
    "default": "",  # 默认值  # 默认为空
    "befor_process": [  #字段解析前，顺序执行的前处理方法 # 可选，默认为空
        {
            "name": "",  # 处理方法名称
            "args": ""  # 处理方法参数，其中可变值使用{}包裹
        },
    ],
    "after_process": [  #字段解析后，顺序执行的后处理方法 # 可选，默认为空
        {
            "name": "",  # 处理方法名称
            "args": ""  # 处理方法参数，其中可变值使用{}包裹
        },
    ],
    "save_method": "",  # 字段解析后，保存方法  # replace、append、add 默认替换原本的同名字段
}

# def create_config(crawl_type, response_type):
#     global times
#     config = {}

#     if crawl_type == "api":
#         config['crawl_type'] = "api"
#         if response_type == "json":
#             config['response_type'] = "json"
#         elif response_type == "html":
#             config['response_type'] = "html"
#         else:
#             config['response_type'] = response_type
#             logging.warning(f"抓取阶段{times}: 未知的响应类型{response_type}")
#     elif crawl_type == "browser":
#         config['crawl_type'] = "browser"
#         config['response_type'] = "browser"
#     else:
#         raise Exception("抓取方式设置有误")
