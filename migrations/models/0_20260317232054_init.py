from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "bot_settings" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "bot_id" BIGINT NOT NULL UNIQUE,
    "auto_approve" INT NOT NULL DEFAULT 1,
    "notifications_enabled" INT NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS "invite_links" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "bot_id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "url" VARCHAR(512) NOT NULL,
    "revoked" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_invite_link_bot_id_334ef3" ON "invite_links" ("bot_id");
CREATE TABLE IF NOT EXISTS "join_requests" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "bot_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "username" VARCHAR(255),
    "full_name" VARCHAR(512) NOT NULL,
    "status" VARCHAR(10) NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "invite_link_id" INT REFERENCES "invite_links" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_join_reques_bot_id_6552d4" ON "join_requests" ("bot_id");
CREATE TABLE IF NOT EXISTS "member_events" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "bot_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "username" VARCHAR(255),
    "full_name" VARCHAR(512) NOT NULL,
    "language" VARCHAR(10),
    "is_bot" INT NOT NULL DEFAULT 0,
    "is_premium" INT NOT NULL DEFAULT 0,
    "event_type" VARCHAR(10) NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "invite_link_id" INT REFERENCES "invite_links" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_member_even_bot_id_749bc8" ON "member_events" ("bot_id");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztm1tz2jgUgP8K46d0hu0ACSHdN0hJS8ulQ8juTjsdj7CF0WJL1JZJmQ7/vZJs47uLU6"
    "4dPYWci6zzWdI5RyQ/FIvo0HRedwh9hJQibDjK35UfCgYWZB+y1NWKApbLUMkFFExNYT8l"
    "VHWillOH2kCjTDcDpgOZSIeOZqMlRQQzKXZNkwuJxgyZVyhyMfrmQpUSA9I5tJniy1cmRl"
    "iH36ET/LpcqDMETT02a6TzZwu5StdLIeth+iAM+dOmqkZM18Kh8XJN5wRvrRGmXGpADG1A"
    "IR+e2i6fPp+dH20QkTfT0MSbYsRHhzPgmjQS7o4MNII5PzYb77UY/Cl/Neo3rZu769ubO2"
    "YiZrKVtDZeeGHsnqMgMJwoG6EHFHgWAmPIjb+9LHYdZOTiC31+jTAAdgYM3zQa19etRu36"
    "9q5502o172pbmGlVEdVO7x0HywwIW+jeLghIh2SBS4nKto1NVjCDLyEmBDgbcNI1gXnKfF"
    "/CORCEoMMNGpDeon8R6SJoo1GfT9pynG+mRzGBcPg06HTHV/VXXMyMEM0hiwlFM6QBPjtH"
    "hZjHm7WEixDnjiFZb/ghO1tEjgsumAJt8QxsXU1pSIPk2aZVVsNKSgAGhiDE4+RR+Rmoh1"
    "dsWn2EF1n5KaItTE9I2KkmM5TpSaanvWzlPyI/iZ8psPdzYOecmL59AioL5FDn429StcB3"
    "1YTYoHO+HpvNAmL/tMf379vjK2b1KnFQ+qqGp4sjdG2zDEHf/DIBNuuNHQAyq1yAQhcHaM"
    "MVWZTO3RGvI2brstniJKWRZkMetgpomulbpqHIgtlQ454Jrrrv+jr4cKYrlsWgj7C59s/o"
    "AuaT3qD7OGkPPsXAv21PulzTENJ1Qnp1m1jb20Eq//Ym7yv818rn0bArCBKHGrZ4Ymg3+a"
    "zwOYn6HpNnFeiRdBJIAzBl6rBwBfxPEFZtyJA71MnYWL77w8cxNEX1m/G6/RLrAxtq7I20"
    "w/v2ozji694EaziQhq89Ui5CawptFa4g/l0eAzFUl490WTwOWaVHF0lGmZ5YQ/l1emrdyk"
    "JdFuqyUOdlo8POr7JsI06Hgrv37H0yumVboajPi6r54+eGI3RDM/ZgtSzKmJPsjLYwHQqo"
    "m1Gv5JMMPY6HUVlCrHNS+2JZr+2Asl7LJclVsiP6Yzui6IuNXOxmZsf8qi3l+KIMeYIzfA"
    "81XKqnzASapvlAbIgM/BGuBdQemxjAWtapnXk/f3Ys83olJrbB87YxyFgsLFQWIPRuYB67"
    "k8rwqd9XNqf5jiTakmZ0X4mONb/7SnXJsvs6t51bld2X7L5k9yW7L9l9Hbz7MgE2XJZxy7"
    "CM+lzkstx/74UclWWZkt/uhU7yy70UzqUNLeRa5ZFGHCXWOFZR9Ho4Smz3uNdlnp3ytkXe"
    "tijytkXetsjblp1uW9rQRtpcybho8TXVojsWENrIy5Uz26jVgsuVFbQd/+9Cdi0OIi6XWR"
    "kcpEXlW6MERN/8MgHWa7vVVkXFVbq6Ipj6V7lxiB8eR8Ocsip0SYB8wizALzrSaLViIod+"
    "PU+sBRR51LHyKYB3NWj/l+R63x91knURH6Bz6n942PwEHoS9Og=="
)
