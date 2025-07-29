import os
import sys
import time
import subprocess
import logging

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 配置日志，放在脚本同目录下
logging.basicConfig(
    filename=os.path.join(BASE_DIR, "py_daemon.log"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# 目标Python脚本的路径（与本文件同目录）
PYTHON_PATH = sys.executable  # 当前python环境
SCRIPT_PATH = os.path.join(BASE_DIR, "serv.py")  # 目标脚本


def daemonize():
    """
    将当前进程变为守护进程
    """
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # 父进程退出

        os.setsid()  # 创建一个新会话，脱离控制终端

        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # 第一个子进程退出

        # 设置当前工作目录为脚本所在目录，避免路径问题
        os.chdir(BASE_DIR)

        # 重设文件权限掩码
        os.umask(0)

        # 关闭文件描述符
        sys.stdout.flush()
        sys.stderr.flush()
        with open(os.devnull, "wb") as devnull:
            sys.stdout = devnull
            sys.stderr = devnull
            sys.stdin = devnull

    except OSError as e:
        logging.error(f"Fork error: {e}")
        sys.exit(1)


def start_python_script():
    """
    启动目标Python脚本
    """
    try:
        process = subprocess.Popen([PYTHON_PATH, SCRIPT_PATH])
        return process
    except Exception as e:
        logging.error(f"Failed to start the Python script: {e}")
        return None


def main():
    daemonize()
    # 新增：日志记录守护进程自身PID
    logging.info(f"Daemon process started. PID: {os.getpid()}")

    while True:
        logging.info("Starting Python script...")
        process = start_python_script()

        if process:
            logging.info(f"Python script started with PID {process.pid}")

            # 等待子进程退出
            process.wait()

            # 检查脚本是正常退出还是被信号中断
            if process.returncode == 0:
                logging.info("Python script exited normally.")
            else:
                logging.warning(
                    f"Python script exited with code {process.returncode}. Restarting..."
                )

        else:
            logging.error("Failed to start the Python script. Retrying...")

        # 如果脚本退出，休眠一段时间后再启动
        time.sleep(2)


if __name__ == "__main__":
    main()
