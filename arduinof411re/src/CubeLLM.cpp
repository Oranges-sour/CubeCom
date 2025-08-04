#include "CubeLLM.h"

#include <Arduino.h>  // for millis()/delay()

// --- 工具函数 ---

void CubeLLM::fmt4(char* buf, int buflen, const char* cmd, const char* a1,
                   int a2, int a3, const char* s) {
    if (s)
        snprintf(buf, buflen, "%s\n%s\n%d\n%d\n%s\n", cmd, a1, a2, a3, s);
    else
        snprintf(buf, buflen, "%s\n%s\n%d\n%d\n", cmd, a1, a2, a3);
}

void CubeLLM::fmt3(char* buf, int buflen, const char* cmd, const char* a1,
                   int a2, const char* s) {
    if (s)
        snprintf(buf, buflen, "%s\n%s\n%d\n%s\n", cmd, a1, a2, s);
    else
        snprintf(buf, buflen, "%s\n%s\n%d\n", cmd, a1, a2);
}
void CubeLLM::fmt2(char* buf, int buflen, const char* cmd, int a1,
                   const char* s) {
    if (s)
        snprintf(buf, buflen, "%s\n%d\n%s\n", cmd, a1, s);
    else
        snprintf(buf, buflen, "%s\n%d\n", cmd, a1);
}
void CubeLLM::fmt1(char* buf, int buflen, const char* cmd, const char* s) {
    if (s)
        snprintf(buf, buflen, "%s\n%s\n", cmd, s);
    else
        snprintf(buf, buflen, "%s\n", cmd);
}
void CubeLLM::fmt0(char* buf, int buflen, const char* cmd) {
    snprintf(buf, buflen, "%s\n", cmd);
}

// 同步发送并等待回复
i16 CubeLLM::send_and_wait(const char* req) {
    Talk::send(req, strlen(req));

    char str[512];
    i16 len;
    Talk::read(str, len);
    str[len] = 0;

    return atoi(str);
}

// --- 具体接口实现 ---

i16 CubeLLM::create_session() {
    char req[256];
    fmt0(req, sizeof(req), "CREATE_SESSION");
    return send_and_wait(req);
}

i16 CubeLLM::clear_session_context(i16 session_id) {
    char req[256];
    fmt2(req, sizeof(req), "CLEAR_SESSION_CONTEXT", session_id, nullptr);
    return send_and_wait(req);
}

i16 CubeLLM::ask_agent(const char* agent_id, i16 session_id,
                       const char* prompt) {
    char req[256];
    fmt3(req, sizeof(req), "ASK_AGENT", agent_id, session_id, prompt);
    return send_and_wait(req);
}

i16 CubeLLM::get_session_statue(i16 session_id) {
    char req[256];
    fmt2(req, sizeof(req), "GET_SESSION_STATUE", session_id, nullptr);
    return send_and_wait(req);
}

i16 CubeLLM::get_recent_message(i16 session_id) {
    char req[256];
    fmt2(req, sizeof(req), "GET_RECENT_MESSAGE", session_id, nullptr);
    return send_and_wait(req);
}

i16 CubeLLM::message_have(i16 message_id, const char* key_word) {
    char req[256];
    fmt2(req, sizeof(req), "MESSAGE_HAVE", message_id, key_word);
    return send_and_wait(req);
}

i16 CubeLLM::message_to_speech(i16 message_id) {
    char req[256];
    fmt2(req, sizeof(req), "MESSAGE_TO_SPEECH", message_id, nullptr);
    return send_and_wait(req);
}

i16 CubeLLM::show_message(i16 message_id) {
    char req[256];
    fmt2(req, sizeof(req), "SHOW_MESSAGE", message_id, nullptr);
    return send_and_wait(req);
}

i16 CubeLLM::show_alert(const char* alert_info) {
    char req[256];
    fmt1(req, sizeof(req), "SHOW_ALERT", alert_info);
    return send_and_wait(req);
}

i16 CubeLLM::open_camera() {
    char req[256];
    fmt0(req, sizeof(req), "OPEN_CAMERA");
    return send_and_wait(req);
}

i16 CubeLLM::close_camera() {
    char req[256];
    fmt0(req, sizeof(req), "CLOSE_CAMERA");
    return send_and_wait(req);
}

i16 CubeLLM::take_photo() {
    char req[256];
    fmt0(req, sizeof(req), "TAKE_PHOTO");
    return send_and_wait(req);
}

i16 CubeLLM::show_photo(i16 photo_id) {
    char req[256];
    fmt2(req, sizeof(req), "SHOW_PHOTO", photo_id, nullptr);
    return send_and_wait(req);
}

i16 CubeLLM::ask_agent_with_photo(const char* agent_id, i16 session_id,
                                  i16 photo_id, const char* prompt) {
    char req[256];
    fmt4(req, sizeof(req), "ASK_AGENT_WITH_PHOTO", agent_id, session_id,
         photo_id, prompt);
    return send_and_wait(req);
}
