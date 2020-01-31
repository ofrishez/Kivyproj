from classes import Serverlib
import threading
import time
import atexit
import sys


def main():
    ads = input("ads?[y/n]\n")
    if ads == "y":
        ads = True
    else:
        ads = False
    malware = input("malwares?[y/n]\n")
    if malware == "y":
        malware = True
    else:
        malware = False
    proxy_server = Serverlib.Server(logging=True, malware_block=malware, ad_filtering=ads)
    threading.Thread(target=proxy_server.start_server, daemon=True).start()
    proxy_server.config_proxy_windows()
    while 1:
        x= input()
        if x=="close":
            proxy_server.shutdown()
        if x == "quit":
            proxy_server.shutdown()
            sys.exit(1)

#    atexit.register(proxy_server.shutdown)
#    time.sleep(15)
#    proxy_server.shutdown()


if __name__ == "__main__":
    # Call the main handler function
    main()