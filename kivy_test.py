from kivy.app import App
import threading
from classes import Serverlib
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen,ScreenManager
from kivy.lang import Builder
sm = ScreenManager()


class MainScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass




class test_app(App):
    def build(self):
        Builder.load_file("test_.kv")
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm


class SettingsGrid(Widget):
    screen_manager = sm
    ads_active = False
    malware_active = False


class FL(FloatLayout):
    proxy_server = Serverlib.Server()
    server_active = False

    @staticmethod
    def enable_proxy():
        print('Starting Proxy')
        print(SettingsGrid.ads_active)
        print(SettingsGrid.malware_active)
        FL.proxy_server = \
            Serverlib.Server(logging=False, ad_filtering=SettingsGrid.ads_active,
                             malware_block=SettingsGrid.malware_active)

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

    def on_touch_up(self, touch):
        if 318 < touch.pos[0] < 680 and 150 < touch.pos[1] < 270:
            if not FL.server_active:
                FL.enable_proxy()
            else:
                FL.close_proxy()
        if 710 < touch.pos[0] < 800 and 540 < touch.pos[1] < 600:
            sm.transition.direction="left"
            sm.current = "settings"


if __name__ == "__main__":
    test_app().run()

