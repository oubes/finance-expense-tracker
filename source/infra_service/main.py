import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


from source.infra_service.core.bootstrap.app_factory import create_app

app = create_app()