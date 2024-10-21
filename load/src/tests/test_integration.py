import os

import pytest
import dlt

@pytest.mark.integration
def test__pipeline_run():
    from load.confluence import confluence
    pipeline = dlt.pipeline(
        pipeline_name="test_pipeline",
        destination="duckdb",
        dataset_name="confluence_data",
    )
    data = confluence(
        target_spaces=[os.environ["CONFLUENCE_DOC_INSIGHT__LOAD__INTEGRATION_TEST__TARGET_SPACES"]],
        analytics_backfill_days=0
    )
    result = pipeline.run(data)