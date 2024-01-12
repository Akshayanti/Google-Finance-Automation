import logging
import os
import re
import argparse
from datetime import date
from time import sleep

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class GoogleFinance:
    def __init__(self, data_dir, start_date, end_date):
        self.stonks_data = []
        self.portfolios = {}
        self.logger = logging.getLogger("")
        logging.basicConfig(level=logging.INFO)
        self.start_date = self.check_date(start_date) if start_date is not None else date.min
        self.end_date = self.check_date(end_date) if end_date is not None else date.max
        self.read_dir(data_dir)
        sleep(5)
        self.driver = uc.Chrome()
        self.driver.delete_all_cookies()

    def check_date(self, input_date):
        """
        Check the dates are in correct format, and then refashion them to allow easy comparison
            Parameters:
                    input_date (str): Date in DD-MM-YYYY format

            Returns:
                    d8 (date): Date object from input date
        """
        if re.compile("\d{2}-\d{2}-\d{4}").match(input_date):
            try:
                d, m, y = input_date.split("-")
                return date(month=int(m), day=int(d), year=int(y))
            except:
                pass
        self.logger.log(level=logging.ERROR, msg="The date should be in format DD-MM-YYYY")
        exit(1)

    def read_dir(self, dirname):
        """
        Reads all the tsv files inside a given directory, calling `read_file()` function on each of them.
        Does NOT read recursive directories
            Parameters:
                    dirname (str): Name of the directory
        """
        self.logger.log(level=logging.INFO, msg="Reading contents of {} directory for CSV and TSV files".format(dirname))
        for item in os.listdir(dirname):
            if os.path.isfile(os.path.join(dirname, item)) and item.endswith(".tsv"):
                self.read_tsv_file(os.path.join(dirname, item))
            elif os.path.isfile(os.path.join(dirname, item)) and item.endswith(".csv"):
                self.read_portfolio(os.path.join(dirname, item))
        self.logger.log(level=logging.INFO, msg="Finished reading contents of directory")

    def read_tsv_file(self, filename):
        """
        Reads a given tsv file and stores the list of stock data to be added to google finance portfolio
            Parameters:
                    filename (str): Name of the file
        """
        with open(filename, "r", encoding="utf-8") as infile:
            for line in infile:
                if line == "\n" or line.startswith("Symbol") or line.startswith("#"):
                    continue
                self.stonks_data.append(line.strip())
        self.remove_data_outside_dates()

    def read_portfolio(self, filename):
        """
        Reads portfolio.csv file and stores the mapping between group name and portfolio link
            Parameters:
                    filename (str): Name of the file
        """
        self.logger.log(level=logging.INFO, msg="Reading Portfolios...")
        with open(filename, "r", encoding="utf-8") as infile:
            for line in infile:
                if line == "\n" or line.startswith("Group_Name") or line.startswith("#"):
                    continue
                k, v = line.strip().split(",")
                if k not in self.portfolios.keys():
                    self.portfolios[k] = v.lstrip()
        self.logger.log(level=logging.INFO, msg="Finished Reading Portfolios")

    def remove_data_outside_dates(self):
        """
        Based on the parameters, remove the unnecessary data that falls outside the date range provided
        """
        for item in [x for x in self.stonks_data]:
            y, m, d = item.split("\t")[2].split("-")
            given_date = date(year=int(y), day=int(d), month=int(m))
            if self.start_date <= given_date <= self.end_date:
                continue
            self.stonks_data.remove(item)

    def login_google(self, email, password, two_fa_enabled):
        """
        Log in to the Google account with the associated credentials
            Parameters:
                    email (str): Email to log in with
                    password (str): Password to log in with
                    two_fa_enabled (bool): Adds a minute of wait after logging to allow the user to log in with their 2FA
        """
        self.driver.get("https://accounts.google.com")
        WebDriverWait(self.driver, 5) \
            .until(EC.visibility_of_element_located((By.NAME, 'identifier'))) \
            .send_keys(f'{email}' + Keys.ENTER)
        WebDriverWait(self.driver, 5) \
            .until(EC.visibility_of_element_located((By.NAME, 'Passwd'))) \
            .send_keys(f'{password}' + Keys.ENTER)
        sleep(5)
        if two_fa_enabled:
            sleep(30)

    def start_transactions(self, specific_symbol, specific_grp):
        """
        Adds the given stock to the Google finance portfolio.
        If the purchase unit was not processed properly, the details are printed on stderr
            Parameters:
                    specific_symbol (str): Specified if ONLY this symbol should be processed
                    specific_grp (str): Specified if ONLY this group should be processed
        """
        curr_grp = None
        for item in self.stonks_data:
            symbol, action, d8, qty, price, _, group = item.strip().split()
            if specific_grp is not None:
                if specific_grp != group:
                    continue
            if specific_symbol is not None:
                if specific_symbol != symbol:
                    continue
            if curr_grp != group:
                # Navigate to a different portfolio only if required. No need to reload the page every time.
                sleep(1)
                self.driver.get(self.portfolios[group])
                curr_grp = group
            if action == "BUY":
                try:
                    new_date = "/".join(reversed(d8.split("-")))
                    self.process_purchase(symbol.split(".")[0], qty, new_date, price)
                except:
                    message = "Could not add {x} units at {y}/unit on {z} for {s}".format(x=qty, y=price, z=d8,
                                                                                          s=symbol)
                    self.logger.log(logging.ERROR, msg=message)
                    self.driver.get(self.portfolios[group])
            elif action == "SELL":
                self.process_sale(symbol, qty, price, d8)

    def process_purchase(self, symbol_name, qty, d8, price):
        """
        Adds the given stock to the Google finance portfolio
            Parameters:
                    symbol_name (str): Stock symbol
                    qty (float): Number of units purchased
                    d8 (str): Date of purchase
                    price (float): Price of the unit
        """
        # Start adding a new investment
        try:
            WebDriverWait(self.driver, 5) \
                .until(EC.visibility_of_element_located((By.XPATH, '//span[text()="Investment"]'))) \
                .click()
        except:
            WebDriverWait(self.driver, 5) \
                .until(EC.visibility_of_element_located((By.XPATH, '//span[text()="Add investments"]'))) \
                .click()
        # Search for and input the symbol
        sleep(1)
        x = self.driver.find_element(By.XPATH, '//div[@class="mBfJdc"]//input[@class="Ax4B8 ZAGvjd"]')
        x.send_keys(f'{symbol_name}')
        x.click()
        x.send_keys(Keys.ENTER)
        # Add quantity
        WebDriverWait(self.driver, 5) \
            .until(EC.visibility_of_element_located((By.XPATH, '//input[@class="VfPpkd-fmcmS-wGMbrd ylDj9e"]'))) \
            .send_keys(f'{qty}')
        # Add purchase date as a string, rather than clicking on date frame
        sleep(1)
        purchase_date = self.driver.find_element(By.XPATH, '//input[@class="whsOnd zHQkBf"]')
        purchase_date.click()
        purchase_date.click()
        purchase_date.send_keys(f'{d8}')
        # Add cost/unit after clearing the already prefilled value
        sleep(1)
        cost_per_unit = self.driver.find_element(By.XPATH, '//input[@class="VfPpkd-fmcmS-wGMbrd Is59ac"]')
        cost_per_unit.clear()
        cost_per_unit.send_keys(f'{price}')
        # Save button
        WebDriverWait(self.driver, 5) \
            .until(EC.visibility_of_element_located((By.XPATH, '//span[text()="Save"]'))) \
            .click()
        sleep(1)

    def process_sale(self, symbol, qty, price, d8):
        """
        Notify what stocks need to be sold on what dates since this is not automated
            Parameters:
                    symbol (str): Stock symbol
                    qty (float): Number of units purchased
                    d8 (str): Date of purchase
                    price (float): Price of the unit
        """
        message = "Please manually sell {x} units at {y}/unit on {z} for {s}".format(x=qty, y=price, z=d8, s=symbol)
        self.logger.log(logging.INFO, message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, help="Directory containing the TSV and CSV files", required=True)
    parser.add_argument("--email", type=str, help="Email Id for logging in to Google", required=True)
    parser.add_argument("--password", type=str, help="Password for logging in to Google", required=True)
    parser.add_argument("--mfa", action='store_true', help="True if MFA is enabled on the account")
    parser.add_argument("--start_date", type=str, help="Start date (DD-MM-YYYY) when to start register")
    parser.add_argument("--end_date", type=str, help="End date (DD-MM-YYYY) when to end register")
    parser.add_argument("--symbol", type=str, help="Add data for specific symbol")
    parser.add_argument("--group", type=str, help="Add data for specific group")
    args = parser.parse_args()

    google = GoogleFinance(data_dir=args.directory, start_date=args.start_date, end_date=args.end_date)
    google.login_google(email=args.email, password=args.password, two_fa_enabled=args.mfa)
    google.start_transactions(specific_symbol=args.symbol, specific_grp=args.group)
