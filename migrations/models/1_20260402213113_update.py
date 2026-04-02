from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "bot_configs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "bot_token" VARCHAR(255) NOT NULL UNIQUE,
    "channel_id" BIGINT NOT NULL,
    "notification_channel_id" BIGINT,
    "timezone" VARCHAR(64) NOT NULL DEFAULT 'Europe/Berlin',
    "is_active" INT NOT NULL DEFAULT 1,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
        CREATE TABLE IF NOT EXISTS "client_admins" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "bot_id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "uid_client_admi_bot_id_2150af" UNIQUE ("bot_id", "user_id")
);
CREATE INDEX IF NOT EXISTS "idx_client_admi_bot_id_6abaa4" ON "client_admins" ("bot_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "bot_configs";
        DROP TABLE IF EXISTS "client_admins";"""


MODELS_STATE = (
    "eJztm1tz2jgUgP8K46fsDNsFQi67b0DJljaBDiG7O81kPMIWRostUVlOmu3w31eSbXx3cQ"
    "oEMnojOufY0ucjnYud75pDTGi777qE9QieIUv7o/Zdw8CB/EdWWK9pYLmMRGKAgakttaeE"
    "6YbUk+Ng6jIKDMZFM2C7kA+Z0DUoWjJEMB/Fnm2LQWJwRYStaMjD6KsHdUYsyOaQcsH9Ax"
    "9G2ITfoBv+uVzoMwRtMzFlZIp7y3GdPS/l2ACzK6ko7jblc7Q9B0fKy2c2J3itjTAToxbE"
    "kAIGxeUZ9cT0xeyCxYYr8mcaqfhTjNmYcAY8m8WWuyEDTlLw47Nx5QItcZdfW832Rfvy9L"
    "x9yVXkTNYjFyt/edHafUNJYDjRVlIOGPA1JMaIm3h4jCwgzuLrzQHN55cwSmHkk09jDKG9"
    "KkcHfNNtiC02F/DOzkqo/dUZ9z50xidc6xexFsLd2Xf1YSBq+TKBNkJpzAHG0NbzXLGLrE"
    "JvTNr92Cs3wRkORDyjvbhVx/y91To9vWg1Ts8vz9oXF2eXjbWHZkVlrtod/Cm8NYE7dN+I"
    "MSYMzZABxGz1lwIvuciL6Aeu+ubhM+TA/wiGVY6KuM12TopN6Gp9j5Il/K0LqY3kKbWVY+"
    "O8vcGpcd4uPDSEKIkUuToPlegxh2mXEBsCXBDB4nYprlNuuCuw61P5RTTLPHA0uhaTdlz3"
    "q+27ZMofh3c33f74pCnpciXECtzUoFCsWgcsC/U9lwiXLDiJE5YprGZg+i78caDnMl+DOc"
    "L2c/C0SphPBjf920nn5nMC/PvOpC8kLTn6nBo9OU959/oitb8Hkw818Wfty2jYlwSJyywq"
    "7xjpTb5oYk7AY0TH5EkHZizch6MhmJVI+GaLWOoiBqbAWDwBauoZCWmRIt2syGk56RGAgS"
    "Ufi4ArphmlwreQMQ7e1fIz5bX4h7myG9dUyfKRJctVk43IZjuZ3Z4Y7jm1kPuebxtKKofC"
    "tKmKhoUZs6tDLNab58JliAuvoVgfSoDq2Qhi1jEdhPMCVFxcGqAMqciDMtfcQYS6j52Hng"
    "up+PmgwtbbD1vZLf4m4lbow5XYxoxUt6eMrqrkVCW37UA5wI88fl8jvMiLkzFpaZhEUk+3"
    "uaKq41RAVAFxXW4Ap1J/ONTfX2/44N8jedSuQjBQP06AZ83WBgC5ViFAKUsCpPCRLCoXuT"
    "GrPZa1VaOF6qirPGxveVjkAf8ShHUKOXKXuTkbKzC/+jSGtmwT5TzuIMX6yC819q90kO9W"
    "V6EPh6PRY4+li9CZ8iIOPkL8szxu5KX64krHxWOXWXrcSXLS9JQPFefpGb9VibpK1FWirj"
    "pXe6BbtRSK27wom3+F75B2Xw3N+I31qigTRqoyWsN0GWBeTr5STDKy2OPXW0uITUFqWyyb"
    "jQ1QNhuFJIVIVURvtiJKfJAXNXZzo2Nx1pYxPK5vSX8qh8vUlLlAszSvCIXIwp/gs4Q64B"
    "MD2Mg7tXP78wfHsqhW4sMUPK0Lgxxn4UvlC4R+B+a2P6kN766vtdXrvCOJl6Q51VeqYi2u"
    "vjJVsqq+Dm3n1lX1paovVX2p6ktVXzuvvmyALY9H3Cos4zZH6Zbbr72Qq/MoU/HtXmSkXu"
    "5lcC4pdJDnVEcaM1RYk1hl0uvjqLDdk1bHeXaqbovqtmiq26K6LarbslG3pQMpMuZaTqMl"
    "kNTLeiwg0lHNlQPbqPWS5sojpG7wXcimyUHM5Dgzg52UqGJrVIAYqB8nwGZjs9yqLLnKZl"
    "cEs6CVm4T48XY0LEirIpMUyDvMF3hvIoPVazZy2cNhYi2hKFadSJ9CeCc3nX/SXHvXo246"
    "LxIX6L72fwau/gd5/4nX"
)
