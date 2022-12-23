import sys
from multiprocessing import Process

import gi

from plaid.manager import PlaidManager

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject


class PlaidApp(Gtk.Application):
    process: Process
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = PlaidManager()
        self.connect('activate', self.app_start)
        image = Gtk.Image.new_from_file("./plaid.png")
        image.set_pixel_size(24)
        self.tray_icon = Gtk.StatusIcon.new_from_pixbuf(image.get_pixbuf())
        self.tray_icon.set_tooltip_text("Plaid")
        self.tray_icon.connect("activate", self.close_app)
        self.process = Process(target=self.manager.RenderForever)

    def close_app(self, data=None):
        try:
            self.process.terminate()
        finally:
            Gtk.main_quit()
            sys.exit(0)

    def app_start(self, app):
        self.process.start()


if __name__ == '__main__':
    GObject.threads_init()
    app = PlaidApp(application_id="net.boundcorp.Plaid")
    app.run(sys.argv)
    Gtk.main()
