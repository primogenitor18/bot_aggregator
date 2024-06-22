import traceback
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Response,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware

from response_models import Error40xResponse

from models.base import AnonymousUser

from managers.auth.manager import AuthManager

from v1.auth.handlers.auth import router as auth_router
from v1.auth.handlers.account import router as account_router
from v1.provider.handlers.provider import router as provider_router
from v1.search.handlers.search import router as search_router

from redis.connector import OsintClientRedisConnection

from config import (
    REDIS_URI,
    REDIS_PORT,
    REDIS_PUBSUB_DB,
    REDIS_DB,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_connection = OsintClientRedisConnection(host=REDIS_URI, port=REDIS_PORT, db=REDIS_DB)
    await redis_connection.add_transport(conn_name="redis_pubsub_con", db=REDIS_PUBSUB_DB)
    app.redis_pubsub_con = redis_connection.transports["redis_pubsub_con"]
    await redis_connection.add_transport(conn_name="redis_conn")
    app.redis_conn = redis_connection.transports["redis_conn"]
    yield


app = FastAPI(root_path="/api", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(provider_router)
app.include_router(search_router)

@app.middleware("http")
async def get_auth(request: Request, call_next, *args, **kwargs):
    request.scope["user"] = AnonymousUser()
    request.scope["auth"] = {"status": False, "reason": ""}
    if request.headers.get("authorization"):
        try:
            user_type, token = request.headers.get("authorization").split(" ")
            code, reason, user_info = await AuthManager.check_token(token=token)
        except:
            request.scope["auth"]["reason"] = "wrong token type"
        else:
            request.scope["user"] = user_info
            request.scope["auth"]["reason"] = reason
    else:
        request.scope["auth"]["reason"] = "no token"

    try:
        response = await call_next(request)
    except Exception:
        trace = traceback.format_exc()
        print(trace)
        response = Response(
            content=Error40xResponse(reason="Internal error").json(),
            status_code=status.HTTP_409_CONFLICT,
            media_type="application/json",
        )

    return response
