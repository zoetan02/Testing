import logging
import multiprocessing
import os
import unittest
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from tests.authentication_test.test_login import TestLogin
from tests.authentication_test.test_register import TestRegister
#from tests.authentication_test.test_setting import TestSetting
#from tests.authentication_test.test_forgotpassword import TestPassword
from tests.deposit_test.test_quickreload import TestQuickReload
from tests.deposit_test.test_banktransfer import TestBankTransfer
from tests.withdraw_test.test_withdrawtransfer import TestWithdrawTransfer
#from tests.withdraw_test.test_ewallet import TestEWallet
#from tests.coupon_test.test_coupon import TestCoupon
#from tests.transaction_history_test.test_history import TestHistory
from tests.test_profile import TestProfilePage
from tests.deposit_test.test_spamdeposit import TestSpamDeposit
from tests.transfer_test.test_transfer import TestTransfer
from tests.transfer_test.test_main_provider import TestMainProvider
from tests.transfer_test.test_provider_to_provider import TestProviderToProvider
from tests.revert_test.revert_test import TestRevert
import sys


def setup_logger(log_filename):
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_filename),
                            logging.StreamHandler(sys.stdout)
                        ])


class CustomTestResult(unittest.TextTestResult):

    def __init__(self, stream, descriptions, verbosity, browser, language):
        super().__init__(stream, descriptions, verbosity)
        self.successes = []
        self.errors_and_failures = []
        self.test_results = []
        self.browser = browser
        self.language = language

    def log_test(self, status, test, error=None):
        test_class = test.__class__.__name__
        test_name = test._testMethodName
        message = f"{test_class} - {self.browser} - {self.language} - {status}"
        if error:
            message += f" - {error}"
        logging.info(message)
        self.test_results.append((status, test, error))

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test)
        self.log_test("PASS", test)

    def addError(self, test, err):
        super().addError(test, err)
        self.errors_and_failures.append(("ERROR", test, err))
        self.log_test("ERROR", test, err)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.errors_and_failures.append(("FAILURE", test, err))
        self.log_test("FAILURE", test, err)


class CustomTestRunner(unittest.TextTestRunner):

    def __init__(self, language, browser, **kwargs):
        super().__init__(**kwargs)
        self.language = language
        self.browser = browser

    def _makeResult(self):
        return CustomTestResult(self.stream, self.descriptions, self.verbosity,
                                self.browser, self.language)

    def run(self, test):
        result = super().run(test)
        logging.info(f"Test Run Summary - {self.browser} - {self.language}")
        logging.info(f"Total tests run: {result.testsRun}")
        logging.info(f"Successes: {len(result.successes)}")
        logging.info(f"Failures: {len(result.failures)}")
        logging.info(f"Errors: {len(result.errors)}")
        return result


def create_test_suite(language, browser):
    suite = unittest.TestSuite()
    test_classes = [TestLogin]
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        for test in tests:
            suite.addTest(
                test_class(test._testMethodName,
                           language=language,
                           browser=browser))
    return suite


def run_tests(language, browser):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"TestResults_{language}_{browser}_{timestamp}.log"
    setup_logger(log_filename)

    logging.info(f"Starting test run - {browser} - {language}")
    suite = create_test_suite(language, browser)
    runner = CustomTestRunner(language, browser, verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    languages = ["bm"]
    browsers = ["chrome"]
    processes = []

    for browser in browsers:
        for language in languages:
            logging.info(f"Launching test process - {browser} - {language}")
            process = multiprocessing.Process(target=run_tests,
                                              args=(language, browser))
            process.start()
            processes.append(process)

    for process in processes:
        process.join()
