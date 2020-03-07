import os
import socket
import threading
import select
import platform
import re
from string import ascii_lowercase

files_dir = os.path.dirname(os.path.realpath(__file__))


class Server:
    def __init__(self, logging=True, ad_filtering=False, malware_block=False, porn_block=False):
        """
        Class constructor , creating a server socket the method has optional variables for logging and ad filtering
        """
        self.blocks = []
        self.logging = logging  # login mode depends on input
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket creation
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # socket can be reused
        self.client_list = []
        self.database = {}
        if ad_filtering:
            self.blocks.append("ads")
            self.blocked_ads = 0
        if malware_block:
            self.blocks.append("malware")
        if porn_block:
            self.blocks.append("porn")
        self.port = 8080
        self.__start_database()

    def shutdown(self):
        """
        shuts the server down , deleting all clients from client list
        """
        if platform.system() == "Windows":
            self.config_proxy_windows(set_active=False)
        for client in self.client_list:
            try:
                client.close()
            except:
                del client
        self.server_socket.close()
        print('server closed successfully')

    def start_server(self, port=8080, ip="0.0.0.0"):
        """
        starting the server socket , listening to connections and calls a method to handle a connection
        default ip is except everyone and default port 8080
        """
        if port != 8080:
            self.port = port
        port = self.port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket = self.server_socket

        server_socket.bind((ip, port))  # binding server socket
        server_socket.listen(10)  # listening for new connections
        print("Listening for connections on port %d\n" % port)
        while True:
            try:
                client_socket, client_address = server_socket.accept()  # accept new connection
                self.client_list.append(client_socket)
                index = len(self.client_list) - 1  # index of new socket in client list
                if self.logging:
                    print('New connection received with ip address - ' + client_address[0] + '\n')
                threading.Thread(name="client- " + client_address[0], target=self.__connection_handler,
                                 args=(index,), daemon=True).start()  # start a thread to handle new connection
            except:
                print('server socket closed')
                break

    def __connection_handler(self, index):
        """
        private method to manage a connection
        """
        try:
            client_socket = self.client_list[index]
            while True:
                client_request = client_socket.recv(1024)  # request from client
                if len(client_request.decode()) > 1:
                    self.__request_handler(client_request.decode(), client_socket)
                else:
                    return
        except:
            if self.logging:
                print("connection %s was terminated" % threading.current_thread().name)
            try:
                del self.client_list[index]
            except:
                pass
            return

    def __request_handler(self, request, client_socket):
        """
        takes a request from client and it's socket object and fills it
        """
        url = request.split('\n')[0].split(' ')  # get url
        print(" ".join(url)) if self.logging else None
        if url[0] == 'CONNECT':  # CONNECT http method
            self.__connect_request(url, client_socket)  # handles CONNECT method
            return

        if url[0] == "GET" or url[0] == 'HEAD' or url[0] == 'POST':
            webserver, port, link = parse_url(url)
        else:
            print("request type not supported")
            return

        # creating client socket with web
        result = self.__send_request(webserver, port, request.encode(), link)
        s = result if result is not False else False
        if not s: return

        session_sockets = [client_socket, s]
        while 1:
            # receive data from web server
            try:
                while True:
                    (read, [], []) = select.select(session_sockets, [], [])
                    if read:  # a client has data to send
                        data_from_client = ''
                        data_from_server = ''
                        for user in read:
                            data_from_client = user.recv(2048) if user is client_socket else ''
                            data_from_server = user.recv(2048) if data_from_client is '' else ''
                        if data_from_client != '':
                            decoded_data = data_from_client.decode()
                            url = decoded_data.split('\n')[0].split(' ')  # get url
                            if url[0] == "GET" or url[0] == 'HEAD' or url[0] == 'POST':
                                webserver, port, link = parse_url(url)
                                if "ads" in self.blocks and \
                                        (self.is_ad_request(webserver) or self.is_ad_request_wildcards(link)):
                                    pass
                                else:
                                    if "malware" in self.blocks is True and self.is_malware(webserver):
                                        pass
                                    else:
                                        if 'porn' in self.blocks and self.is_porn(webserver):
                                            pass
                                        else:
                                            s.send(data_from_client)
                        if data_from_server != '':
                            client_socket.send(data_from_server)

            except TimeoutError:
                print('timeout error with server- ' + webserver)
                break

    def __connect_request(self, url, client_socket):
        """
        private method to handle CONNECT http request , this request is sent to a proxy server by the client to request
        a secure connection between it and the requested webserver via the proxy
        """
        if ':' in url[1]:
            host = url[1].split(':')
            webserver = host[0]
            port = host[1]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            port = int(port)
            if "ads" in self.blocks and self.is_ad_request(webserver):
                return False
            if "malware" in self.blocks is True and self.is_malware(webserver):
                return False
            if 'porn' in self.blocks and self.is_porn(webserver):
                return False
            if self.logging:
                print("connecting " + webserver + " through port " + str(port) + "\n")
            try:
                s.connect((webserver, port))
            except:
                print('connection error')
                return
            client_socket.send(b'HTTP/1.1 200 Connection established\nServer: Python-Proxy\nConnection: close\n\n')
            if self.logging:
                print('connection tunnel between client and ' + webserver + ' was created successfully \n')
            session_sockets = [client_socket, s]
            while True:
                (recv, [], []) = select.select(session_sockets, [], [])
                if recv:
                    data_from_client = ''
                    data_from_server = ''
                    for user in recv:
                        if user is client_socket:
                            data_from_client = user.recv(2048)
                        else:
                            data_from_server = user.recv(2048)
                    if data_from_client != '':
                        s.send(data_from_client)
                    if data_from_server != '':
                        client_socket.send(data_from_server)

    def __send_request(self, server, port, request , link):
        """private method that takes a server , port and request
        connects the requested server at given port and sends it the given request , blocks the request if needed"""
        #        print(server + "\n" + str(port) + "\n" + request + "\n")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        port = int(port)
        if "ads" in self.blocks and \
                (self.is_ad_request(server) or self.is_ad_request_wildcards(link)):
            return False
        if "malware" in self.blocks is True and self.is_malware(server):
            return False
        if 'porn' in self.blocks and self.is_porn(server):
            return False
        print("connecting " + server + " through port " + str(port))
        try:
            s.connect((server, port))
        except:
            print("failed to connect to server")
            return False
        s.sendall(request)
        return s

    def config_proxy_windows(self, ip_addr="127.0.0.1", set_active=True):
        """
        setting up proxy settings for windows , to automate application use
        ip_address could be given to configure a proxy connection on other ip than current pc ip address
        set_active - true to set proxy on , false to turn proxy off default is turn on
        """

        if not platform.system() == "Windows":
            print("This function is supported for Windows system")
        try:
            import winreg
        except ImportError:
            'Windows registry could not be imported'
            return
        key = winreg.OpenKeyEx \
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0,
             winreg.KEY_WRITE)
        if set_active:
            try:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, ip_addr + ":" + str(self.port))
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                print("proxy is active\n")
            except:
                print("Failed to setup proxy\n")
                return
        else:
            try:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                print("proxy inactive\n")
            except:
                return

    def __start_database(self):
        """
        private method that takes data from domains files and fills the server`s database by it's rules
        in order to make the process efficient as possible.
        """

        if "ads" in self.blocks:
            try:
                ad_domains_file = open(files_dir + r"\Ad_domains.txt", 'r')
            except:
                print("cant open ads file ")
                return
            hosts, keywords = ad_domains_file.read().split('#adkeywords:#')

            self.database["ads"] = {c: set() for c in ascii_lowercase + "".join([str(i) for i in range(0, 10, 1)])}
            self.database["ads"]["keywords"] = [word for word in keywords.split("\n") if word != ""]
            data = hosts.split("\n")
            for line in data:
                if line != "":
                    try:
                        self.database["ads"][line[0].lower()].add(line)
                    except KeyError:
                        self.database["ads"][line[0].lower()] = set()
                        self.database["ads"][line[0].lower()].add(line)
            ad_domains_file.close()
        if "malware" in self.blocks:
            try:
                malware_domains_file = open(files_dir + r"\Ad_domains.txt", 'r')
            except:
                print("cant open malwares file ")
                return
            self.database["malwares"] = {c: set() for c in ascii_lowercase + "".join([str(i) for i in range(0, 10, 1)])}
            data = malware_domains_file.read().split("\n")
            for line in data:
                if line != "":
                    try:
                        self.database["malwares"][line[0].lower()].add(line)
                    except KeyError:
                        self.database["malwares"][line[0].lower()] = set()
                        self.database["malwares"][line[0].lower()].add(line)
            malware_domains_file.close()
            if "porn" in self.blocks:
                try:
                    porn_domains_file = open(files_dir + r"\Porn_domains.txt", 'r')
                except:
                    print("cant open porn domains file ")
                    return
                self.database["porn"] = {c: set() for c in
                                         ascii_lowercase + "".join([str(i) for i in range(0, 10, 1)])}
                data = porn_domains_file.read().split("\n")
                for line in data:
                    if line != "":
                        try:
                            self.database["porn"][line[0].lower()].add(line)
                        except KeyError:
                            self.database["porn"][line[0].lower()] = set()
                            self.database["porn"][line[0].lower()].add(line)
                porn_domains_file.close()

    def is_ad_request(self, domain):
        """
        checks if the request is a request for advertisement returns true if so , false otherwise
        """
        if domain in self.database['ads'][domain[0].lower()]:
            if self.logging:
                print("ad request detected and blocked -" + domain)
                self.blocked_ads += 1
            return True
        for keyword in self.database['ads']['keywords']:
            if re.search(keyword, domain):
                if self.logging:
                    print("ad request detected and blocked -" + domain)
                self.blocked_ads += 1
                return True
        return False

    def is_ad_request_wildcards(self,link):
        for keyword in self.database['ads']['keywords']:
            if re.search(keyword, link):
                if self.logging:
                    print("ad request detected and blocked -" + link)
                return True
        return False

    def is_malware(self, domain):
        """
        checks if the request is a request for malware or suspicious site returns true if so , false otherwise
        """
        if type(domain) != type(str):
            print("domain should be string type")
            return
        if domain in self.database['malwares'][domain[0].lower]:
            if self.logging:
                print("malware request detected and blocked -" + domain)
            return True
        return False

    def is_porn(self, domain):
        """
        checks if the request is a request for porn or suspicious site returns true if so , false otherwise
        """
        if type(domain) != type(str):
            print("domain should be string type")
            return
        if domain in self.database['porn'][domain[0].lower]:
            if self.logging:
                print("porn request detected and blocked -" + domain)
            return True
        return False

    def get_blocked_ads(self):
        if "ads" in self.blocks:
            return self.blocked_ads
        else:
            return 0


def parse_url(url):
    if url[1].find("://") == -1:  # find position of ://
        link = url[1]
    else:
        link = url[1][(url[1].find("://") + 3):]  # get the rest of url

    port_pos = link.find(":")  # find the port pos (if any)

    # find end of web server
    end_of_webserver = link.find("/")
    if end_of_webserver == -1:  # was not found
        end_of_webserver = len(link)  # position is the length of link

    if port_pos == -1 or end_of_webserver < port_pos:  # no port defined
        # default port
        port = 80
        webserver = link[:end_of_webserver]  # gets only the webserver address ex: www.google.com
    else:  # specific port
        port = int((link[(port_pos + 1):])[:end_of_webserver - port_pos - 1])
        webserver = link[:port_pos]  # excluding the port number from server address
    return webserver, port, link
