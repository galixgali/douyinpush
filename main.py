import time
import sys

import schedule

import push_channel
import query_task
from common.config import global_config
from common.logger import log


def init_push_channel(push_channel_config_list: list):
    log.info("开始初始化推送通道")
    for config in push_channel_config_list:
        if config.get('enable', False):
            if push_channel.push_channel_dict.get(config.get('name', '')) is not None:
                raise ValueError(f"推送通道名称重复: {config.get('name', '')}")

            log.info(f"初始化推送通道: {config.get('name', '')}，通道类型: {config.get('type', None)}")
            push_channel.push_channel_dict[config.get('name', '')] = push_channel.get_push_channel(config)


def init_push_channel_test(common_config: dict):
    push_channel_config: dict = common_config.get("push_channel", {})
    send_test_msg_when_start = push_channel_config.get("send_test_msg_when_start", False)
    if send_test_msg_when_start:
        for channel_name, channel in push_channel.push_channel_dict.items():
            log.info(f"推送通道【{channel_name}】发送测试消息")
            channel.push(title=f"【{channel_name}】通道测试",
                         content=f"可正常使用🎉",
                         jump_url="https://www.baidu.com",
                         pic_url=None,
                         extend_data={})


def init_query_task(query_task_config_list: list):
    log.info("初始化查询任务")
    for config in query_task_config_list:
        if config.get('enable', False):
            current_query = query_task.get_query_task(config).query
            schedule.every(config.get("intervals_second", 60)).seconds.do(current_query)
            log.info(f"初始化查询任务: {config.get('name', '')}，任务类型: {config.get('type', None)}")
            # 先执行一次
            current_query()

    while True:
        schedule.run_pending()
        time.sleep(1)


def login_wechat():
    """登录微信机器人"""
    push_channel_config_list = global_config.get_push_channel_config()
    init_push_channel(push_channel_config_list)
    
    for channel_name, channel in push_channel.push_channel_dict.items():
        if isinstance(channel, push_channel.WeChatBot):
            log.info(f"开始登录微信机器人【{channel_name}】")
            success = channel.login()
            if success:
                log.info(f"微信机器人【{channel_name}】登录成功，可以开始使用")
                # 发送一条测试消息
                # channel.push(
                #     title="微信机器人登录成功",
                #     content="登录成功，现在可以接收推送消息了！",
                #     jump_url=None,
                #     pic_url=None
                # )
            else:
                log.error(f"微信机器人【{channel_name}】登录失败")


def main():
    # 处理命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "login_wechat":
            login_wechat()
            return
    
    common_config = global_config.get_common_config()
    query_task_config_list = global_config.get_query_task_config()
    push_channel_config_list = global_config.get_push_channel_config()
    # 初始化推送通道
    init_push_channel(push_channel_config_list)
    # 初始化推送通道测试
    init_push_channel_test(common_config)
    # 初始化查询任务
    init_query_task(query_task_config_list)


if __name__ == '__main__':
    main()
