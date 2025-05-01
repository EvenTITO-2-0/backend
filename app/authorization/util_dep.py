from fastapi import Depends, HTTPException


def verify_or_dep(deps: list[bool]):
    if any(deps):
        return
    raise HTTPException(status_code=403, detail="Not enough permissions")


def verify_or2(first, second):
    async def verify(first_dep: first, second_dep: second) -> None:
        return verify_or_dep([first_dep, second_dep])

    return Depends(verify)


def verify_or3(first, second, third):
    async def verify(first_dep: first, second_dep: second, third_dep: third) -> None:
        return verify_or_dep([first_dep, second_dep, third_dep])

    return Depends(verify)


def verify_or4(first, second, third, fourth):
    async def verify(first_dep: first, second_dep: second, third_dep: third, fourth_dep: fourth) -> None:
        return verify_or_dep([first_dep, second_dep, third_dep, fourth_dep])

    return Depends(verify)


def verify_or5(first, second, third, fourth, fifth):
    async def verify(
        first_dep: first, second_dep: second, third_dep: third, fourth_dep: fourth, fifth_dep: fifth
    ) -> None:
        return verify_or_dep([first_dep, second_dep, third_dep, fourth_dep, fifth_dep])

    return Depends(verify)


def or_(*dependencies):
    if len(dependencies) == 2:
        return verify_or2(*dependencies)
    elif len(dependencies) == 3:
        return verify_or3(*dependencies)
    elif len(dependencies) == 4:
        return verify_or4(*dependencies)
    elif len(dependencies) == 5:
        return verify_or5(*dependencies)
    raise HTTPException(status_code=500)
