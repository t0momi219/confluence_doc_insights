import os
import dlt
from load.confluence import confluence


pipeline = dlt.pipeline(
    pipeline_name="confluence",
    destination="snowflake",
    dataset_name="confluence",
)
data = confluence(
    target_spaces=[],
    analytics_backfill_days=0
)
result = pipeline.run(data)
