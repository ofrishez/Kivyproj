from classes import Serverlib
import threading
import time
import atexit


def main():
    proxy_server = Serverlib.Server(logging=True, malware_block=True, ad_filtering=True)
    threading.Thread(target=proxy_server.start_server).start()
    proxy_server.config_proxy_windows()
#    atexit.register(proxy_server.shutdown)
#    time.sleep(15)
#    proxy_server.shutdown()


if __name__ == "__main__":
    # Call the main handler function
    main()
