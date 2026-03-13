from copy import copy
from threading import Thread
from typing import Callable, TypeVar

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


class _WebDriverWorker[_T]:
    def __init__(self, driver: WebDriver, next_task: Callable[[], WebDriverTask[_T]]):
        self._driver = driver
        self._nextTask = next_task

    def start(self) -> list[_T]:
        results: list[_T] = []
        while True:
            task = self._nextTask()
            if task is None:
                break
            result = task.execute(self._driver)
            results.append(result)
        return results


class WebDriverOrchestrater[_T]:
    _WEB_DRIVER_COUNT = 3

    def __init__(self, tasks: list[WebDriverTask[_T]]):
        self._drivers: list[WebDriver] = []
        self._was_dismissed = False
        self._tasks = copy(tasks)
        self._results: list[_T] = []
        self._init_drivers()

    def _init_drivers(self):
        for _ in range(self._WEB_DRIVER_COUNT):
            new_driver = self._new_driver()
            self._drivers.append(new_driver)

    @staticmethod
    def _new_driver():
        return webdriver.Chrome()

    def start(self) -> list[_T]:
        workers = [
            _WebDriverWorker(driver, self._next_task)
            for driver in self._drivers]
        threads = [
            Thread(target=self._thread_routine(worker))
            for worker in workers]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return self._results

    def _thread_routine(self, worker: _WebDriverWorker[_T]):
        def routine():
            results = worker.start()
            self._results.extend(results)

        return routine

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
