import json
from common.logger import log
from . import PushChannel

class WeChatBot(PushChannel):
    def __init__(self, config):
        super().__init__(config)
        
        # 微信群名称列表
        self.group_names = config.get("group_names", [])
        if not self.group_names:
            log.error(f"【推送_{self.name}】配置不完整，未指定群聊名称，推送功能将无法正常使用")
            
        # 是否自动登录
        self.auto_login = config.get("auto_login", True)
        
        # 初始化微信机器人
        try:
            import itchat
            self.itchat = itchat
            if self.auto_login:
                try:
                    # 登录微信（热登录，如果存在缓存，则使用缓存）
                    self.itchat.auto_login(hotReload=True, enableCmdQR=2)
                    # 启动机器人
                    self.itchat.run(blockThread=False)
                    log.info(f"【推送_{self.name}】微信机器人登录成功")
                except IndexError as e:
                    log.error(f"【推送_{self.name}】微信机器人登录失败，可能是登录过期或网络问题: {e}")
                    log.error("请尝试手动登录或者删除itchat.pkl文件后重试")
                    self.itchat = None
                except Exception as e:
                    log.error(f"【推送_{self.name}】微信机器人登录失败: {e}")
                    self.itchat = None
        except ImportError:
            log.error(f"【推送_{self.name}】未安装itchat库，请执行 pip install itchat-uos")
            self.itchat = None
            
    # 手动登录方法
    def login(self):
        if self.itchat is None:
            try:
                import itchat
                self.itchat = itchat
            except ImportError:
                log.error(f"【推送_{self.name}】未安装itchat库，请执行 pip install itchat-uos")
                return False
                
        try:
            # 登录微信（热登录，如果存在缓存，则使用缓存）
            self.itchat.auto_login(hotReload=True, enableCmdQR=2)
            # 启动机器人
            self.itchat.run(blockThread=False)
            log.info(f"【推送_{self.name}】微信机器人登录成功")
            # 打印所有群聊名称，方便用户查看和配置
            self.print_all_chatrooms()
            return True
        except IndexError as e:
            log.error(f"【推送_{self.name}】微信机器人登录失败，可能是登录过期或网络问题: {e}")
            log.error("请删除itchat.pkl文件后重试")
            return False
        except Exception as e:
            log.error(f"【推送_{self.name}】微信机器人登录失败: {e}")
            return False
    
    # 打印所有群聊名称
    def print_all_chatrooms(self):
        if self.itchat is None:
            return
        
        chatrooms = self.itchat.get_chatrooms()
        if not chatrooms:
            log.info(f"【推送_{self.name}】未找到任何群聊")
            return
            
        log.info(f"【推送_{self.name}】找到 {len(chatrooms)} 个群聊，群聊名称列表:")
        for room in chatrooms:
            log.info(f"- {room['NickName']}")

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        if self.itchat is None:
            log.error(f"【推送_{self.name}】微信机器人未初始化，无法推送消息")
            return
        
        # 拼接消息内容
        message = f"{title}\n\n{content}"
        if jump_url:
            message += f"\n\n👉 {jump_url}"
        
        success_count = 0
        # 获取所有群聊
        all_chatrooms = self.itchat.get_chatrooms()
        log.info(f"【推送_{self.name}】未找到群聊: {all_chatrooms}，{self.group_names}")
        
        # 遍历所有指定的群聊名称
        for group_name in self.group_names:
            matched_rooms = []
            # 优先精确匹配
            for room in all_chatrooms:
                if room['NickName'] == group_name:
                    matched_rooms.append(room)
                    break
            
            # 如果精确匹配失败，尝试模糊匹配
            if not matched_rooms:
                for room in all_chatrooms:
                    if group_name in room['NickName'] or room['NickName'] in group_name:
                        matched_rooms.append(room)
                        log.info(f"【推送_{self.name}】找到类似群聊: {room['NickName']}，将使用此群聊")
            
            if matched_rooms:
                # 找到群聊，发送消息
                for room in matched_rooms:
                    try:
                        if pic_url:
                            # 如果有图片，先发送图片
                            self.itchat.send_msg(message, room['UserName'])
                            # 这里需要先下载图片再发送，简化版先省略图片发送
                            # self.itchat.send_image(pic_path, room['UserName'])
                        else:
                            # 没有图片，只发送文本
                            self.itchat.send_msg(message, room['UserName'])
                        success_count += 1
                        log.info(f"【推送_{self.name}】向群聊 {room['NickName']} 发送消息成功")
                    except Exception as e:
                        log.error(f"【推送_{self.name}】向群聊 {room['NickName']} 发送消息失败: {e}")
            else:
                log.error(f"【推送_{self.name}】未找到群聊: {group_name}")
        
        # 输出推送结果
        push_result = "成功" if success_count > 0 else "失败"
        log.info(f"【推送_{self.name}】向 {success_count}/{len(self.group_names)} 个群聊推送消息{push_result}")

    def __del__(self):
        # 在对象销毁时尝试登出微信
        if hasattr(self, 'itchat') and self.itchat:
            try:
                self.itchat.logout()
            except:
                pass 