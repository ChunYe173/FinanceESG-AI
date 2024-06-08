from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


class DriverManager:
    def __init__(self):
        self.driver = None

    def get_webdriver_instance(self):
        if self.driver is None:
            self.driver = webdriver.Chrome()
        return self.driver

    def close(self):
        if self.driver is not None:
            self.driver.close()
            self.driver.quit()
            self.driver = None
