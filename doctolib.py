

import json, math, time, pprint, threading, requests, datetime, queue, os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import winsound
import signal
import sys

import browsing

filters = ["1re injection", "5494"]

booking_filters = [["1re injection", "5494", "Pfizer"], ["1re injection", "5494", "Moderna"]]

stop_waiting_dose_selection = False
signal_started = False

def signal_handler(sig, frame):
    global stop_waiting_dose_selection
    print('You pressed Ctrl+C!')
    stop_waiting_dose_selection = True

class Scraper (threading.Thread):
  def __init__(self, center, results_queue):
    threading.Thread.__init__(self)
    self.center = center
    self.previous_availabilities = []
    self.results_queue = results_queue
    self.pause = False
    print("Thread scraper for {} is ready".format(center["scraping_url"]))
   
  def pause_thread(self):
    print("Pause scraper {}".format(self.center["center_name"]))
    self.pause = True
  
  def resume_thread(self):
    print("Resume scraper {}".format(self.center["center_name"]))
    self.pause = False

  def run(self):
    url = self.center["scraping_url"]
    while 1:
      while self.pause:
        time.sleep(.5)
      now = datetime.datetime.now()
      chronodose_limit = (now + datetime.timedelta(hours=48)).replace(hour=23, minute=59)
      # print(url.format(now.strftime("%y-%m-%d")))

      # if os.getenv("DEBUG", '0') == '1':
      #   reply = {"availabilities":[{"date":"2021-05-19","slots":["2021-05-19T11:15:00.000+02:00","2021-05-19T11:30:00.000+02:00","2021-05-19T11:45:00.000+02:00","2021-05-19T12:00:00.000+02:00","2021-05-19T12:15:00.000+02:00","2021-05-19T12:30:00.000+02:00","2021-05-19T12:45:00.000+02:00"],"substitution":None},{"date":"2021-05-20","slots":[],"substitution":None},{"date":"2021-05-21","slots":["2021-05-21T12:00:00.000+02:00","2021-05-21T15:00:00.000+02:00","2021-05-21T15:15:00.000+02:00","2021-05-21T15:30:00.000+02:00","2021-05-21T15:45:00.000+02:00","2021-05-21T16:00:00.000+02:00","2021-05-21T16:15:00.000+02:00","2021-05-21T16:30:00.000+02:00","2021-05-21T16:45:00.000+02:00","2021-05-21T17:00:00.000+02:00","2021-05-21T17:15:00.000+02:00","2021-05-21T17:45:00.000+02:00","2021-05-21T18:45:00.000+02:00"],"substitution":None},{"date":"2021-05-22","slots":[],"substitution":None}],"total":20}
      # else:
      response = requests.get(url.format(now.strftime("%y-%m-%d")))
      reply = response.json()
      
      print("Checks doses for {}".format(self.center["center_name"]))

      if reply["availabilities"] and reply["availabilities"] != self.previous_availabilities:
        for availability in reply["availabilities"]:
          if availability["slots"]:
            date = datetime.datetime.now()
            date = date.replace(month=int(availability["date"][5:7]), day=int(availability["date"][8:10]))
            if date < chronodose_limit:
              print("Found doses on {} in {}".format(date, self.center["center_name"]))
              self.results_queue.put(self.center)
              self.previous_availabilities = reply["availabilities"]
              break
      
      time.sleep(.5)


class DoseFoundAlerter (threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.center = {}
    self.stop_flag = True
    self.quit = False
   
  def stop_ringing(self):
    self.stop_flag = True

  def start_ringing(self, center):
    self.center = center
    self.stop_flag = False

  def exit(self):
    self.quit = True

  def run(self):
    while not self.quit:
      if not self.stop_flag:
        winsound.PlaySound('alert.mp3', winsound.SND_FILENAME | winsound.SND_ASYNC)
      time.sleep(.5)

def process_browser_logs_for_network_events(logs):
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if (
            "Network.response" in log["method"]
            or "Network.request" in log["method"]
            or "Network.webSocket" in log["method"]
        ):
            yield log

def extract_scraping_url_from_browser(driver):
  urls = []
  logs = driver.get_log("performance")
  events = process_browser_logs_for_network_events(logs)
  for event in events:
    try:
      urls.append(event["params"]["request"]["url"])
    except:
      pass
  return urls

def login_to_doctolib(driver, username, password):
  driver.get("https://www.doctolib.fr/sessions/new")


  username_field = driver.find_element_by_id("username")

  username_field.send_keys(username)
  actions = ActionChains(driver) 
  actions = actions.send_keys(Keys.TAB)
  actions.perform()
  actions = ActionChains(driver) 
  actions = actions.send_keys(password)
  actions.perform()
  login_button = driver.find_element_by_class_name("dl-button-DEPRECATED_yellow")
  login_button.click()

def open_center_and_get_scraping_url(driver, center):
  try:
    driver.get(center["center_link"])
    WebDriverWait(driver,3).until(EC.presence_of_element_located((By.ID, "booking_motive")))
    booking_motive_selector = driver.find_element_by_id("booking_motive")

    now = datetime.datetime.now().strftime("%y-%m-%d")

    for booking_motive in booking_motive_selector.find_elements_by_tag_name("option"):
      i = 0
      for filter in filters:
        if filter in booking_motive.get_attribute("value"):
          i+= 1
        if i == len(filters):
          booking_motive.click()
          WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "booking-availabilities")))
          urls = extract_scraping_url_from_browser(driver)
          urls.reverse()
          scraping_url = ""
          for url in urls:
            if "availabilities.json" in url:
              scraping_url = url
              break
          center["scraping_url"] = scraping_url.replace(now, "{}")
          return center
  except:
    return False
  return False


def get_centers_scraping_urls(driver, centers):
  for center in centers:
    center = open_center_and_get_scraping_url(driver, center)
  return centers



def get_centers(driver, base_city="Rennes", max_km=100, user_position=(48.113308097376766, -1.6840329418658475)):
  driver.get(f'https://www.doctolib.fr/vaccination-covid-19/{base_city.lower()}?ref_visit_motive_ids[]=6970&ref_visit_motive_ids[]=7005&force_max_limit=2')
  WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "dl-search-result")))

  vaccination_centers_parsed = []

  is_last_page = False

  while not is_last_page:

    vaccination_centers = driver.find_elements_by_class_name("dl-search-result")


    for vaccination_center in vaccination_centers:
      hover = ActionChains(driver).move_to_element(vaccination_center)
      hover.perform()
      WebDriverWait(vaccination_center,10).until(EC.presence_of_element_located((By.CLASS_NAME, "availabilities-slots")))
      center_name = vaccination_center.find_element_by_class_name("dl-search-result-title").find_element_by_tag_name("div").text
      center_lat = float(vaccination_center.get_attribute("data-lat"))
      center_long = float(vaccination_center.get_attribute("data-lng"))
      center_link = vaccination_center.find_element_by_class_name("dl-search-result-name").get_attribute("href")

      vaccination_center_search_result_id = vaccination_center.get_attribute("id").split("-")[-1]


      R = 6373.0


      lat2 = math.radians(center_lat)
      lon2 = math.radians(center_long)


      user_lat = math.radians(user_position[0])
      user_long = math.radians(user_position[1])

      dlon = lon2 - user_long
      dlat = lat2 - user_lat
      a = math.sin(dlat / 2)**2 + math.cos(user_lat) * math.cos(user_long) * math.sin(dlon / 2)**2
      c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
      distance = R * c

      if distance < max_km:
        print("Select center {}, at {}km".format(center_name, distance))
        vaccination_centers_parsed.append({
          "distance": distance,
          "center_name": center_name,
          "center_geoloc": (center_lat, center_long),
          "center_link": center_link,
          "vaccination_center_search_result_id": vaccination_center_search_result_id
        })
      else:
        print("Center {} too far".format(center_name))

    if os.getenv("DEBUG", '0') == '1':
      break

    next_button = driver.find_element_by_class_name("next")
    try:
      if next_button.find_element_by_tag_name("span").get_attribute("class") != "disabled":
        next_button.click()
        time.sleep(1)
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "dl-search-result")))
      else:
        is_last_page = True
    except:
      next_button.click()
      time.sleep(1)
      WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "dl-search-result")))
  

  vaccination_centers_parsed = get_centers_scraping_urls(driver, vaccination_centers_parsed)

  return vaccination_centers_parsed

def pause_all_scrapers(threads):
  for thread in threads:
    thread.pause_thread()


def resume_all_scrapers(threads):
  for thread in threads:
    thread.resume_thread()

def open_appointment(driver, center):
  driver.get(center["center_link"])
  WebDriverWait(driver,10).until(EC.presence_of_element_located((By.ID, "booking_motive")))

  booking_motive_selector = driver.find_element_by_id("booking_motive")
  for booking_motive in booking_motive_selector.find_elements_by_tag_name("option"):
    i = 0
    for booking_filter in booking_filters:
      for filter in booking_filter:
        if filter in booking_motive.get_attribute("value"):
          i+= 1
        if i == len(booking_filter):
          WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "booking-availabilities")))
          print(booking_motive.get_attribute("value"))
          booking_motive.click()
          return


def start_all_centers_scraping(vaccination_centers):
  threads = []
  q = queue.Queue()
  for center in vaccination_centers:
    if center:
      new_scraper = Scraper(center, q)
      new_scraper.start()
      threads.append(new_scraper)
      if os.getenv("DEBUG", '0') == '1':
        break #DEBUG
  return threads, q
