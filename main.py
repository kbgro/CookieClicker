import time
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class Transaction(Enum):
    BUY = 0
    SELL = 1


class Cookie:

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.transaction: Transaction = Transaction.BUY
        self.cookies_count: int = 0
        self.bulk_amount: int = 0
        self.bought_products: List[str] = []

    def set_cookie_count(self) -> None:
        """Sets cookie cookie count"""
        cookies = self.driver.find_element(By.ID, "cookies").text.split()[0].strip()
        cookies_c = cookies.replace(",", "")
        self.cookies_count = int(cookies_c)

    def pause(self) -> None:
        """Pause clicking"""

    def click(self) -> None:
        """Click cookie"""
        cookie = self.driver.find_element(By.XPATH, "//*[@id='bigCookie']")
        cookie.click()

    def _toggle_buy_sell(self, amount: int) -> None:
        mapping = {
            1: "storeBulk1",
            10: "storeBulk10",
            100: "storeBulk100",
            0: "storeBulkMax",
        }
        self.bulk_amount = amount if amount in mapping else 1
        self.driver.find_element(By.ID, mapping.get(self.bulk_amount)).click()

    def toggle_buy(self, amount: int) -> None:
        """
        Toggle the amount of building to buy

        :param amount: amount to buy
        """
        self.transaction = Transaction.BUY
        buy = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "storeBulkBuy")))
        # self.driver.find_element(By.ID, "storeBulkBuy").click()
        buy.click()
        self._toggle_buy_sell(amount)

    def toggle_sell(self, amount: int) -> None:
        """
        Toggle the amount of building to buy

        :param amount: amount to buy
        """
        self.transaction = Transaction.SELL
        self.driver.find_element(By.ID, "storeBulkSell").click()
        self._toggle_buy_sell(amount)

    def products(self, unlocked=True) -> List[WebElement]:
        """
        Returns all products or only unlocked products (which is the default implementation

        :param unlocked: when True only unlocked products are returned
        :return: products WebElements
        """
        selector = "#products .product"
        if unlocked:
            selector += ".unlocked.enabled"

        return self.driver.find_elements(By.CSS_SELECTOR, selector)

    @staticmethod
    def unlocked_product_prices(products: List[WebElement]) -> Dict[WebElement, int]:
        """
        Returns all only unlocked products prices

        :param products: unlocked products list
        :return: dictionary of products WebElements and their prices
        """
        return {element: int(element.text.split()[1].strip().replace(",", "")) for element in products}

    def affordable_products(self, products: Dict[WebElement, int]) -> List[WebElement]:
        """
        Returns affordable products

        :param products: unlocked product dictionary
        :return: affordable products
        """
        return [product for product, cost in products.items() if self.is_affordable(cost)]

    def is_affordable(self, value: int) -> bool:
        """
        Check if product value is affordable

        :param value: product cost
        :return: True if product is affordable else False
        """
        return self.cookies_count >= value

    def purchase_building(self, products: List[WebElement]) -> None:
        """
        Purchase a building.

        :param products: products/building to purchase
        """
        if products:
            last_product = products[-1]
            product_name = last_product.text.split("\n")[0].strip()
            print(f"{product_name=}")
            if product_name not in self.bought_products:
                self.bought_products.append(product_name)
                self.driver.execute_script("arguments[0].click();", last_product)

            if len(self.bought_products) == 2 and self.bulk_amount != 10:
                self.toggle_buy(10)
                self.bought_products.clear()

    def mining(self) -> None:
        """Mining Cookies"""
        start = datetime.now()
        last_checked = datetime.now()

        while True:
            self.click()
            self.set_cookie_count()

            if (last_checked - datetime.now()).seconds > 3:
                unlocked_products = self.products()
                print(f"unlocked: {len(unlocked_products)}")
                if unlocked_products:
                    unlocked_products = self.unlocked_product_prices(unlocked_products)

                    # to get most expensive upgrade that is affordable
                    affordable_products = self.affordable_products(unlocked_products)
                    self.purchase_building(affordable_products)

                # time.sleep(.000001)
                print(f"{self.cookies_count=}")
                last_checked = datetime.now()

            if (datetime.now() - start).seconds / 60 > 10:
                print(self.cookies_count)
                break


@contextmanager
def get_driver():
    driver = webdriver.Chrome()
    try:
        yield driver
    finally:
        driver.close()


def main():
    with get_driver() as driver:
        driver.get("https://orteil.dashnet.org/cookieclicker/")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "bigCookie")))

        cookie = Cookie(driver)
        cookie.mining()


if __name__ == '__main__':
    main()
