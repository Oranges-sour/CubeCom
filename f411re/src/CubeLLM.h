#ifndef __CUBE_LLM_H__
#define __CUBE_LLM_H__

#include "Talk.h"

/*
CubeLLM的消息结构

i16 type 消息类型
针对每一种消息的结构体
*/

class CubeLLM {
   public:
    // 约定 返回负数则代表失败
    // 默认 message_id = 1 为最近一次的失败的消息提示

    // 创建一个会话，返回会话id
    i16 create_session();
    // 清除会话上下文
    i16 clear_session_context(i16 session_id);

    // 询问agent，返回消息id
    // session_id为负则代表没有会话
    i16 ask_agent(const char* agent_id, i16 session_id, const char* prompt);
    // 获得会话状态
    i16 get_session_statue(i16 session_id);

    // 返回消息id，获得会话的最新消息
    i16 get_recent_message(i16 session_id);

    // 消息中是否含有这个关键词
    i16 message_have(i16 message_id, const char* key_word);
    // 消息转语音
    i16 message_to_speech(i16 message_id);

    // 显示消息
    i16 show_message(i16 mesage_id);
    // 显示警告消息
    i16 show_alert(const char* alert_info);

   private:
    // 工具：发送请求并同步等回复（超时返回负数）
    i16 send_and_wait(const char* req);

    // 工具：格式化命令
    void fmt3(char* buf, int buflen, const char* cmd, const char* a1, int a2,
              const char* s);
    void fmt2(char* buf, int buflen, const char* cmd, int a1, const char* s);
    void fmt1(char* buf, int buflen, const char* cmd, const char* s);
    void fmt0(char* buf, int buflen, const char* cmd);
};

#endif
