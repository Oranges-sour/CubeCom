#include "Talk.h"

msg Talk::queue[QUEUE_SIZE] = {};
i16 Talk::head = 0;
i16 Talk::tail = 0;

extern int serial;

constexpr char PRE_CHR = 0xAA;
constexpr char START_CHR = 0xAB;

enum State { s_prefix = 0, s_start_b, s_len, s_data, s_check_sum };

State state = s_prefix;

i16 pre_cnt = 0;

i16 msg_len = 0;
i16 check_sum = 0;
i16 check_len_cnt = 0;
i16 start_len_cnt = 0;
i16 data_len_cnt = 0;

char data_buf[DATA_BUF_SIZE];

i16 to_big(i16 x) {
#if BYTE_ORDER == BIG_ENDIAN
    return x;
#else
    i16 a;
    *(char*)&a = x >> 8;
    *(((char*)&a) + 1) = x & 0xFF;
    return a;
#endif
}

struct MsgHead {
    char prefix[7];
    char start;
    i16 len;
};

bool update();

void Talk::send(const char* smsg, i16 len) {
    msg m;
    m.len = len;
    memcpy(m.d, smsg, len);

    char buf[DATA_BUF_SIZE * 2];

    MsgHead head;
    for (i16 i = 0; i < 7; ++i) {
        head.prefix[i] = PRE_CHR;
    }
    head.start = START_CHR;
    head.len = to_big(m.len);

    i16 check_sum = 0;
    for (i16 i = 0; i < m.len; ++i) {
        check_sum += *(unsigned char*)&m.d[i];
    }
    check_sum = to_big(check_sum);
    memcpy(buf, (const void*)&head, sizeof(head));
    memcpy(buf + sizeof(head), m.d, m.len);
    memcpy(buf + sizeof(head) + m.len, (const void*)&check_sum,
           sizeof(check_sum));
    Serial.write(buf, sizeof(head) + m.len + sizeof(check_sum));
}

void Talk::read(char* buf, i16& len) {
    while (empty()) {
        update();
    }

    memcpy(buf, queue[head].d, queue[head].len);
    len = queue[head].len;
    head += 1;
    head %= QUEUE_SIZE;
}

bool Talk::empty() { return head == tail; }

void Talk::incoming(const char* buf, i16 len) {
    if ((tail + 1) % QUEUE_SIZE == head) {
        return;
    }
    memcpy(queue[tail].d, buf, len);
    queue[tail].len = len;
    tail += 1;
    tail %= QUEUE_SIZE;
}

void serialEvent() { update(); }

bool update() {
    // int _byte = fgetc(serial);
    while (Serial.available() > 0) {
        i16 byte = Serial.read();
        switch (state) {
            case s_prefix:
                if (byte == PRE_CHR) {
                    pre_cnt += 1;
                } else {
                    pre_cnt = 0;
                }

                if (pre_cnt == 7) {
                    state = s_start_b;
                }
                break;
            case s_start_b:
                if (byte == START_CHR) {
                    state = s_len;
                    start_len_cnt = 0;
                    msg_len = 0;
                } else {
                    state = s_prefix;
                    pre_cnt = 0;
                    // Serial.println("1 Err!");
                }

                break;
            case s_len:
                if (start_len_cnt == 0) {
#if BYTE_ORDER != BIG_ENDIAN
                    msg_len = (byte << 8);
#else
                    msg_len = byte;
#endif
                    start_len_cnt += 1;
                } else if (start_len_cnt == 1) {
#if BYTE_ORDER != BIG_ENDIAN
                    msg_len = msg_len | (byte & 0xFF);
#else
                    msg_len = msg_len | ((byte << 8) & 0xFF00);
#endif

                    state = s_data;
                    data_len_cnt = 0;
                }
                break;
            case s_data:
                // 如果消息长度过大，则丢弃这个包
                if (msg_len > DATA_BUF_SIZE) {
                    state = s_prefix;
                    pre_cnt = 0;
                    // Serial.println("big Err!");
                }

                if (data_len_cnt < msg_len) {
                    data_buf[data_len_cnt] = byte;
                    data_len_cnt += 1;

                    if (data_len_cnt >= msg_len) {
                        state = s_check_sum;
                        check_len_cnt = 0;
                        check_sum = 0;
                    }
                } else {
                    state = s_check_sum;
                    check_len_cnt = 0;
                    check_sum = 0;
                }
                break;
            case s_check_sum:
                if (check_len_cnt == 0) {
#if BYTE_ORDER != BIG_ENDIAN
                    check_sum = (byte << 8);
#else
                    check_sum = byte;
#endif
                    check_len_cnt += 1;
                } else if (check_len_cnt == 1) {
#if BYTE_ORDER != BIG_ENDIAN
                    check_sum = check_sum | (byte & 0xFF);
#else
                    check_sum = check_sum | ((byte << 8) & 0xFF00);
#endif
                    // 检验check_sum
                    i16 check1 = 0;
                    for (i16 i = 0; i < msg_len; ++i) {
                        check1 += data_buf[i];
                    }
                    bool suc = false;
                    if (check1 == check_sum) {
                        // 检验成功，说明是正确的消息
                        // 推入队列
                        Talk::incoming(data_buf, msg_len);
                        suc = true;
                    }

                    state = s_prefix;
                    pre_cnt = 0;

                    if (suc) {
                        return true;
                    }
                }
                break;
            default:
                break;
        }
    }
    return false;
}
