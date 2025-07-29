#include <fcntl.h>
// #define PPPY
#ifdef PPPY
#include <pybind11/pybind11.h>
#endif
#include <termios.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <future>
#include <iostream>
#include <limits>
#include <queue>
#include <random>
#include <set>
#include <string>
#include <thread>
#include <utility>
#include <vector>
using namespace std;
using namespace std::chrono;

#include "Talk.h"

int serial = -1;

atomic_bool run;

future<void> fu1;

queue<string> in_que;

static mutex m;

bool init(const string& device) {
    run = true;

    serial = open(device.c_str(), O_RDWR | O_NOCTTY | O_NDELAY);
    if (serial == -1) {
        printf("open serial err!\n");
        return false;
    }
    struct termios options;
    tcgetattr(serial, &options);

    cfsetispeed(&options, B115200);  // 根据实际波特率设置
    cfsetospeed(&options, B115200);

    options.c_cflag |= (CLOCAL | CREAD);  // 本地连接, 使能接收
    options.c_cflag &= ~CSIZE;
    options.c_cflag |= CS8;       // 8位数据位
    options.c_cflag &= ~PARENB;   // 无校验
    options.c_cflag &= ~CSTOPB;   // 1位停止位
    options.c_cflag &= ~CRTSCTS;  // 无硬件流控

    options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);  // 原始输入模式
    options.c_iflag &= ~(IXON | IXOFF | IXANY);          // 无软件流控
    options.c_oflag &= ~OPOST;                           // 原始输出模式

    tcsetattr(serial, TCSANOW, &options);

    // 清空接收缓冲区
    tcflush(serial, TCIOFLUSH);

    fu1 = async([]() {
        char str[1024];
        i16 len;
        while (run) {
            serialEvent();

            Talk::read(str, len);
            if (len > 0) {
                str[len] = 0;
                {
                    unique_lock<mutex> lk(m);
                    in_que.push(string(str));
                }
            }

            this_thread::sleep_for(1ms);
        }
    });

    return true;
}

void sclose() {
    run = false;
    fu1.get();
    close(serial);
}

void send(const string& str) { Talk::send(str.c_str(), str.size()); }

bool my_empty() {
    unique_lock<mutex> lk(m);
    return in_que.empty();
}

string receive() {
    unique_lock<mutex> lk(m);
    if (in_que.empty()) {
        return string("");
    }

    string str = in_que.front();
    in_que.pop();

    return str;
}
#ifdef PPPY
namespace py = pybind11;

PYBIND11_MODULE(cubeCom, m) {
    m.doc() = "pybind11 cubeCom plugin";

    m.def("init", &init, "打开串口并初始化");
    m.def("close", &sclose, "关闭串口并清理");
    m.def("send", &send, "发送数据");
    m.def("empty", &my_empty, "in队列是否为空");
    m.def("receive", &receive, "从in队列获取一条消息");
}

#endif
