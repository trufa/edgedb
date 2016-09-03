##
# Copyright (c) 2016 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import uuid

from edgedb.client import exceptions as exc
from edgedb.server import _testbase as tb


class TestInsert(tb.QueryTestCase):
    SETUP = """
        CREATE DELTA test::d_insert01 TO $$
            concept Subordinate:
                required link name to str

            concept InsertTest:
                link l1 to int
                required link l2 to int
                link l3 to str:
                    default: "test"
                link subordinates to Subordinate:
                    mapping: "1*"
        $$;

        COMMIT DELTA test::d_insert01;
    """

    async def test_insert_fail_1(self):
        err = 'missing value for required pointer ' + \
              '{test::InsertTest}.{test::l2}'
        with self.assertRaisesRegex(exc.MissingRequiredPointerError, err):
            await self.con.execute('''
                INSERT test::InsertTest;
            ''')

    async def test_insert_simple01(self):
        result = await self.con.execute(r"""
            INSERT test::InsertTest {
                l2 := 0,
                l3 := 'test'
            };

            INSERT test::InsertTest {
                l3 := "Test\"1\"",
                l2 := 1
            };

            INSERT test::InsertTest {
                l3 := 'Test\'2\'',
                l2 := 2
            };

            INSERT test::InsertTest {
                l3 := '\"Test\'3\'\"',
                l2 := 3
            };

            SELECT
                test::InsertTest {
                    l2, l3
                }
            ORDER BY test::InsertTest.l2;
        """)

        self.assert_data_shape(result, [
            [{
                'id': uuid.UUID,
            }],

            [{
                'id': uuid.UUID,
            }],

            [{
                'id': uuid.UUID,
            }],

            [{
                'id': uuid.UUID,
            }],

            [{
                'id': uuid.UUID,
                'l2': 0,
                'l3': 'test',
            }, {
                'id': uuid.UUID,
                'l2': 1,
                'l3': 'Test"1"',
            }, {
                'id': uuid.UUID,
                'l2': 2,
                'l3': "Test'2'",
            }, {
                'id': uuid.UUID,
                'l2': 3,
                'l3': '''"Test'3'"''',
            }]
        ])

    async def test_insert_nested(self):
        result = await self.con.execute('''
            INSERT test::Subordinate {
                name := 'subtest 1'
            };

            INSERT test::Subordinate {
                name := 'subtest 2'
            };

            INSERT test::InsertTest {
                l2 := 0,
                l3 := 'test',
                subordinates := (
                    SELECT test::Subordinate
                    WHERE test::Subordinate.name LIKE 'subtest%'
                )
            };

            SELECT test::InsertTest {
                subordinates: {
                    name
                } ORDER BY test::Subordinate.name
            };
        ''')

        self.assert_data_shape(
            result[3],
            [{
                'id': uuid.UUID,
                'subordinates': [{
                    'id': uuid.UUID,
                    'name': 'subtest 1'
                }, {
                    'id': uuid.UUID,
                    'name': 'subtest 2'
                }]
            }]
        )
