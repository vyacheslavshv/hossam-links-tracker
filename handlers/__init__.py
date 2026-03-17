from aiogram import Router

from . import menu, links, stats, settings, events


def create_router() -> Router:
    router = Router()
    router.include_router(menu.create_router())
    router.include_router(links.create_router())
    router.include_router(stats.create_router())
    router.include_router(settings.create_router())
    router.include_router(events.create_router())
    return router
