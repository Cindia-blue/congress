# Copyright (c) 2014 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo.config import cfg

from congress.exception import DanglingReference
from congress import harness
from congress.managers import datasource as datasource_manager
from congress.tests import base
from congress.tests import fake_datasource
from congress.tests import helper


class TestDataSourceManager(base.SqlTestCase):

    def setUp(self):
        super(TestDataSourceManager, self).setUp()
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])
        self.datasource_mgr = datasource_manager.DataSourceManager
        self.datasource_mgr.validate_configured_drivers()
        self.cage = harness.create(helper.root_path(), helper.state_path())

    def _get_datasource_request(self):
        return {'id': 'asdf',
                'name': 'aaron',
                'driver': '',
                'description': 'hello world!',
                'enabled': True,
                'type': None,
                'config': {}}

    def test_make_datasource_dict(self):
        req = self._get_datasource_request()
        result = self.datasource_mgr.make_datasource_dict(req)
        self.assertEqual(req, result)

    def test_validate_create_datasource_invalid_driver(self):
        req = self._get_datasource_request()
        self.assertRaises(datasource_manager.InvalidDriver,
                          self.datasource_mgr.validate_create_datasource,
                          req)

    def test_validate_create_datasource_invalid_config_invalid_options(self):
        req = self._get_datasource_request()
        req['driver'] = 'invalid_datasource'
        self.assertRaises(datasource_manager.InvalidDriver,
                          self.datasource_mgr.validate_create_datasource,
                          req)

    def test_validate_create_datasource_missing_config_options(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        # This is still missing some required options
        req['config'] = {'auth_url': '1234'}
        self.assertRaises(datasource_manager.MissingRequiredConfigOptions,
                          self.datasource_mgr.validate_create_datasource,
                          req)

    def test_add_datasource(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        req['config'] = {'auth_url': 'foo',
                         'username': 'armax',
                         'password': 'password',
                         'tenant_name': 'armax'}
        # let driver generate this for us.
        del req['id']
        result = self.datasource_mgr.add_datasource(req)
        for key, value in req.iteritems():
            self.assertEqual(value, result[key])
        # TODO(thinrichs): test that ensure the DB, the policy engine,
        #   and the datasource manager are all in sync

    def test_get_datasouce(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        req['config'] = {'auth_url': 'foo',
                         'username': 'armax',
                         'password': 'password',
                         'tenant_name': 'armax'}
        # let driver generate this for us.
        del req['id']
        result = self.datasource_mgr.add_datasource(req)
        result = self.datasource_mgr.get_datasource(result['id'])
        for key, value in req.iteritems():
            self.assertEqual(value, result[key])

    def test_get_datasources(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        req['name'] = 'datasource1'
        req['config'] = {'auth_url': 'foo',
                         'username': 'armax',
                         'password': 'password',
                         'tenant_name': 'armax'}
        # let driver generate this for us.
        del req['id']
        self.datasource_mgr.add_datasource(req)
        req['name'] = 'datasource2'
        self.datasource_mgr.add_datasource(req)
        result = self.datasource_mgr.get_datasources()

        req['name'] = 'datasource1'
        for key, value in req.iteritems():
            self.assertEqual(value, result[0][key])

        req['name'] = 'datasource2'
        for key, value in req.iteritems():
            self.assertEqual(value, result[1][key])

    def test_get_datasources_hide_secret(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        req['name'] = 'datasource1'
        req['config'] = {'auth_url': 'foo',
                         'username': 'armax',
                         'password': 'password',
                         'tenant_name': 'armax'}
        # let driver generate this for us.
        del req['id']
        self.datasource_mgr.add_datasource(req)
        req['name'] = 'datasource2'
        self.datasource_mgr.add_datasource(req)

        # Value will be set as <hidden>
        req['config']['password'] = "<hidden>"
        result = self.datasource_mgr.get_datasources(filter_secret=True)

        req['name'] = 'datasource1'
        for key, value in req.iteritems():
            self.assertEqual(value, result[0][key])

        req['name'] = 'datasource2'
        for key, value in req.iteritems():
            self.assertEqual(value, result[1][key])

    def test_create_datasource_duplicate_name(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        req['name'] = 'datasource1'
        req['config'] = {'auth_url': 'foo',
                         'username': 'armax',
                         'password': 'password',
                         'tenant_name': 'armax'}
        # let driver generate this for us.
        del req['id']
        self.datasource_mgr.add_datasource(req)
        self.assertRaises(datasource_manager.DatasourceNameInUse,
                          self.datasource_mgr.add_datasource, req)

    def test_delete_datasource(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        req['config'] = {'auth_url': 'foo',
                         'username': 'armax',
                         'password': 'password',
                         'tenant_name': 'armax'}
        # let driver generate this for us.
        del req['id']
        result = self.datasource_mgr.add_datasource(req)
        self.datasource_mgr.delete_datasource(result['id'])
        self.assertRaises(datasource_manager.DatasourceNotFound,
                          self.datasource_mgr.get_datasource,
                          result['id'])
        engine = self.cage.service_object('engine')
        self.assertFalse(engine.policy_exists(req['name']))
        # TODO(thinrichs): test that we've actually removed
        #   the row from the DB

    def test_delete_datasource_error(self):
        req = self._get_datasource_request()
        req['driver'] = 'fake_datasource'
        req['config'] = {'auth_url': 'foo',
                         'username': 'armax',
                         'password': 'password',
                         'tenant_name': 'armax'}
        # let driver generate this for us.
        del req['id']
        result = self.datasource_mgr.add_datasource(req)
        engine = self.cage.service_object('engine')
        engine.create_policy('alice')
        engine.insert('p(x) :- %s:q(x)' % req['name'], 'alice')
        self.assertRaises(DanglingReference,
                          self.datasource_mgr.delete_datasource,
                          result['id'])

    def test_delete_invalid_datasource(self):
        self.assertRaises(datasource_manager.DatasourceNotFound,
                          self.datasource_mgr.delete_datasource,
                          "does_not_exist")

    def test_get_driver_schema(self):
        schema = self.datasource_mgr.get_driver_schema(
            'fake_datasource')
        self.assertEqual(
            schema,
            fake_datasource.FakeDataSource.get_schema())

    def test_get_datasouce_schema_driver_not_found(self):
        self.assertRaises(datasource_manager.DatasourceNotFound,
                          self.datasource_mgr.get_datasource_schema,
                          "does_not_exist")

    def test_create_table_dict(self):
        table_name = 'fake_table'
        schema = {'fake_table': ('id', 'name')}
        expected = {'table_id': table_name,
                    'columns': [{'name': 'id', 'description': 'None'},
                                {'name': 'name', 'description': 'None'}]}
        result = self.datasource_mgr.create_table_dict(table_name,
                                                       schema)
        self.assertEqual(expected, result)

    def test_duplicate_driver_name_raises(self):
        # Load the driver twice
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource',
             'congress.tests.fake_datasource.FakeDataSource'])
        self.datasource_mgr = datasource_manager.DataSourceManager
        self.assertRaises(datasource_manager.BadConfig,
                          self.datasource_mgr.validate_configured_drivers)
