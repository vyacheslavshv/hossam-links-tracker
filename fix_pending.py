"""
One-time script: convert pending JoinRequests to approved + create MemberEvents.
Run: python fix_pending.py
"""
import asyncio
from tortoise import Tortoise
from config import TORTOISE_ORM
from models import JoinRequest, MemberEvent, InviteLink


async def main():
    await Tortoise.init(config=TORTOISE_ORM)

    # Find all pending join requests
    pending = await JoinRequest.filter(status="pending").select_related("invite_link")

    if not pending:
        print("No pending requests found.")
        await Tortoise.close_connections()
        return

    print(f"Found {len(pending)} pending request(s):\n")

    for jr in pending:
        link_name = jr.invite_link.name if jr.invite_link else "N/A"
        print(f"  - User: {jr.full_name} (ID: {jr.user_id}), Link: {link_name}, Bot: {jr.bot_id}")

    confirm = input("\nConvert all to approved + create MemberEvents? [y/N]: ")
    if confirm.lower() != "y":
        print("Cancelled.")
        await Tortoise.close_connections()
        return

    created = 0
    for jr in pending:
        # Create MemberEvent if invite link exists
        if jr.invite_link:
            # Check if MemberEvent already exists (avoid duplicates)
            exists = await MemberEvent.filter(
                bot_id=jr.bot_id, user_id=jr.user_id,
                invite_link=jr.invite_link, event_type="joined"
            ).exists()

            if not exists:
                await MemberEvent.create(
                    bot_id=jr.bot_id,
                    invite_link=jr.invite_link,
                    user_id=jr.user_id,
                    username=jr.username,
                    full_name=jr.full_name,
                    event_type="joined",
                )
                created += 1
                print(f"  ✅ Created MemberEvent for {jr.full_name}")
            else:
                print(f"  ⏭ MemberEvent already exists for {jr.full_name}")

        # Update status
        jr.status = "approved"
        await jr.save()

    updated = len(pending)
    print(f"\nDone: {updated} request(s) → approved, {created} MemberEvent(s) created.")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
