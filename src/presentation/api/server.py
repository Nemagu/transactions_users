from logging import getLogger

import uvicorn
from fastapi import FastAPI

from infrastructure.config import APIWorkerSettings
from presentation.api.dependencies import APILifespan
from presentation.api.error_handler import setup_error_handler
from presentation.api.middlewares import (
    LoggingMiddleware,
    PerformanceMiddleware,
    RequestIDMiddleware,
)
from presentation.api.routers import main_router

logger = getLogger(__name__)


class APIWorker:
    def __init__(self, settings: APIWorkerSettings) -> None:
        self.settings = settings
        logger.info("init api worker lifespan")
        lifespan = APILifespan(self.settings)

        logger.info("init fastapi app")
        self.app = FastAPI(lifespan=lifespan.lifespan)

        self.app.add_middleware(LoggingMiddleware)
        self.app.add_middleware(PerformanceMiddleware)
        self.app.add_middleware(RequestIDMiddleware)

        setup_error_handler(self.app)

        self.app.include_router(main_router)

    def run(self) -> None:
        config = uvicorn.Config(
            app=self.app,
            host=self.settings.uvicorn.host,
            port=self.settings.uvicorn.port,
            reload=self.settings.uvicorn.reload,
            loop=self.settings.uvicorn.loop,
            workers=self.settings.uvicorn.workers,
            access_log=False,
        )
        server = uvicorn.Server(config)
        logger.info("start api server")
        server.run()
