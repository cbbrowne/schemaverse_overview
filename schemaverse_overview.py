#!/bin/env python
import collections
import curses
import psycopg2
import os
import time
import datetime
import sys

from curses import wrapper

# Draw data from environment
if os.getenv("PGHOST") == "":
    HOST="db.schemaverse.com"
else:
    HOST=os.getenv("PGHOST")
if os.getenv("PGUSER") == "":
    USERNAME=os.getlogin()
else:
    USERNAME=os.getenv("PGUSER")
if os.getenv("PGPORT") == "":
    PORT="5432"
else:
    PORT=os.getenv("PGPORT")
if os.getenv("PGDATABASE") == "":
    DATABASE="schemaverse"
else:
    DATABASE=os.getenv("PGDATABASE")

class Window(object):
    def __init__(self, app):
        self.app = app
        self.cursor = self.app.db.cursor()
        self.window = None
        self.data = None

    def init_window(self):
        pass

    def update(self):
        pass

    def draw(self):
        pass

EventTuple = collections.namedtuple("Event", ['time', 'event_description'])
class EventWindow(Window):
    def init_window(self):
        self.window = curses.newwin(16, 129, 12, 0)
        self.window.border()

    def draw(self):
        self.window.addstr(0, 4, "Events")

        line = 1
        for row in self.data:
            row_string = "[%s] %s" % (row.time. strftime("%d/%b %H:%M:%S"), row.event_description)

            self.window.addstr(line, 2, row_string)
            line += 1

        self.window.redrawwin()

    def update(self):
        self.cursor.execute("SELECT toc, READ_EVENT(id) FROM my_events WHERE player_id_1 = GET_PLAYER_ID(%s) OR player_id_2 = GET_PLAYER_ID(%s) ORDER BY toc DESC LIMIT 14;", (USERNAME, USERNAME))

        results = []

        for result in self.cursor.fetchall():
            results.append(EventTuple(*result))

        self.data = reversed(results)

ShipTuple = collections.namedtuple("Ship", ['id', 'name', 'fleet', 'current_fuel', 'max_fuel', 'current_health', 'max_health', 'location_x', 'location_y'])
class ShipsWindow(Window):
    def init_window(self):
        self.window = curses.newwin(12, 93, 0, 36)
        self.window.border()

    def update(self):
        self.cursor.execute("SELECT id, name, fleet_id, current_fuel, max_fuel, current_health, max_health, location_x, location_y FROM my_ships LIMIT 8;")

        results = []

        for result in self.cursor.fetchall():
            results.append(ShipTuple(*result))

        self.data = results

    def draw(self):
        header = "%s | %s | %s | %s | %s | %s" % ("ID".center(5), "Name".center(15), "Fleet".center(20), "Fuel".center(12), "Health".center(12), "X/Y".center(10))
        sep = "%s-+-%s-+-%s-+-%s-+-%s-+-%s" % ("-"*5, "-"*15, "-"*20, "-"*12, "-"*12, "-"*10)

        self.window.addstr(0, 4, "Ships")
        self.window.addstr(1, 2, header)
        self.window.addstr(2, 2, sep)

        for line in xrange(0, len(self.data)):
            row = self.data[line]
            row_string = "%s | %s | %s | %s | %s | %s" % (str(row.id).ljust(5),
                                                     row.name.ljust(15),
                                                     str(row.fleet).ljust(20),
                                                     ("%s/%s" % (row.current_fuel, row.max_fuel)).ljust(12),
                                                     ("%s/%s" % (row.current_health, row.max_health)).ljust(12),
                                                     ("%s/%s" % (row.location_x, row.location_y)).ljust(10))
            self.window.addstr(3+line, 2, row_string)

InfoTuple = collections.namedtuple("Info", ['user', 'money', 'fuel', 'last_update'])
class InfoWindow(Window):
    def init_window(self):
        self.window = curses.newwin(12, 35, 0, 0)
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
    _load_modules = ['Info', 'Ships', 'Event']
    def __init__(self, screen):
        self.screen = screen
        self.db = None
        self.modules = []

    def connect(self):
        self.db = psycopg2.connect(database=DATABASE, user=USERNAME, port=PORT, host=HOST)

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
