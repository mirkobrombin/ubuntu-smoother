# keyboard.py
#
# Copyright 2023 mirkobrombin
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
import gi

gi.require_version("GnomeDesktop", "4.0")

import contextlib
import os
import re
import subprocess

from gi.repository import Adw, Gio, GLib, Gtk

from vanilla_first_setup.core.keymaps import KeyMaps


@Gtk.Template(resource_path="/org/vanillaos/FirstSetup/gtk/widget-keyboard.ui")
class KeyboardRow(Adw.ActionRow):
    __gtype_name__ = "KeyboardRow"

    select_button = Gtk.Template.Child()
    suffix_bin = Gtk.Template.Child()

    def __init__(
        self, title, subtitle, layout, variant, key, selected_keyboard, toggled_callback, **kwargs
    ):
        super().__init__(**kwargs)
        self.__title = title
        self.__subtitle = subtitle
        self.__layout = layout
        self.__variant = variant
        self.__key = key
        self.__selected_keyboard = selected_keyboard

        self.set_title(title)
        self.set_subtitle(subtitle)
        self.suffix_bin.set_label(key)

        self.select_button.connect("toggled", toggled_callback, self)


@Gtk.Template(resource_path="/org/vanillaos/FirstSetup/gtk/default-keyboard.ui")
class VanillaDefaultKeyboard(Adw.Bin):
    __gtype_name__ = "VanillaDefaultKeyboard"

    btn_next = Gtk.Template.Child()
    entry_test = Gtk.Template.Child()
    entry_search_keyboard = Gtk.Template.Child()
    all_keyboards_group = Gtk.Template.Child()
    selected_keyboard = {"layout": None, "model": "pc105", "variant": None}

    search_controller = Gtk.EventControllerKey.new()
    test_focus_controller = Gtk.EventControllerFocus.new()

    match_regex = re.compile(r"[^a-zA-Z0-9 ]")

    def __init__(self, window, distro_info, key, step, **kwargs):
        super().__init__(**kwargs)
        self.__window = window
        self.__distro_info = distro_info
        self.__key = key
        self.__step = step
        self.__keymaps = KeyMaps()

        self.__keyboard_rows = self.__generate_keyboard_list_widgets(
            self.selected_keyboard
        )
        for i, widget in enumerate(self.__keyboard_rows):
            self.all_keyboards_group.append(widget)

        # controllers
        self.entry_search_keyboard.add_controller(self.search_controller)
        self.entry_test.add_controller(self.test_focus_controller)

        # signals
        self.btn_next.connect("clicked", self.__next)
        self.all_keyboards_group.connect(
            "selected-rows-changed", self.__keyboard_verify
        )
        self.all_keyboards_group.connect("row-selected", self.__keyboard_verify)
        self.all_keyboards_group.connect("row-activated", self.__keyboard_verify)
        self.__window.carousel.connect("page-changed", self.__keyboard_verify)

        self.search_controller.connect("key-released", self.__on_search_key_pressed)
        if "VANILLA_NO_APPLY_XKB" not in os.environ:
            self.test_focus_controller.connect("enter", self.__apply_layout)

    def __keyboard_verify(self, *args):
        if self.selected_keyboard["layout"] is not None:
            self.btn_next.set_sensitive(True)
        else:
            self.btn_next.set_sensitive(False)

    def __next(self, *args):
        self.__window.next()

    def get_finals(self):
        variant = self.selected_keyboard["variant"]

        # NOTE: we use BACKSPACE=guess here by default
        # Ref: <https://manpages.ubuntu.com/manpages/bionic/en/man5/keyboard.5.htmlZ
        if variant is None:
            return {
                "vars": {"confKeyboard": True},
                "funcs": [
                    {
                        "if": "confKeyboard",
                        "type": "command",
                        "commands": [
                            f'echo XKBMODEL="pc105" >> /etc/default/keyboard',
                            f'echo XKBLAYOUT="{self.selected_keyboard["layout"]}" >> /etc/default/keyboard',
                            f'echo BACKSPACE="guess" >> /etc/default/keyboard',
                        ],
                    }
                ],
            }  # fallback
        return {
            "vars": {"confKeyboard": True},
            "funcs": [
                {
                    "if": "confKeyboard",
                    "type": "command",
                    "commands": [
                        f'echo XKBMODEL="pc105" >> /etc/default/keyboard',
                        f'echo XKBLAYOUT="{self.selected_keyboard["layout"]}" >> /etc/default/keyboard',
                        f'echo XKBVARIANT="{self.selected_keyboard["variant"]}" >> /etc/default/keyboard',
                        f'echo BACKSPACE="guess" >> /etc/default/keyboard',
                    ],
                }
            ],
        }

    def __generate_keyboard_list_widgets(self, selected_keyboard):
        keyboard_widgets = []
        current_layout, current_variant = self.__get_current_layout()

        all_keyboard_layouts = {
            value["display_name"]: {
                "key": key,
                "country": country,
                "layout": value["xkb_layout"],
                "variant": value["xkb_variant"],
            }
            for country in self.__keymaps.list_all.keys()
            for key, value in self.__keymaps.list_all[country].items()
        }

        # Changed display_name as this charchter string is causing gtk markup error
        if all_keyboard_layouts.get("Czech (with <\|> key)"):
            all_keyboard_layouts["Czech (bksl)"] = all_keyboard_layouts.pop(
                "Czech (with <\|> key)"
            )

        for keyboard_title, content in all_keyboard_layouts.items():
            keyboard_key = content["key"]
            keyboard_country = content["country"]
            keyboard_layout = content["layout"]
            keyboard_variant = content["variant"]
            keyboard_row = KeyboardRow(
                keyboard_title,
                keyboard_country,
                keyboard_layout,
                keyboard_variant,
                keyboard_key,
                selected_keyboard,
                self.__on_check_button_toggled,
            )

            if len(keyboard_widgets) > 0:
                keyboard_row.select_button.set_group(keyboard_widgets[0].select_button)
            keyboard_widgets.append(keyboard_row)

            # set up current keyboard
            if (
                current_layout == keyboard_layout
                and current_variant == keyboard_variant
            ):
                keyboard_row.select_button.set_active(True)
                self.selected_keyboard["layout"] = current_layout
                self.selected_keyboard["variant"] = current_variant

        return keyboard_widgets

    def __get_current_layout(self):
        res = subprocess.run(
            ["setxkbmap", "-query"], capture_output=True, text=True
        ).stdout.splitlines()

        current_layout = [
            line.split(": ")[1] for line in res if line.startswith("layout")
        ][0]
        current_variant = None

        if "," in current_layout:
            current_layout = current_layout.split(",")[0].strip()

        with contextlib.suppress(IndexError):
            current_variant = [
                line.split(": ")[1] for line in res if line.startswith("variant")
            ][0]
            if "," in current_variant:
                current_variant = current_variant.split(",")[0].strip()

        return current_layout, current_variant

    def __apply_layout(self, *args):
        layout = self.selected_keyboard["layout"]
        variant = self.selected_keyboard["variant"]

        if variant is None:
            return

        # set the layout
        self.__set_keyboard_layout(layout, variant)

    def __on_search_key_pressed(self, *args):
        keywords = self.match_regex.sub(
            "", self.entry_search_keyboard.get_text().lower()
        )

        for row in self.all_keyboards_group:
            row_title = self.match_regex.sub("", row.get_title().lower())
            row_subtitle = self.match_regex.sub("", row.get_subtitle().lower())
            row_label = self.match_regex.sub("", row.suffix_bin.get_label().lower())

            search_text = row_title + " " + row_subtitle + " " + row_label
            row.set_visible(re.search(keywords, search_text, re.IGNORECASE) is not None)

    def __set_keyboard_layout(self, layout, variant=None):
        value = layout

        if variant != "":
            value = layout + "+" + variant

        Gio.Settings.new("org.gnome.desktop.input-sources").set_value(
            "sources",
            GLib.Variant.new_array(
                GLib.VariantType("(ss)"),
                [
                    GLib.Variant.new_tuple(
                        GLib.Variant.new_string("xkb"), GLib.Variant.new_string(value)
                    )
                ],
            ),
        )

    @property
    def step_id(self):
        return self.__key

    def __on_check_button_toggled(self, __radio_button, widget):
        self.selected_keyboard["layout"] = widget._KeyboardRow__layout
        self.selected_keyboard["variant"] = widget._KeyboardRow__variant
        self.btn_next.set_sensitive(True)