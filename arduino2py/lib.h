#ifndef __LIB_H__
#define __LIB_H__

#include <string>
using namespace std;

void init(const string& device);

void reset();

void sclose();

void send(const string& str);

bool empty();

string receive();

#endif