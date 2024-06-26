from datetime import datetime, timezone

import pytest
from mock.mock import call

from utils.db.helpers import TableStats, get_table_stats_for_schema, move_table, snowflake_engine, upload_csv_as_table


@pytest.mark.parametrize(
    "config,expected_url",
    [
        pytest.param(
            {
                "SNOWFLAKE_ACCOUNT": "test-account",
                "SNOWFLAKE_USER": "admin",
                "SNOWFLAKE_PASSWORD": "safe",
                "SNOWFLAKE_DATABASE": "test-database",
                "SNOWFLAKE_SCHEMA": "test-schema",
                "SNOWFLAKE_WAREHOUSE": "test-warehouse",
                "SNOWFLAKE_ROLE": "test-role",
            },
            "snowflake://admin:safe@test-account/test-database/test-schema?role=test-role&warehouse=test-warehouse",
            id="all properties",
        ),
        pytest.param(
            {
                "SNOWFLAKE_ACCOUNT": "test-account",
                "SNOWFLAKE_USER": "admin",
                "SNOWFLAKE_PASSWORD": "safe",
                "SNOWFLAKE_DATABASE": "test-database",
                "SNOWFLAKE_SCHEMA": "test-schema",
                "SNOWFLAKE_WAREHOUSE": "test-warehouse",
            },
            "snowflake://admin:safe@test-account/test-database/test-schema?warehouse=test-warehouse",
            id="missing role",
        ),
        pytest.param(
            {
                "SNOWFLAKE_ACCOUNT": "test-account",
                "SNOWFLAKE_USER": "admin",
                "SNOWFLAKE_PASSWORD": "safe",
                "SNOWFLAKE_DATABASE": "test-database",
                "SNOWFLAKE_WAREHOUSE": "test-warehouse",
                "SNOWFLAKE_ROLE": "test-role",
            },
            "snowflake://admin:safe@test-account/test-database?role=test-role&warehouse=test-warehouse",
            id="missing schema",
        ),
        pytest.param(
            {
                "SNOWFLAKE_ACCOUNT": "test-account",
                "SNOWFLAKE_USER": "admin",
                "SNOWFLAKE_PASSWORD": "safe",
            },
            "snowflake://admin:safe@test-account/",
            id="basic properties",
        ),
    ],
)
def test_should_pass_connection_details(mocker, config, expected_url):
    """
    Test that if the proper variables are passed to SQL alchemy engine factory, then
    they are used for creating the SQLAlchemy connection.
    """
    # GIVEN: create_engine exists and ready to create connections
    mock_create_engine = mocker.patch("utils.db.helpers.create_engine")

    # WHEN: request to create with given role
    snowflake_engine(config)

    # THEN: expect proper keys have been used to create the engine
    mock_create_engine.assert_called_once_with(expected_url, connect_args={"sslcompression": 0})


def test_should_return_table_stats(mocker):
    # GIVEN: mock engine and mock connection
    mock_engine = mocker.MagicMock()
    mock_connection = mocker.MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_connection
    # GIVEN: query will return results
    mock_connection.execute.return_value = [
        ('schema', 'table1', 3, datetime(2022, 12, 28, 23, 55, 59, tzinfo=timezone.utc)),
        ('schema', 'table2', 20, datetime(2023, 1, 15, 12, 23, 45, tzinfo=timezone.utc)),
    ]

    # WHEN: request to get table stats
    result = get_table_stats_for_schema(mock_engine, 'database', 'schema')

    # THEN: expect two rows to have been returned
    assert result == [
        TableStats('schema', 'table1', 3, datetime(2022, 12, 28, 23, 55, 59, tzinfo=timezone.utc)),
        TableStats('schema', 'table2', 20, datetime(2023, 1, 15, 12, 23, 45, tzinfo=timezone.utc)),
    ]


def test_should_upload_file_to_table(mocker):
    # GIVEN: mock engine and mock connection
    mock_engine = mocker.MagicMock()
    mock_connection = mocker.MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_connection

    # WHEN: request to get upload a file to a table
    upload_csv_as_table(mock_engine, '/tmp/upload.csv', 'test-schema', 'a-table')

    # THEN: expect the script to has been called.
    mock_connection.execute.assert_has_calls(
        [
            call('TRUNCATE TABLE test-schema.a-table'),
            call('CREATE TEMPORARY STAGE IF NOT EXISTS test-schema.a-table'),
            call('PUT file:///tmp/upload.csv @test-schema.a-table OVERWRITE=TRUE'),
            call(
                "COPY INTO test-schema.a-table FROM @test-schema.a-table FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '\"')"  # noqa: E501
            ),  # noqa: E501
        ]
    )


def test_should_move_table(mocker):
    # GIVEN: mock connection
    mock_connection = mocker.MagicMock()
    mock_connection.execute = mocker.MagicMock()

    # WHEN: request to move table
    move_table(mock_connection, "table", "source-db", "source-schema", "target-db", "target-schema")

    # THEN: expect an alter table
    mock_connection.execute.assert_called_once_with(
        '''
        ALTER TABLE source-db.source-schema.table
        RENAME TO target-db.target-schema.table
    '''
    )


def test_should_move_table_with_postfix(mocker):
    # GIVEN: mock connection
    mock_connection = mocker.MagicMock()
    mock_connection.execute = mocker.MagicMock()

    # WHEN: request to move table
    move_table(mock_connection, "table", "source-db", "source-schema", "target-db", "target-schema", postfix="_old")

    # THEN: expect an alter table
    mock_connection.execute.assert_called_once_with(
        '''
        ALTER TABLE source-db.source-schema.table
        RENAME TO target-db.target-schema.table_old
    '''
    )
