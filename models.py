from tortoise import fields
from tortoise.models import Model


class BotSettings(Model):
    id = fields.IntField(pk=True)
    bot_id = fields.BigIntField(unique=True)
    auto_approve = fields.BooleanField(default=True)
    notifications_enabled = fields.BooleanField(default=True)

    class Meta:
        table = "bot_settings"


class InviteLink(Model):
    id = fields.IntField(pk=True)
    bot_id = fields.BigIntField(index=True)
    name = fields.CharField(max_length=255)
    url = fields.CharField(max_length=512)
    revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "invite_links"


class JoinRequest(Model):
    id = fields.IntField(pk=True)
    bot_id = fields.BigIntField(index=True)
    invite_link = fields.ForeignKeyField(
        "models.InviteLink", null=True, on_delete=fields.SET_NULL, related_name="join_requests"
    )
    user_id = fields.BigIntField()
    username = fields.CharField(max_length=255, null=True)
    full_name = fields.CharField(max_length=512)
    status = fields.CharField(max_length=10, default="pending")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "join_requests"


class MemberEvent(Model):
    id = fields.IntField(pk=True)
    bot_id = fields.BigIntField(index=True)
    invite_link = fields.ForeignKeyField(
        "models.InviteLink", null=True, on_delete=fields.SET_NULL, related_name="member_events"
    )
    user_id = fields.BigIntField()
    username = fields.CharField(max_length=255, null=True)
    full_name = fields.CharField(max_length=512)
    language = fields.CharField(max_length=10, null=True)
    is_bot = fields.BooleanField(default=False)
    is_premium = fields.BooleanField(default=False)
    event_type = fields.CharField(max_length=10)  # joined / left
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "member_events"
