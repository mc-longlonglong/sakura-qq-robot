import json
from nonebot import get_plugin_config, on_message, get_bot, on_command
from nonebot.rule import to_me, Rule
from nonebot.plugin import PluginMetadata
from nonebot.exception import MatcherException
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg
from nonebot.adapters import Message
import datetime
import asyncio
import websockets
import threading
import nonebot
import os
from .cryptoutils import CryptoUtils

import websockets.protocol

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="sakura",
    description="",
    usage="",
    config=Config,
)
crypto = CryptoUtils()

# group_id = 332411779
group_id = 332411779
url = "https://gw-panel.xyeidc.com/server/b60be1c5/files/edit#/logs/latest.log"
last_content = None
# 线程安全的消息队列
global wbs
wbs = None

bots = nonebot.get_bots()
print(bots)

async def get_nickname_from_group(user_id: int, group_id: int) -> str:
    bot: Bot = get_bot()
    try:
        member_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        return member_info['nickname']  # 返回群昵称
    except Exception as e:
        print(f"Error fetching group member info: {e}")
        return "Unknown"  # 如果获取失败，返回未知

# 定义一个规则，仅当消息来自特定群组时才触发
def from_specific_group() -> Rule:
    async def _from_specific_group(event: MessageEvent) -> bool:
        return isinstance(event, GroupMessageEvent) and event.group_id == group_id
    return Rule(_from_specific_group)

config = get_plugin_config(Config)

sakura = on_message(rule=from_specific_group(), priority=5,block=False)

# 任何消息都会触发这个命令
changeInActionText = on_command("更换进入", priority=2, block=True)

changeLeaveText = on_command("更换退出", priority=2, block=True)

changeActionHelper = on_command("更换帮助", priority=2, block=True)

@changeInActionText.handle()
async def change_inter_action_text_handle(args: Message = CommandArg()):
    # 尝试获取命令参数
    print("changeInActionText " + str(args))
    arr = args.extract_plain_text().split(" ")
    if len(arr) < 2:
        await changeInActionText.finish("请输入正确的命令格式")
    else:
        file_path = "data/sakura/player_in_out.json"
        if not os.path.exists(file_path):
            # 如果文件不存在，则创建一个默认的数据文件
            data = {}
            f = open(file_path, "w")
            json.dump(data, f)
            await changeInActionText.finish("数据文件不存在，已创建新文件，请重新执行命令。")
        else:
            with open(file_path, "r") as f:
                data = json.load(f)
            in_text = ""
            for i in range(1, len(arr)):
                in_text += arr[i]
                if i != len(arr) - 1:
                    in_text += " "
                    arr[1] = in_text
            if arr[0] not in data:
                data[arr[0]] = {}
                data[arr[0]]['join'] = in_text
                with open(file_path, "w") as f:
                    json.dump(data, f)
                await changeInActionText.finish("进入语句修改成功")
            else:
                data[arr[0]]['join'] = in_text
                with open(file_path, "w") as f:
                    json.dump(data, f)
                await changeInActionText.finish("进入语句修改成功")

@changeLeaveText.handle()
async def change_leave_action_text_handle(args: Message = CommandArg()):
    # 尝试获取命令参数
    print("changeLeaveText " + str(args))
    arr = args.extract_plain_text().split(" ")
    if len(arr) < 2:
        await changeLeaveText.finish("请输入正确的命令格式")
    else:
        file_path = "data/sakura/player_in_out.json"
        if not os.path.exists(file_path):
            # 如果文件不存在，则创建一个默认的数据文件
            data = {}
            f = open(file_path, "w")
            json.dump(data, f)
            await changeLeaveText.finish("数据文件不存在，已创建新文件，请重新执行命令。")
        else:
            with open(file_path, "r") as f:
                data = json.load(f)

            # 把除了arr[0]以外的所有都拼成字符串
            in_text = ""
            for i in range(1, len(arr)):
                in_text += arr[i]
                if i != len(arr) - 1:
                    in_text += " "
                    arr[1] = in_text
            if arr[0] not in data:
                data[arr[0]] = {}
                data[arr[0]]['leave'] = in_text
                with open(file_path, "w") as f:
                    json.dump(data, f)
                await changeLeaveText.finish("退出语句修改成功")
            else:
                data[arr[0]]['leave'] = in_text
                with open(file_path, "w") as f:
                    json.dump(data, f)
                await changeLeaveText.finish("退出语句修改成功")


@changeActionHelper.handle()
async def change_action_text_help_handle():
    help_message = (
        "使用以下命令格式来更换玩家的进入或退出语句：\n\n"
        "/更换进入 昵称 进入语句\n"
        "例如: /更换进入 JustinXC 哈哈哈地进入游戏\n\n"
        "/更换退出 昵称 退出语句\n"
        "例如: /更换退出 JustinXC 悄悄地离开了游戏"
    )
    await changeActionHelper.finish(MessageSegment.text(help_message))


@sakura.handle()
async def handle_function(event: MessageEvent):
    try:
        # print(event)
        # 获取发送人昵称
        sender_id = event.get_user_id()
        sender_name = await get_nickname_from_group(sender_id, group_id)
        # 获取消息内容
        message = event.get_message()
        return_msg = ""
        for m in message:
            # 使用最新的matchs
            match m.type:
                case "text":
                    return_msg += f"{sender_name}：{m.data.get('text', '')}"
                case "face":
                    if return_msg == "":
                        return_msg += f"{sender_name}："
                    return_msg += "[表情]"
                case "image":
                    if return_msg == "":
                        return_msg += f"{sender_name}："
                    return_msg += "[图片]"
                case "at":
                    return_msg += f"[@{await get_nickname_from_group(m.data.get('qq', ''),group_id)}]"
                case _:
                    return_msg += f"[{m.type}]"
        # {message: return_msg, timestamp: time.time()}
        msg = {
            "timestamp": datetime.datetime.now().timestamp(),
            "message": return_msg
        }
        msg = crypto.encrypt(json.dumps(msg))
        global wbs            
        await wbs.send(msg)
    except Exception as e:
        print(f"Error handling message: {e}")


async def websocket_server():
    async def handler(websocket, path):
        try:
            global wbs
            wbs = websocket
            bot = nonebot.get_bot()
            async for message in websocket:
                try:
                    message = crypto.decrypt(message)
                    message = json.loads(message)
                    # timestamp = message['timestamp']
                    # # 判断当前时间和timestamp的时间差是否大于10秒
                    # if datetime.datetime.now().timestamp() - timestamp > 10:
                    #     print("Invalid timestamp")
                    #     return
                    message = message['message']
                except json.JSONDecodeError:
                    print("Invalid JSON")
                    return
                
                if message['eventType'] == "join":
                    # 判断根目录下的data/sakura/player_in_out.json文件是否存在
                    return_msg = getInteractionText(message['player'], "join")
                    await bot.send_group_msg(group_id=group_id, message=return_msg, auto_escape=True)
                elif message['eventType'] == "chat":
                    await bot.send_group_msg(group_id=group_id, message=f"{message['player']}说：{message['message']}")
                elif message['eventType'] == "leave":
                    return_msg = getInteractionText(message['player'], "leave")
                    await bot.send_group_msg(group_id=group_id, message=return_msg, auto_escape=True)
                elif message['eventType'] == "death":
                    await bot.send_group_msg(group_id=group_id, message=f"{message['message']}")
        except websockets.ConnectionClosed:
            print("Connection closed")

    async with websockets.serve(handler, "0.0.0.0", 20112):
        print("WebSocket Server running on ws://localhost:20112")
        await asyncio.Future()  # 运行直到被外部方式关闭

def getInteractionText(nickname, type):
     with open("data/sakura/player_in_out.json", "r") as f:
        data = json.load(f)
        # 判断这个人的nickname是否存在于json中
        if nickname not in data:
            if type == "join":
                return f"{nickname}加入了游戏，欢迎~"
            elif type == "leave":
                return f"{nickname}离开了游戏，再见哦~"
        else:
            if type == "join":
                return nickname+data[nickname]['join']
            elif type == "leave":
                return nickname+data[nickname]['leave']

def run_websocket_server():
    asyncio.run(websocket_server())

# 创建并启动线程
thread = threading.Thread(target=run_websocket_server)
thread.start()


