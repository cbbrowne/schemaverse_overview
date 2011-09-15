#!/bin/env python
import collections
import curses
import psycopg2
import os
import time
import datetime
import sys

from curses import wrapper

HOST="db.schemaverse.com"
USERNAME=""
PASSWORD=""
DATABASE="schemaverse"


class Window(object):
    def __init__(self, app):
        self.app = app
        self.cursor = self.app.db.cursor()
        self.window = None

    def init_window(self):
        pass

    def update(self):
        pass

    def draw(self):
        pass

ShipTuple = collections.namedtuple("Ship", ['id', 'name', 'fleet', 'current_fuel', 'max_fuel', 'current_health', 'max_health'])
class ShipsWindow(Window):
    def init_window(self):
        self.window = curses.newwin(12, 80, 0, 36)
        self.window.border()

    def draw(self):
        self.window.addstr(0, 4, "Ships")

    def update(self):
        self.cursor.execute("SELECT id, name, fleet_id, current_fuel, max_fuel, current_health, max_health FROM my_ships;")

        results = []

        for result in self.cursor.fetchall():
            results.append(ShipTuple(*result))

        self.data = results

    def draw(self):
        header = "%s | %s | %s | %s | %s" % ("ID".center(5), "Name".center(15), "Fleet".center(20), "Fuel".center(12), "Health".center(12))
        sep = "%s-+-%s-+-%s-+-%s-+-%s" % ("-"*5, "-"*15, "-"*20, "-"*12, "-"*12)

        self.window.addstr(0, 4, "Ships")
        self.window.addstr(1, 2, header)
        self.window.addstr(2, 2, sep)

        for line in xrange(0, len(self.data)):
            row = self.data[line]
            row_string = "%s | %s | %s | %s | %s" % (str(row.id).ljust(5),
                                                     row.name.ljust(15),
                                                     str(row.fleet).ljust(20),
                                                     ("%s/%s" % (row.current_fuel, row.max_fuel)).ljust(12),
                                                     ("%s/%s" % (row.current_health, row.max_health)).ljust(12))
            self.window.addstr(3+line, 2, row_string)

InfoTuple = collections.namedtuple("Info", ['user', 'money', 'fuel', 'last_update'])
class InfoWindow(Window):
    def init_window(self):
        self.window = curses.newwin(6, 35, 0, 0)
        self.window.border()

    def update(self):
        self.cursor.execute("SELECT username, balance, fuel_reserve FROM my_player;")
        self.data = InfoTuple(*self.cursor.fetchone(), last_update = datetime.datetime.now())

    def draw(self):
        self.window.addstr(0, 4, "General Info")

        self.window.addstr(1, 2, "User: %s" % self.data.user)
        self.window.addstr(2, 2, "Money: %.2f" % self.data.money)
        self.window.addstr(3, 2, "Fuel: %u" % self.data.fuel)
        self.window.addstr(4, 2, "Last Updated: %s" % self.data.last_update.strftime("%H:%M:%S"))

class Application(object):
    _load_modules = ['Info', 'Ships']
    def __init__(self, screen):
        self.screen = screen
        self.db = None
        self.modules = []

    def connect(self):
        self.db = psycopg2.connect(database=DATABASE, user=USERNAME, password=PASSWORD, host=HOST)

    def init_modules(self):
        for module in self._load_modules:
            window = globals()["%sWindow" % module](self)
            window.init_window()

            self.modules.append(window)

    def update(self):
        for module in self.modules:
            module.update()

    def draw(self):
        for module in self.modules:
            module.draw()
            module.window.refresh()

    def run(self):
        while True:
            self.update()
            self.draw()

            time.sleep(2.5)

def main(screen):
    app = Application(screen)
    app.connect()
    app.init_modules()
    app.run()

if __name__ == '__main__':
    wrapper(main)
