# user.py
#
# Copyright 2023 mirkobrombin
# Copyright 2023 muqtadir
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
import subprocess
import shutil
from gi.repository import Gtk, Adw


@Gtk.Template(resource_path="/org/vanillaos/FirstSetup/gtk/default-user.ui")
class VanillaDefaultUser(Adw.Bin):
    __gtype_name__ = "VanillaDefaultUser"

    btn_next = Gtk.Template.Child()
    fullname_entry = Gtk.Template.Child()
    username_entry = Gtk.Template.Child()

    fullname = ""
    fullname_filled = False
    username = ""
    username_filled = False

    existing_users = []

    def __init__(self, window, distro_info, key, step, **kwargs):
        super().__init__(**kwargs)
        self.__window = window
        self.__distro_info = distro_info
        self.__key = key
        self.__step = step
        self.__verify_continue()

        # signals
        self.btn_next.connect("clicked", self.__on_btn_next_clicked)
        self.fullname_entry.connect("changed", self.__on_fullname_entry_changed)
        self.username_entry.connect("changed", self.__on_username_entry_changed)

        # some useful variables
        self.automatic_username = ""
        self.username_just_changed = False

        # get existing users
        self.existing_users = subprocess.Popen("getent passwd | cut -d: -f1", shell=True,
                                          stdout=subprocess.PIPE).stdout.read().decode().splitlines()

    @property
    def step_id(self):
        return self.__key

    def __on_btn_next_clicked(self, widget):
        self.__window.set_user(self.username)
        self.__window.next()

    def get_finals(self):
        return {
            "vars": {"createUser": True},
            "funcs": [
                {
                    "if": "createUser",
                    "type": "command",
                    "commands": [
                        f'adduser --quiet --disabled-password --shell /bin/bash --gecos "{self.fullname}" {self.username}',
                        f'passwd --delete --expire "{self.username}"',
                        f"usermod -a -G sudo,adm,lpadmin {self.username}",
                    ]
                }
            ],
        }

    def __on_fullname_entry_changed(self, *args):
        _fullname = self.fullname_entry.get_text()

        if len(_fullname) > 32:
            self.fullname_entry.set_text(_fullname[:32])
            self.fullname_entry.set_position(-1)
            _fullname = self.fullname_entry.get_text()

        self.__generate_username_from_fullname()

        self.fullname_filled = True
        self.__verify_continue()
        self.fullname = _fullname

    def __on_username_entry_changed(self, *args):
        _input = self.username_entry.get_text()
        _status = True

        # cannot be longer than 32 characters
        if len(_input) > 32:
            self.username_entry.set_text(_input[:32])
            self.username_entry.set_position(-1)
            _input = self.username_entry.get_text()

        # cannot contain special characters
        if re.search(r"[^a-z0-9_-]", _input):
            _status = False
            self.__window.toast(
                "Username cannot contain special characters or uppercase letters. Please choose another username."
            )

        # cannot be empty
        elif not _input:
            _status = False
            if self.username_just_changed:
                self.username_just_changed = False
                return
            self.__window.toast("Username cannot be empty. Please type a username.")

        # cannot be root
        elif _input == "root":
            _status = False
            self.__window.toast(
                "root user is reserved. Please choose another username."
            )

        # cannot be vanilla
        elif _input == "vanilla":
            _status = False
            self.__window.toast(
                "The username 'vanilla' is reserved. Please choose another username."
            )
        
        # cannot already exist
        elif _input in self.existing_users:
            _status = False
            self.__window.toast(
                "The username '" + _input + "' is reserved. Please choose another username."
            )

        if not _status:
            self.username_entry.add_css_class("error")
            self.username_filled = False
            self.__verify_continue()
        else:
            self.username_entry.remove_css_class("error")
            self.username_filled = True
            self.__verify_continue()
            self.username = _input

    def __generate_username_from_fullname(self):
        if self.username_entry.get_text() != '' and self.username_entry.get_text() != self.automatic_username:
            return

        username = self.fullname_entry.get_text()

        if re.findall('[^ ]+', username) == []: # i.e. just spaces and nothing else (causes the app to crash)
            return

        username = re.sub(r' ', '_', username)
        username = re.sub(r'\W+', '', username)
        username = username.lower()

        current_position = 0
        while '_' in username:
            underscore_position = username.find('_')
            username = username[:(current_position + 1)] + username[(underscore_position + 1):]
            current_position += 1

        self.username_just_changed = True
        self.automatic_username = username
        self.username_entry.set_text(username)

    def __verify_continue(self):
        self.btn_next.set_sensitive(
            self.fullname_filled and self.username_filled
        )
