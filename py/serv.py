import os
import time
import cubeCom
import requests
import uuid
import threading
import gui_display
import flet as ft

session_map = {}  # 用于保存映射关系：int16 id <-> Coze会话ID
message_map = {}  # 用于保存 message_id -> message 内容 的映射
session_recent_message = {}  # int16 -> message_id  会话最新一条消息
next_session_id = 2  #
next_message_id = 2  #
last_failed_message = "最近一次的失败消息"  # 默认失败消息

# COZE 配置
COZE_API_BASE = "https://api.coze.cn/v1"
COZE_GPT_API_BASE = " https://api.coze.cn/v3"
COZE_API_KEY = "pat_TzsWzEGdMY6pqIVi0TcCrYgMOlsOW4gk8fwb3wuCz6lsrq2vUNIYPDwauIfhY1zO"  # Coze API 密钥


# 创建会话
def create_session():
    global next_session_id
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "user": str(uuid.uuid4()),  # 用UUID模拟用户身份
    }
    try:
        response = requests.post(
            f"{COZE_API_BASE}/conversation/create", json=body, headers=headers
        )
        if response.status_code == 200 and response.json()["code"] == 0:
            coze_id = response.json()["data"]["id"]
            local_id = next_session_id
            session_map[local_id] = coze_id
            next_session_id += 1

            # 默认最近的消息指向错误消息
            session_recent_message[local_id] = 1

            return local_id
        else:
            print(
                f"Coze API error: {response.status_code}, {response.json()['code']}, {response.text}"
            )
            return -1
    except Exception as e:
        print(f"Exception while creating session: {e}")
        return -1


# 清除会话上下文
def clear_session_context(session_id):
    if session_id not in session_map:
        return -1

    coze_id = session_map[session_id]
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            f"{COZE_API_BASE}/conversations/{coze_id}/clear",
            headers=headers,
        )
        if response.status_code == 200 and response.json()["code"] == 0:
            return 0  # 成功
        else:
            print(f"Coze API error: {response.status_code}, {response.text}")
            return -1
    except Exception as e:
        print(f"Exception while clearing session: {e}")
        return -1


# 向 agent 提问
def ask_agent(agent_id, session_id, prompt, max_wait=30):
    global next_message_id

    # 会话检查
    if session_id not in session_map:
        print("会话未找到，请先初始化session_map")
        return -1
    coze_conversation_id = session_map[session_id]

    # 请求头
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json",
    }

    # 组装 additional_messages
    additional_messages = [
        {"role": "user", "type": "question", "content": prompt, "content_type": "text"}
    ]

    # 组装body
    body = {
        "bot_id": agent_id,
        "user_id": f"{session_id}",
        "additional_messages": additional_messages,
        "stream": False,
        "auto_save_history": True,
    }

    # 1. 发起对话请求
    try:
        resp = requests.post(
            f"{COZE_GPT_API_BASE}/chat?conversation_id={coze_conversation_id}&",
            json=body,
            headers=headers,
        )
        data = resp.json()
        if resp.status_code != 200 or data.get("code") != 0:
            print(f"Coze API error: {resp.status_code}, {resp.text}")
            return -1

        chat_id = data["data"]["id"]
        conversation_id = data["data"]["conversation_id"]

        # 2. 轮询查看对话状态
        detail_url = f"{COZE_GPT_API_BASE}/chat/retrieve?conversation_id={conversation_id}&chat_id={chat_id}&"
        status = "created"
        wait_count = 0

        while wait_count < max_wait:
            resp = requests.get(detail_url, headers=headers)
            detail = resp.json()
            if resp.status_code != 200 or detail.get("code") != 0:
                print(f"Retrieve error: {resp.status_code}, {resp.text}")
                return -1
            status = detail["data"]["status"]
            if status == "completed":
                break
            elif status in ("failed", "canceled"):
                print(
                    f"Chat failed: {detail['data'].get('last_error', {}).get('msg', 'Unknown error')}"
                )
                return -1
            time.sleep(1)
            wait_count += 1

        if status != "completed":
            print("等待超时，AI回复未完成")
            return -1

        # 3. 通过新API获取消息列表，筛选assistant的answer内容
        message_list_url = f"{COZE_GPT_API_BASE}/chat/message/list?conversation_id={conversation_id}&chat_id={chat_id}"
        resp = requests.get(message_list_url, headers=headers)
        msg_detail = resp.json()
        if resp.status_code != 200 or msg_detail.get("code") != 0:
            print(f"Message list error: {resp.status_code}, {resp.text}")
            return -1

        answer_content = ""
        for m in msg_detail.get("data", []):
            if m.get("role") == "assistant" and m.get("type") == "answer":
                answer_content = m.get("content", "")
                break

        # 4. 更新本地message_map
        message_id = next_message_id
        next_message_id += 1
        message_map[message_id] = answer_content

        session_recent_message[session_id] = message_id

        return message_id

    except Exception as e:
        print(f"Exception while asking agent: {e}")
        return -1


# 获取会话状态
def get_session_statue(session_id):
    if session_id not in session_map:
        return -1

    # 暂时未实现
    return 0
    # coze_id = session_map[session_id]
    # headers = {
    #     "Authorization": f"Bearer {COZE_API_KEY}",
    #     "Content-Type": "application/json",
    # }
    # try:
    #     response = requests.get(
    #         f"{COZE_API_BASE}/conversation/status",
    #         params={"conversation_id": coze_id},
    #         headers=headers,
    #     )
    #     if response.status_code == 200 and response.json()["code"] == 0:
    #         return 0  # 状态正常
    #     else:
    #         print(f"Coze API error: {response.status_code}, {response.text}")
    #         return -1
    # except Exception as e:
    #     print(f"Exception while getting session status: {e}")
    #     return -1


# 获取最新消息
def get_recent_message(session_id):
    global next_message_id
    if session_id not in session_map:
        return -1

    return session_recent_message[session_id]


# 消息中是否含有关键词
def message_have(message_id, keyword):
    if message_id not in message_map:
        return -1

    message = message_map[message_id]
    if keyword in message:
        return 1  # 关键词存在
    return 0  # 关键词不存在


# 消息转语音
def message_to_speech(message_id):
    if message_id not in message_map:
        return -1

    message = message_map[message_id]
    # 文本转语音API
    print(f"Text-to-speech: {message}")
    return 1


# 显示消息
def show_message(message_id):
    global last_failed_message
    if message_id == 1:
        # 当 message_id 为 1 时，返回最近的失败消息
        message = last_failed_message
    elif message_id not in message_map:
        return -1

    else:
        message = message_map[message_id]

    print(f"show message: '{message}'")
    gui_display.display_message(message)
    return 1


# 显示警告消息
def show_alert(alert_info):
    print(f"Alert: {alert_info}")
    gui_display.display_alert(alert_info)
    return 1


# 消息分发处理
def handle_message(msg: str):
    s1 = msg.replace("\n", " & ")
    print(f"msg:{s1}")
    lines = msg.strip().split("\n")
    cmd = lines[0]

    if cmd == "CREATE_SESSION":
        session_id = create_session()
        cubeCom.send(str(session_id))
    elif cmd == "CLEAR_SESSION_CONTEXT":
        session_id = int(lines[1])
        result = clear_session_context(session_id)
        cubeCom.send(str(result))
    elif cmd == "ASK_AGENT":
        agent_id = lines[1]
        session_id = int(lines[2])
        prompt = lines[3]
        message_id = ask_agent(agent_id, session_id, prompt)
        cubeCom.send(str(message_id))
    elif cmd == "GET_SESSION_STATUE":
        session_id = int(lines[1])
        result = get_session_statue(session_id)
        cubeCom.send(str(result))
    elif cmd == "GET_RECENT_MESSAGE":
        session_id = int(lines[1])
        message_id = get_recent_message(session_id)
        cubeCom.send(str(message_id))
    elif cmd == "MESSAGE_HAVE":
        message_id = int(lines[1])
        keyword = lines[2]
        result = message_have(message_id, keyword)
        cubeCom.send(str(result))
    elif cmd == "MESSAGE_TO_SPEECH":
        message_id = int(lines[1])
        result = message_to_speech(message_id)
        cubeCom.send(str(result))
    elif cmd == "SHOW_MESSAGE":
        message_id = int(lines[1])
        result = show_message(message_id)
        cubeCom.send(str(result))
    elif cmd == "SHOW_ALERT":
        alert_info = lines[1]
        result = show_alert(alert_info)
        cubeCom.send(str(result))
    else:
        cubeCom.send("-1")  # 未知指令返回错误


def main_loop():
    # 串口初始化
    if not cubeCom.init("/dev/tty.usbmodem21103"):
        return
    try:
        while True:
            if not cubeCom.empty():
                msg = cubeCom.receive()
                if msg:
                    handle_message(msg)
            time.sleep(0.1)
    except KeyboardInterrupt:
        cubeCom.close()
        print("串口关闭，程序1s后退出。")
        time.sleep(1)


if __name__ == "__main__":
    # 1. 先起业务主循环线程
    t = threading.Thread(target=main_loop, daemon=True)
    t.start()

    # 2. 用Flet方式启动GUI（必须主线程，不能直接调用run）
    ft.app(target=gui_display.run)

    gui_display.close_gui()
    # 3. 结束处理
    cubeCom.close()
    print("串口关闭，程序1s后退出。")
    time.sleep(1)
    print("程序已退出。")
