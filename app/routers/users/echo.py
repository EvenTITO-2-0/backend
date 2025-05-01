from fastapi import APIRouter

echo_router = APIRouter(
    prefix="/echo",
    tags=["Echo"],
)


@echo_router.get("", status_code=200, response_model=None)
async def echo():
    print("echo test OK!")
    return
