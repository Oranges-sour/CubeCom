#include <dirent.h>
#include <fcntl.h>
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

#include <random>
#include <string>

#include "lib.h"

extern int bad_msg_cnt;

std::string random_string(size_t length) {
    // 字符池，可以根据需要添加你想要的字符
    const std::string chars =
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789";

    // 随机数生成器
    std::random_device rd;   // 用于获取真正的随机种子
    std::mt19937 gen(rd());  // 使用种子初始化梅森旋转算法
    std::uniform_int_distribution<> dis(0, chars.size() - 1);

    std::string result;
    result.reserve(length);
    for (size_t i = 0; i < length; ++i) {
        result += chars[dis(gen)];
    }
    return result;
}

int main() {


    init("/dev/tty.usbmodem21103");

    int bytes_send = 0;
    int bytes_read = 0;
    auto t0 = steady_clock::now();
    while (true) {
        // send(random_string(128));
        // bytes_send += 128;
        // this_thread::sleep_for(100ms);
        if (!my_empty()) {
            static int cnt = 0;
            cnt += 1;
            auto s = receive();
            bytes_read += s.size();
            // printf("%d %s\n", cnt, s.c_str());

            auto t1 = steady_clock::now();
            double sec = duration_cast<milliseconds>(t1 - t0).count() / 1000.0;

            printf("r%d byte/s  w%d byte/s err%d\n", (int)(bytes_read / sec),
                   (int)(bytes_send / sec), bad_msg_cnt);

            // send(s);
        }
        this_thread::sleep_for(1ms);
    }

    return 0;
}
