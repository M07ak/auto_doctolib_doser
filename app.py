from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pathlib, json, time, os, signal, sys

import browsing, doctolib


# import v2.browsing as browsing, v2.doctolib as doctolib

path = pathlib.Path(__file__).parent.absolute()

with open("infos.json".format(path), 'r') as outfile:
  infos = json.load( outfile)

if infos["debug"] == 1:
  os.environ['DEBUG'] = "1"


driver = browsing.load_browser()

doctolib.login_to_doctolib(driver, infos["doctolib_username"], infos["doctolib_password"])
centers = doctolib.get_centers(driver, max_km=int(infos["max_distance"]), user_position=(float(infos["latitude"]), float(infos["longitude"])))
threads, q = doctolib.start_all_centers_scraping(centers)
alerter = doctolib.DoseFoundAlerter()
alerter.start()

paused = False

# def signal_handler(sig, frame):
#     global paused
#     if paused:
#       paused = False
#     else:
#       sys.exit(0)


# signal.signal(signal.SIGINT, signal_handler)

while 1:
  try:
    item = q.get_nowait()
    if item:
      paused = True
      print("-----")
      print(item)
      print("-------")
      print("FOUND DOSES IN QUEUE")
      doctolib.pause_all_scrapers(threads)
      doctolib.open_appointment(driver, item)
      alerter.start_ringing(item)
      input("Press Enter to continue...")
      alerter.stop_ringing()
      doctolib.resume_all_scrapers(threads)
  except:
    pass
  time.sleep(.01)