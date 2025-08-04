#ifndef __LIB_H__
#define __LIB_H__

#include <string>

bool init(const std::string& device);

void reset();

void sclose();

void send(const std::string& str);

bool my_empty();

std::string receive();

bool open_and_config_serial();

bool check_device();

#endif