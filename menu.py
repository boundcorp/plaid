import sys
from threading import Thread

import gi

from main import PlaidManager

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject

thread = None

def message(data=None):
    "Function to display messages to the user."
    msg = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL,
                            Gtk.MessageType.INFO, Gtk.ButtonsType.OK, data)
    msg.run()
    msg.destroy()


def close_app(data=None):
    Gtk.main_quit()
    sys.exit(0)


def make_menu(event_button, event_time, data=None):
    menu = Gtk.Menu()
    start_item = Gtk.MenuItem("Start Plaid")
    close_item = Gtk.MenuItem("Close App")

    # Append the menu items
    menu.append(start_item)
    menu.append(close_item)
    # add callbacks
    start_item.connect_object("activate", start_plaid, None)
    close_item.connect_object("activate", close_app, "Close App")
    # Show the menu items
    start_item.show()
    close_item.show()

    # Popup the menu
    menu.popup(None, None, None, None, event_button, event_time)


def on_right_click(data, event_button, event_time):
    make_menu(event_button, event_time)


def on_left_click(event):
    message("Plaid 0.1")


def start_plaid(data=None):
    manager = PlaidManager()
    Thread(target=manager.Start).start()


if __name__ == '__main__':
    icon = Gtk.StatusIcon()
    icon.connect('popup-menu', on_right_click)
    icon.connect('activate', on_left_click)
    GObject.threads_init()
    Gtk.main()
