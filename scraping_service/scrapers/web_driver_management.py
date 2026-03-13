from copy import copy
from threading import Thread
from time import sleep
from typing import Callable, TypeVar, TypeAlias, Optional

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

_T = TypeVar("_T")


class WebDriverTask[_T]:
    def __init__(self, url: str, func: Callable[[WebDriver], _T]):
        self._url = url
        self._func = func

    def execute(self, driver: WebDriver) -> _T:
        driver.get(self._url)
        return self._func(driver)


NextTask: TypeAlias = Callable[[], Optional[WebDriverTask[_T]]]


class _WebDriverWorker[_T]:
    def __init__(self, driver: WebDriver, next_task: NextTask[_T], push: Callable[[_T], None]):
        self._driver = driver
        self._next_task = next_task
        self._push = push

    def start(self):
        while True:
            task = self._next_task()
            if task is None:
                break
            result = task.execute(self._driver)
            self._push(result)


class _WebDriverThreadController[_T]:
    _TIME_INCREMENT_MS = 100

    def __init__(self, driver: WebDriver, next_task: NextTask[_T], push: Callable[[_T], None], timeout: int):
        self._driver = driver
        self._next_task = next_task
        self._push = push
        self._timeout_ms = timeout * 1000
        self._supervisor_thread = Thread(target=self._supervise)
        self._worker_thread: Thread = Thread(target=self._work)
        self._lifetime_ms = 0
        self._should_terminate = False

    def start(self):
        self._supervisor_thread.start()
        self._worker_thread.start()
        while not self._should_terminate:
            pass

    def _work(self):
        supervised_next_task = lambda: self._next_task() if not self._should_terminate else None
        _WebDriverWorker(
            self._driver,
            supervised_next_task,
            self._push
        ).start()

    def _supervise(self):
        while not self._should_terminate:
            sleep(self._TIME_INCREMENT_MS * 0.001)
            self._lifetime_ms += self._TIME_INCREMENT_MS
            if self._lifetime_ms >= self._timeout_ms:
                self._should_terminate = True
                print("should terminate now")


class WebDriverOrchestrater[_T]:
    _WEB_DRIVER_COUNT = 3

    def __init__(self, tasks: list[WebDriverTask[_T]]):
        self._drivers: list[WebDriver] = []
        self._was_dismissed = False
        self._results: list[_T] = []
        self._tasks = copy(tasks)
        self._init_drivers()

    def _init_drivers(self):
        for _ in range(self._WEB_DRIVER_COUNT):
            new_driver = webdriver.Chrome()
            self._drivers.append(new_driver)

    def start(self) -> list[_T]:
        thread_controllers = [
            _WebDriverThreadController(driver, self._next_task, self._results.append, 15)
            for driver in self._drivers]
        threads = [
            Thread(target=controller.start)
            for controller in thread_controllers]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return self._results

    def _next_task(self):
        try:
            next_task = self._tasks.pop(0)
            return next_task
        except IndexError:
            return None

    def dismiss(self):
        for driver in self._drivers:
            driver.close()
        self._was_dismissed = True

    def __del__(self):
        if not self._was_dismissed:
            self.dismiss()
