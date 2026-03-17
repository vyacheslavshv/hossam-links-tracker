from aiogram import Router

from . import menu, links, stats, settings, events


def create_router() -> Router:
    router = Router()
    router.include_router(menu.router)
    router.include_router(links.router)
    router.include_router(stats.router)
    router.include_router(settings.router)
    router.include_router(events.router)
    return router
