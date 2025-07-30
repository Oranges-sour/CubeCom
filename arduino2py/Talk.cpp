#include "Talk.h"

msg Talk::queue[QUEUE_SIZE] = {};
i16 Talk::head = 0;
i16 Talk::tail = 0;

extern int serial;

// 错误消息计数器
int bad_msg_cnt = 0;

constexpr i16 PRE_CHR = 0xAA;
constexpr i16 START_CHR = 0xAB;

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
    *(char*)&a = *((char*)&x + 1);
    *(((char*)&a) + 1) = *((char*)&x);
    return a;
#endif
}

i16 to_local(i16 x) {
#if BYTE_ORDER == BIG_ENDIAN
    return x;
#else
    i16 a;
    *(char*)&a = *(((char*)&x + 1));
    *(((char*)&a) + 1) = *((char*)&x);
    return a;
#endif
}

struct MsgHead {
    char prefix[7];
    char start;
    i16 len;
};

void update(i16 byte);

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
    write(serial, buf, sizeof(head) + m.len + sizeof(check_sum));
}

void Talk::read(char* buf, i16& len) {
    if (empty()) {
        len = 0;
        return;
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

void serialEvent() {
    char buf[512];
    int n = read(serial, buf, 512);
    if (n <= 0) {
        return;
    }
    // printf("read: %d\n", n);
    for (int i = 0; i < n; ++i) {
        update((i16) * (unsigned char*)&buf[i]);
    }
}

void update(i16 byte) {
    switch (state) {
        case s_prefix:
            if (byte == PRE_CHR) {
                pre_cnt += 1;
            } else {
                bad_msg_cnt += 1;
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
                bad_msg_cnt += 1;
            }

            break;
        case s_len:
            if (start_len_cnt == 0) {
                *((char*)&msg_len) = (byte & 0xFF);
                start_len_cnt += 1;
            } else if (start_len_cnt == 1) {
                *(((char*)&msg_len) + 1) = (byte & 0xFF);

                msg_len = to_local(msg_len);
                state = s_data;
                data_len_cnt = 0;
            }
            break;
        case s_data:
            // 如果消息长度过大，则丢弃这个包
            if (msg_len > DATA_BUF_SIZE) {
                state = s_prefix;
                pre_cnt = 0;
                bad_msg_cnt += 1;
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
                *((char*)&check_sum) = (byte & 0xFF);
                check_len_cnt += 1;
            } else if (check_len_cnt == 1) {
                *(((char*)&check_sum) + 1) = (byte & 0xFF);
                check_sum = to_local(check_sum);

                // 检验check_sum
                i16 check1 = 0;
                for (i16 i = 0; i < msg_len; ++i) {
                    check1 += *(unsigned char*)&data_buf[i];
                }
                if (check1 == check_sum) {
                    // 检验成功，说明是正确的消息
                    // 推入队列
                    Talk::incoming(data_buf, msg_len);
                } else {
                    bad_msg_cnt += 1;
                }

                state = s_prefix;
                pre_cnt = 0;
            }
            break;
        default:
            break;
    }
}
