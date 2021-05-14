
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json


def process_browser_logs_for_network_events(logs):
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if (
            "Network.response" in log["method"]
            or "Network.request" in log["method"]
            or "Network.webSocket" in log["method"]
        ):
            yield log

def load_browser():
  capabilities = DesiredCapabilities.CHROME
  capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
  chrome_options = Options()
  chrome_options.add_argument("--window-size=1920,1080")
  driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options, desired_capabilities=capabilities)
  return driver


def get_browser_url_logs(driver):
    urls = []
    logs = driver.get_log("performance")
    events = process_browser_logs_for_network_events(logs)
    for event in events:
      try:
        urls.append(event["params"]["request"]["url"])
      except:
        pass
    return urls