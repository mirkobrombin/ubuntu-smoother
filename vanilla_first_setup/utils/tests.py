# tests.py
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

import os
import json


class Tests:

    def __init__(self):
        self.__selected_tests = [""]
        self.__tests = {}
        self.__tests_path = "/usr/share/org.vanillaos.FirstSetup/tests.json"
        self.__selected_tests_path = "/home/$REAL_USER/.local/share/selected_tests.json"
        self.__selected_tests_path = "/home/{}/.local/share/selected_tests.json".format(os.getenv("REAL_USER"))

    def add_test(self, test):
        self.__selected_tests.append(test)

    def test(self):
        for i, v in self.__tests["current"]:
            if i in self.__selected_tests:
                for j in v:
                    if not os.path.isfile(j):
                        return False
        return True

    def load(self):
        with open(self.__tests_path, 'r') as f:
            self.__tests = json.load(f)
        with open(self.__selected_tests_path, 'r') as f:
            self.__selected_tests = json.load(f)

    def write(self):
        with open(self.__selected_tests_path, 'w') as f:
            json.dump(self.__selected_tests, f)

    def remove(self):
        os.remove(self.__selected_tests_path)
