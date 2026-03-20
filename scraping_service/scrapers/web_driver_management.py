from copy import copy
from threading import Thread
from time import sleep
from typing import Callable, TypeVar, TypeAlias, Optional

from selenium import webdriver
from selenium.common import NoSuchWindowException
from selenium.webdriver.remote.webdriver import WebDriver

from scrapers.read_once_list import ReadOnceList

_T = TypeVar("_T")


class WebDriverTask[_T]:
    def __init__(self, url: str, func: Callable[[WebDriver], _T]):
        self._url = url
        self._func = func

    def execute(self, driver: WebDriver) -> _T:
        driver.get(self._url)
        return self._func(driver)


class _WebDriverTaskQueue[_T]:
    def __init__(self, tasks: list[WebDriverTask[_T]]):
        self._tasks = copy(tasks)

    def next(self) -> Optional[WebDriverTask[_T]]:
        if len(self._tasks) != 0:
            return self._tasks.pop()
        else:
            return None


class _WebDriverWorker[_T]:
    def __init__(self, driver: WebDriver, queue: _WebDriverTaskQueue[_T], push: Callable[[_T], None]):
        self._driver = driver
        self._queue = queue
        self._push = push
        self._shouldTerminate = False

    def start(self):
        while not self._shouldTerminate:
            task = self._queue.next()
            if task is None:
                break
            try:
                result = task.execute(self._driver)
                self._push(result)
            except NoSuchWindowException as e:
                if not self._shouldTerminate:
                    raise e

    def terminate(self):
        self._shouldTerminate = True


class WebDriverOrchestrater[_T]:
    _WEB_DRIVER_COUNT = 3

    def __init__(self, tasks: list[WebDriverTask[_T]], listings: ReadOnceList[_T]):
        self._drivers: list[WebDriver] = []
        self._listings = listings
        self._was_dismissed = False
        self._queue = _WebDriverTaskQueue[_T](tasks)
        self._workers: list[_WebDriverWorker[_T]] = []
        self._init_drivers()

    def _init_drivers(self):
        for _ in range(self._WEB_DRIVER_COUNT):
            new_driver = webdriver.Chrome()
            self._drivers.append(new_driver)

    def start(self):
        self._workers = [
            _WebDriverWorker(driver, self._queue, self._listings.push)
            for driver in self._drivers]
        threads = [
            Thread(target=worker.start)
            for worker in self._workers]
        for thread in threads:
            thread.start()

    def dismiss(self):
        for driver in self._drivers:
            driver.close()
        for worker in self._workers:
            worker.terminate()
        self._was_dismissed = True

    def __del__(self):
        if not self._was_dismissed:
            self.dismiss()
