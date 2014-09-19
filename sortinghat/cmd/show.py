# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import argparse

from sortinghat import api
from sortinghat.command import Command
from sortinghat.exceptions import NotFoundError


class Show(Command):
    """Show information about unique identities.

    This command prints information related to the unique identities such as
    identities or enrollments. When <uuid> is given, it will only show information
    about the unique identity related to <uuid>.
    """
    def __init__(self, **kwargs):
        super(Show, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Positional arguments
        self.parser.add_argument('uuid', nargs='?', default=None,
                                 help="unique identifier of the identity to show")

    @property
    def description(self):
        return """Show information about a unique identity."""

    @property
    def usage(self):
        return "%(prog)s show [<uuid>]"

    def run(self, *args):
        """Show information about unique identities."""

        params = self.parser.parse_args(args)

        self.show(params.uuid)

    def show(self, uuid=None):
        """Show the information related to unique identities.

        This method prints information related to unique identities such as
        identities or enrollments.
        When <uuid> is given, it will only show information about the unique
        identity related to <uuid>.

        :param uuid: unique identifier
        """
        try:
            uidentities = api.unique_identities(self.db, uuid)

            for uid in uidentities:
                # Add enrollments to a new property 'roles'
                enrollments = api.enrollments(self.db, uid.uuid)
                uid.roles = enrollments

            self.display('show.tmpl', uidentities=uidentities)
        except NotFoundError, e:
            self.error(str(e))