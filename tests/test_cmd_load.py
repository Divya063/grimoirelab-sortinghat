#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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

import datetime
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.cmd.load import Load
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT

LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR = "Error: invalid json format. Expecting ',' delimiter: line 85 column 17 (char 2800)"
LOAD_IDENTITIES_MISSING_KEYS_ERROR = "Error: Attribute uuid not found"
LOAD_IDENTITIES_MATCHING_ERROR = "Error: mock identity matcher is not supported"
LOAD_ORGS_INVALID_FORMAT_ERROR = "Error: invalid json format. Expecting object: line 36 column 2 (char 811)"
LOAD_ORGS_MISSING_KEYS_ERROR = "Error: invalid json format. Attribute is_top not found"
LOAD_ORGS_IS_TOP_ERROR = "Error: invalid json format. 'is_top' must have a bool value"


# Identities outputs

LOAD_IDENTITIES_OUTPUT = """Loading unique identities...
+ 03e12d00e37fd45593c49a5a5a1652deca4cf302 (old 03e12d00e37fd45593c49a5a5a1652deca4cf302) loaded
+ 52e0aa0a14826627e633fd15332988686b730ab3 (old 52e0aa0a14826627e633fd15332988686b730ab3) loaded
2/3 unique identities loaded"""

LOAD_IDENTITIES_OUTPUT_ERROR = """Error: not enough info to load 0000000000000000000000000000000000000000 unique identity. Skipping."""

# Organization outputs

LOAD_SH_ORGS_OUTPUT = """Domain api.bitergia.com added to organization Bitergia
Domain bitergia.com added to organization Bitergia
Domain bitergia.net added to organization Bitergia
Domain test.bitergia.com added to organization Bitergia
Domain example.net added to organization Bitergia
Domain example.com added to organization Example"""

LOAD_ORGS_OVERWRITE_OUTPUT = """Domain api.bitergia.com added to organization Bitergia
Domain bitergia.com added to organization Bitergia
Domain bitergia.net added to organization Bitergia
Domain test.bitergia.com added to organization Bitergia
Domain example.net added to organization Bitergia
Domain example.com added to organization Example
Domain example.net added to organization Example"""

LOAD_ORGS_OUTPUT_WARNING = """Warning: example.net (Bitergia) already exists in the registry. Not updated."""


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on show unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' : DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Load(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def read_json(self, filename):
        import json

        with open(filename, 'r') as f:
            content = f.read().decode('UTF-8')
            obj = json.loads(content)
        return obj


class TestLoadCommand(TestBaseCase):
    """Load command unit tests"""

    def test_load_identities(self):
        """Test to load identities from a file"""

        self.cmd.run('--identities', 'data/sortinghat_valid.json')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT_ERROR)

    def test_load_identities_with_default_matching(self):
        """Test to load identities from a file using default matching"""

        self.cmd.run('--identities', '--matching', 'default',
                     'data/sortinghat_valid.json')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT_ERROR)

    def test_load_identities_invalid_file(self):
        """Test whether it prints error messages while reading invalid files"""

        self.cmd.run('--identities', 'data/sortinghat_invalid.json')
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR)

    def test_load_organizations(self):
        """Test to load organizations from a file"""

        self.cmd.run('--orgs', 'data/sortinghat_orgs_valid.json')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_SH_ORGS_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_ORGS_OUTPUT_WARNING)

    def test_load_organizations_overwrite(self):
        """Test to load organizations from a file with overwrite parameter set"""

        self.cmd.run('--orgs', '--overwrite',
                     'data/sortinghat_orgs_valid.json')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_ORGS_OVERWRITE_OUTPUT)

    def test_load_organizations_invalid_file(self):
        """Test whether it prints error messages while reading invalid files"""

        self.cmd.run('--orgs', 'data/sortinghat_orgs_invalid_json.json')
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_ORGS_INVALID_FORMAT_ERROR)


class TestLoadIdentities(TestBaseCase):
    """Test import_identities method with some Sorting Hat inputs"""

    def test_valid_identities_file(self):
        """Check insertion of valid data from a file"""

        f = open('data/sortinghat_valid.json')

        self.cmd.import_identities(f)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        ids = uid.identities
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

        # Jane Roe
        uid = uids[1]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        ids = uid.identities
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, 'cbfb7bd31d556322c640f5bc7b31d58a12b15904')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jroe@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, 'fef873c50a48cfc057f7aa19f423f81889a8907f')
        self.assertEqual(id2.name, None)
        self.assertEqual(id2.email, 'jroe@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 3)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.start, datetime.datetime(1999, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2000, 1, 1, 0, 0))

        rol1 = enrollments[1]
        self.assertEqual(rol1.organization.name, 'Bitergia')
        self.assertEqual(rol1.start, datetime.datetime(2006, 1, 1, 0, 0))
        self.assertEqual(rol1.end, datetime.datetime(2008, 1, 1, 0, 0))

        rol2 = enrollments[2]
        self.assertEqual(rol2.organization.name, 'Example')
        self.assertEqual(rol2.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, 0, 0))

    def test_valid_identities_with_default_matching(self):
        """Check insertion, matching and merging of valid data"""

        # First, insert the identity that will match with one
        # from the file
        api.add_organization(self.db, 'Example')
        uuid = api.add_identity(self.db, 'unknown', email='jsmith@example.com')
        api.add_enrollment(self.db, uuid, 'Example',
                           datetime.datetime(2000, 1, 1, 0, 0),
                           datetime.datetime(2100, 1, 1, 0, 0))

        f = open('data/sortinghat_valid.json', 'r')
        self.cmd.import_identities(f, matching='default')

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')

        ids = uid.identities
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, 'jsmith@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

        # Enrollments were merged
        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(2000, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

        # Jane Roe
        uid = uids[1]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        ids = uid.identities
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, 'cbfb7bd31d556322c640f5bc7b31d58a12b15904')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jroe@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, 'fef873c50a48cfc057f7aa19f423f81889a8907f')
        self.assertEqual(id2.name, None)
        self.assertEqual(id2.email, 'jroe@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 3)

    def test_valid_identities_already_exist(self):
        """Check method when an identity already exists but with distinc UUID"""

        # The identity already exists but with a different UUID
        uuid = api.add_identity(self.db, 'unknown', email='jsmith@example.com')
        api.add_identity(self.db, source='scm', email='jsmith@example.com',
                         name='John Smith', username='jsmith', uuid=uuid)

        f = open('data/sortinghat_valid.json', 'r')
        self.cmd.import_identities(f)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')

        ids = uid.identities
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, 'jsmith@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

    def test_dates_out_of_bounds(self):
        """Check dates when they are out of bounds"""

        f = open('data/sortinghat_ids_dates_out_of_bounds.json', 'r')
        self.cmd.import_identities(f)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 1)

        # Jane Roe
        uid = uids[0]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 2)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.start, datetime.datetime(1999, 1, 1, 0, 0))
        # The json file has 2200-01-01T00:00:00
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

        rol1 = enrollments[1]
        self.assertEqual(rol1.organization.name, 'Example')
        # The json file has 1800-01-01T00:00:00
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1, 0, 0))

    def test_not_valid_file(self):
        """Check whether it prints an error when parsing invalid files"""

        f = open('data/sortinghat_invalid.json', 'r')
        self.cmd.import_identities(f)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR)
        f.close()

        f = open('data/sortinghat_ids_missing_keys.json', 'r')
        self.cmd.import_identities(f)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR)
        f.close()

    def test_invalid_matching_method(self):
        """Check if it fails when an invalid matching method is given"""

        f = open('data/sortinghat_valid.json', 'r')

        self.cmd.import_identities(f, matching='mock')

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_MATCHING_ERROR)

        f.close()

    def test_invalid_file(self):
        """Check if it raises a RuntimeError when an invalid file object is given"""

        self.assertRaises(RuntimeError, self.cmd.import_identities, None)
        self.assertRaises(RuntimeError, self.cmd.import_identities, 1)


class TestLoadSortingHatImportOrganizations(TestBaseCase):
    """Test import_organizations method with some Sorting Hat inputs"""

    def test_valid_organizations_file(self):
        """Check insertion of valid data from a file"""

        f = open('data/sortinghat_orgs_valid.json', 'r')

        self.cmd.import_organizations(f)

        # Check the contents of the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        # Bitergia
        org = orgs[0]
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 5)

        dom = doms[0]
        self.assertEqual(dom.domain, 'api.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[1]
        self.assertEqual(dom.domain, 'bitergia.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[2]
        self.assertEqual(dom.domain, 'bitergia.net')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[3]
        self.assertEqual(dom.domain, 'test.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[4]
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, False)

        # Example
        org = orgs[1]
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 1)

        dom = doms[0]
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, True)

        # Unknown
        org = orgs[2]
        self.assertEqual(org.name, 'Unknown')

        doms = org.domains
        self.assertEqual(len(doms), 0)

    def test_import_to_non_empty_registry(self):
        """Test load (and overwrite) process in a registry with some contents"""

        # First, load some data
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.net')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        # Import new data, overwriting existing relationships
        f = open('data/sortinghat_orgs_valid_alt.json', 'r')

        self.cmd.import_organizations(f, True)

        # Check the contents of the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 4)

        # Bitergia
        org = orgs[0]
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 4)

        dom = doms[0]
        self.assertEqual(dom.domain, 'bitergia.net')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[1]
        self.assertEqual(dom.domain, 'bitergia.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[2]
        self.assertEqual(dom.domain, 'api.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[3]
        self.assertEqual(dom.domain, 'test.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        # Example
        org = orgs[1]
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 1)

        dom = doms[0]
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, True)

        # GSyC/LibreSoft
        org = orgs[2]
        self.assertEqual(org.name, 'GSyC/LibreSoft')

        doms = org.domains
        self.assertEqual(len(doms), 2)

        dom = doms[0]
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[1]
        self.assertEqual(dom.domain, 'libresoft.es')
        self.assertEqual(dom.is_top_domain, True)

        # Unknown
        org = orgs[3]
        self.assertEqual(org.name, 'Unknown')

        doms = org.domains
        self.assertEqual(len(doms), 0)

    def test_not_valid_organizations_file(self):
        """Check whether it prints an error when parsing invalid files"""

        f1 = open('data/sortinghat_orgs_invalid_json.json', 'r')
        self.cmd.import_organizations(f1)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_ORGS_INVALID_FORMAT_ERROR)
        f1.close()

        f2 = open('data/sortinghat_orgs_missing_keys.json', 'r')
        self.cmd.import_organizations(f2)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, LOAD_ORGS_MISSING_KEYS_ERROR)
        f2.close()

        f3 = open('data/sortinghat_orgs_invalid_top.json', 'r')
        self.cmd.import_organizations(f3)
        output = sys.stderr.getvalue().strip().split('\n')[2]
        self.assertEqual(output, LOAD_ORGS_IS_TOP_ERROR)
        f3.close()


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
