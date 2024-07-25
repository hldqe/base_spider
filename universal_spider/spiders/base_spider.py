import ast
from copy import deepcopy
import logging
from typing import Any, Iterable
import scrapy
from scrapy.http.response import Response
from universal_spider.tools.parse import *
from universal_spider.tools.replacer import Replacer
from universal_spider.tools.request import *


class BaseSpider(scrapy.Spider):
    name = "base_spider"
    replacer = Replacer()

    stage_length = 0

    def __init__(self, *args, **kwargs: Any):
        # 调用父类的构造函数
        super(BaseSpider, self).__init__(*args, **kwargs)
        # 获取抓取配置
        self.config = kwargs.get("config", {})
        # 转化格式
        self.config = ast.literal_eval(self.config)
        # 类型检查
        if not isinstance(self.config, list):
            raise TypeError("config must be a list")
        # 初始化
        self.stage_length = len(self.config)
        logging.info(f"config: {self.config}")

    def start_requests(self):
        """
        根据初始化时的配置，生成请求顺序中的第一个请求
        """
        # 若无配置，则返回
        if self.stage_length == 0:
            return None
        # 默认，从第一个阶段开始
        now_index = 0
        # 获取初始阶段配置
        config = self.config[now_index]
        # 获取请求配置
        request_config = config["request"]
        # 获取响应配置
        response_config = config["response"]

        for req in self._generate_request(request_config, {}, now_index=now_index, response_config=response_config):
            yield req

    def _get_param_config(self, config_name: str, request_config: dict, item: dict, default=None, *args, **kwargs):
        """
        根据请求配置和当前item，生成请求参数
        """
        # ans = request_config.get(config_name, default)
        ans = request_config.pop(config_name, default)
        # ans = item.get(f"next_{config_name}", ans)
        ans = item.pop(f"next_{config_name}", ans)
        ans = ans[0] if isinstance(ans, list) else ans
        return ans

    def _generate_request(self, request_config: dict, item: dict, *args, **kwargs):
        """
        根据请求配置和当前item，生成请求
        """
        # 深度拷贝请求参数和item
        request_config = deepcopy(request_config)
        item = deepcopy(item)
        # 获取上个阶段的内容
        content = kwargs.get("content", "")
        # 定义替换器
        replacer = Replacer()
        # 获取配置
        config_fields = ["url", "type", "method", "headers", "iteration_times", "query_params", "json_params", "form_params"]
        for config_field in config_fields:
            default_value = 1 if config_field == "iteration_times" else None if config_field == "url" else {}
            field_value = self._get_param_config(config_field, request_config, item, default_value)
            request_config[config_field] = field_value

        iteration_times = request_config.pop("iteration_times", 1)
        while iteration_times > 0:
            iteration_times -= 1
            new_item = deepcopy(item)
            _, new_request_config = replacer.replace(request_config, content, item=new_item)
            yield Request(
                **request_config,
                callback=self.parse,
                cb_kwargs={
                    "now_index": kwargs["now_index"],
                    "item": new_item,
                    "response_config": kwargs.get("response_config", {}),
                },
            )

    async def parse(self, response: Response, **kwargs):
        """
        解析当前响应，发送解析结果或下一阶段请求
        """
        # 获取当前阶段索引
        now_index = kwargs["now_index"]
        # 获取上一阶段发送的item
        base_item = kwargs["item"]
        # 获取响应配置
        response_config = kwargs["response_config"]
        # 获取解析字段配置列表
        field_list = response_config["fields"]
        # 获取当前响应的内容
        content = response.text if response_config.get("type", "html") else response.json()
        # 基于base_item，生成新item列表（一个或多个）
        item_list = await self.update_item(base_item, field_list, response_config, response)
        # 当前阶段处理完成
        now_index += 1
        # 若结束发送item
        if now_index >= self.stage_length:
            for item in item_list:
                yield item
            return

        # 未结束,获取下一阶段配置
        config = self.config[now_index]
        # 获取请求配置
        request_config = config["request"]
        # 获取响应配置
        response_config = config["response"]

        # 循环每一项item
        for item in item_list:
            for req in self._generate_request(request_config, item, now_index=now_index, response_config=response_config, content=content):
                yield req

    async def update_item(self, base_item: dict, field_list: list, response_config: dict, response: Response):
        """
        根据当前响应内容以及字段配置，基于原item，更新item
        """
        item_copy = base_item.copy()
        for field_config in field_list:
            value = await self._parse_field(response, field_config, response_config)
            if field_config["name"] not in base_item.keys():
                item_copy[field_config["name"]] = value
            else:
                if field_config["save_method"] == "replace":
                    i