from kivy.app import App
import threading
from classes import Serverlib
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image


class test_app(App):
    def build(self):
        return FL()


class FL(FloatLayout):
    proxy_server = Serverlib.Server(logging=False, ad_filtering=False)
    server_active = False

    @staticmethod
    def enable_proxy():
        print('Starting Proxy')
        threading.Thread(target=FL.proxy_server.start_server).start()
        FL.proxy_server.config_proxy_windows(set_active=True)
        FL.server_active = True

    @staticmethod
    def close_proxy():
        print('Closing Proxy')
        try:
            FL.proxy_server.shutdown()
            FL.server_active = False
        except AttributeError:
            print("proxy server is not active")
            return

    def on_touch_down(self, touch):
        if 318 < touch.pos[0] < 680 and 150 < touch.pos[1] < 270:
            if not FL.server_active:
                FL.enable_proxy()
            else:
                FL.close_proxy()




if __name__ == "__main__":
    test_app().run()

