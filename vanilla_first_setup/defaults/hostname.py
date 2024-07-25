# hostname.py
#
# Copyright 2023 mirkobrombin
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundationat version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from gi.repository import Gtk, Adw


@Gtk.Template(resource_path="/org/vanillaos/FirstSetup/gtk/default-hostname.ui")
class VanillaDefaultHostname(Adw.Bin):
    __gtype_name__ = "VanillaDefaultHostname"

    btn_next = Gtk.Template.Child()
    hostname_entry = Gtk.Template.Child()

    hostname = ""

    def __init__(self, window, distro_info, key, step, **kwargs):
        super().__init__(**kwargs)
        self.__window = window
        self.__distro_info = distro_info
        self.__key = key
        self.__step = step
        self.__verify_continue()

        # signals
        self.btn_next.connect("clicked", self.__on_btn_next_clicked)
        self.hostname_entry.connect("changed", self.__on_hostname_entry_changed)

    @property
    def step_id(self):
        return self.__key

    def __on_btn_next_clicked(self, widget):
        self.__window.next()

    def get_finals(self):
        return {
            "vars": {"setHostname": True},
            "funcs": [
                {
                    "if": "setHostname",
                    "type": "command",
                    "commands": ["hostnamectl set-hostname " + self.hostname],
                    "tests": []
                }
            ],
        }

    def __on_hostname_entry_changed(self, *args):
        _hostname = self.hostname_entry.get_text()

        if self.__validate_hostname(_hostname):
            self.hostname = _hostname
            self.hostname_entry.remove_css_class("error")
            self.__verify_continue()
            return

        self.__window.toast(
            "Hostname cannot contain special characters. Please choose another hostname."
        )
        self.hostname_entry.add_css_class("error")
        self.hostname = ""
        self.__verify_continue()

    def __validate_hostname(self, hostname):
        if len(hostname) > 50:
            return False

        allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))

    def __verify_continue(self):
        self.btn_next.set_sensitive(self.hostname != "")
