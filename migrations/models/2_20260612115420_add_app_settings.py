from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "app_settings" (
    "key" VARCHAR(64) NOT NULL PRIMARY KEY,
    "value" TEXT
) /* Global key\/value settings shared by the master bot (not per-worker-bot). */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "app_settings";"""


MODELS_STATE = (
    "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"
    "Y/8fT8P+0r+vo="
)
