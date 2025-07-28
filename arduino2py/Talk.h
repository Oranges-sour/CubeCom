#ifndef __TALK_H__
#define __TALK_H__
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

using i16 = int16_t;
using u16 = u_int16_t;

constexpr i16 DATA_BUF_SIZE = 512;

constexpr i16 QUEUE_SIZE = 5;

i16 to_big(i16 x);

void serialEvent();

struct msg {
    i16 len;
    char d[DATA_BUF_SIZE];
};

class Talk {
   public:
    static void send(const char* msg, i16 len);

    static void read(char* buf, i16& len);

    static void incoming(const char* msg, i16 len);

   private:
    static bool empty();
    static i16 head;
    static i16 tail;
    static msg queue[QUEUE_SIZE];
};

#endif