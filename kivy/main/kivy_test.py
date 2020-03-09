from kivy.app import App
import threading
from classes import Serverlib
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen,ScreenManager
from kivy.properties import ObjectProperty
from kivy.uix.switch import Switch
sm = ScreenManager()
import time


class MainScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class CustomeScreen(Screen):
    pass


class test_app(App):
    def build(self):
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(CustomeScreen(name="custome"))
        return sm


class SettingsGrid(Widget):
    ads = ObjectProperty(None)
    malwares = ObjectProperty(None)
    eighteen = ObjectProperty(None)
    screen_manager = sm
    ads_on = False
    malware_on = False
    eighteen_on = False

    def on_touch_up(self, touch):
        deltax = self.size[0] - touch.pos[0]
        deltay = self.size[1] - touch.pos[1]
        if 0.3*self.size[0] < deltax < 0.70*self.size[0] and 450 < deltay < 570:
            sm.transition.direction = "left"
            sm.current = "custome"
        if 0.85*self.size[0] < deltax < self.size[0] and 0 < deltay < 50:
            SettingsGrid.ads_on = self.ads.active
            SettingsGrid.malware_on = self.malwares.active
            SettingsGrid.eighteen_on = self.eighteen.active
            sm.transition.direction = "right"
            sm.current = "main"


class FL(FloatLayout):
    count = ObjectProperty(None)
    btn = ObjectProperty(None)
    proxy_server = Serverlib.Server()
    server_active = False

    def update_blocked_ads(self):
        while True:
            self.count.text = "Blocked ads: " + str(self.proxy_server.blocked_ads)
            time.sleep(10)

    @staticmethod
    def enable_proxy():
        print('Starting Proxy, ad filtering-' + str(SettingsGrid.ads_on)
              + "  malware block-"+str(SettingsGrid.malware_on) + "  18+-" + str(SettingsGrid.eighteen_on))
        FL.proxy_server = \
            Serverlib.Server(logging=True, ad_filtering=SettingsGrid.ads_on,
                             malware_block=SettingsGrid.malware_on, porn_block=SettingsGrid.eighteen_on, custome=True)

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
        deltax = self.size[0] - touch.pos[0]
        deltay = self.size[1] - touch.pos[1]
        if 0.37*self.size[0] < deltax < 0.5*self.size[0] and 0.5*self.size[1] < deltay < 0.8*self.size[1]:
            if not FL.server_active:
                self.btn.source = "images/pause.png"
                FL.enable_proxy()
                threading.Thread(target=self.update_blocked_ads).start()
            else:
                self.btn.source = "images/play.png"
                FL.close_proxy()

        if 0 < deltax < 50 and 0 < deltay < 50:
            sm.transition.direction="left"
            sm.current = "settings"


class Custome(FloatLayout):
    customebox = ObjectProperty(None)
    lst = []

    def on_touch_up(self, touch):
        deltax = self.size[0] - touch.pos[0]
        deltay = self.size[1] - touch.pos[1]

        if 0.85 * self.size[0] < deltax < self.size[0] and 0 < deltay < 50:
            sm.transition.direction = "right"
            sm.current = "settings"
            txt = self.customebox.text
            if len(txt) > 0:
                if "\n" in txt:
                    self.lst = txt.split("\n")
                else:
                    self.lst.append(txt)
            FL.proxy_server.update_custome_list(self.lst)


if __name__ == "__main__":
    test_app().run()

