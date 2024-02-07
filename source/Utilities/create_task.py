import asyncio
from asyncio import Task
from typing import Coroutine

from Utilities.handle_task_result import handle_task_result


def create_task(coro: Coroutine) -> Task:
    task = asyncio.create_task(coro)
    task.add_done_callback(handle_task_result)
    return task
