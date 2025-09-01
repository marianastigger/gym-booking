import os.path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

ACCOUNT_EMAIL = os.environ.get("GYM_EMAIL")
ACCOUNT_PASSWORD = os.environ.get("GYM_PASSWORD")
GYM_URL = "https://appbrewery.github.io/gym/"

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

classes_booked = 0
waitlists_joined = 0
already_booked = 0
detailed_list = []

my_bookings = 0

classes_available = []

class_found = False


def retry(func, retries=7):
    if retries >= 7:
        print("Maximum number of retries achieved.")
        return
    else:
        func(retries=retries + 1)


def login(retries=0):
    email = ACCOUNT_EMAIL
    password = ACCOUNT_PASSWORD
    url = GYM_URL

    browser = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(browser, timeout=3)
    browser.get(url)

    login_button = wait.until(
        EC.presence_of_element_located((By.ID, "login-button"))
    )
    login_button.click()

    email_input = wait.until(
        EC.presence_of_element_located((By.ID, "email-input"))
    )
    email_input.send_keys(email)

    password_input = wait.until(
        EC.presence_of_element_located((By.ID, "password-input"))
    )
    password_input.send_keys(password)

    submit_button = wait.until(
        EC.presence_of_element_located((By.ID, "submit-button"))
    )
    submit_button.click()

    print(f"Trying login. Attempt: {retries + 1}/7.")
    try:
        wait.until(
            EC.presence_of_element_located((By.ID, "error-message"))
        )
        browser.quit()
        retry(login, retries)
    except (NoSuchElementException, TimeoutException):
        print("Login successful.")
        book_class(wait=wait, browser=browser)


def book_class(wait, browser):
    global classes_booked, waitlists_joined, already_booked, my_bookings, class_found

    try:
        tuesday_classes = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='day-group-tue']"))
        )
        classes_available.append(tuesday_classes)
    except (NoSuchElementException, TimeoutException):
        pass

    try:
        thursday_classes = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='day-group-thu']"))
        )
        classes_available.append(thursday_classes)
    except (NoSuchElementException, TimeoutException):
        pass

    classes_hours = []

    for available_class in classes_available:
        classes_hours.append(available_class.find_elements(By.CSS_SELECTOR, "p[id^='class-time']"))
    class_hour = "6:00 PM"

    all_classes = []

    for day_classes in classes_hours:
        for hour in day_classes:
            if hour.text == f"Time: {class_hour}":
                chosen_class = hour.find_element(By.XPATH, "..")
                class_name = chosen_class.find_element(By.CSS_SELECTOR, "h3[id^='class-name']").text
                class_date = chosen_class.find_element(By.XPATH, "../../..").text.split("\n")[0]

                class_button = chosen_class.find_element(By.XPATH, "..")
                join_button = class_button.find_element(By.CSS_SELECTOR, "button[id^=book-button]")

                if join_button.text == "Booked":
                    already_booked += 1
                    my_bookings += 1
                    all_classes.append(f"{class_name}")
                    print(f"✅ Already booked: {class_name} on {class_date} at {class_hour}.")
                elif join_button.text == "Waitlisted":
                    already_booked += 1
                    my_bookings += 1
                    all_classes.append(f"{class_name} (Waitlist)")
                    print(f"✅ Already on waitlist: {class_name} on {class_date} at {class_hour}.")
                elif join_button.text == "Join Waitlist":
                    join_button.click()
                    waitlists_joined += 1
                    my_bookings += 1
                    detailed_list.append(f"• [New Waitlist] {class_name} on {class_date}.")
                    all_classes.append(f"{class_name} (Waitlist)")
                    print(f"✅ Joined waitlist for: {class_name} on {class_date} at {class_hour}.")
                elif join_button.text == "Book Class":
                    join_button.click()
                    classes_booked += 1
                    my_bookings += 1
                    detailed_list.append(f"• [New Booking] {class_name} on {class_date}.")
                    all_classes.append(f"{class_name}")
                    print(f"✅ Successfully booked: {class_name} on {class_date} at {class_hour}.")

                class_found = True

    if not class_found:
        print("No class found for desired day and hour.")

    print(f"\n--- BOOKING SUMMARY ---"
          f"\nClasses booked: {classes_booked}"
          f"\nWaitlists joined: {waitlists_joined}"
          f"\nClasses already booked/waitlisted: {already_booked}"
          f"\nTotal Tuesday & Thursday {class_hour} classes processed: "
          f"{classes_booked + waitlists_joined + already_booked}")

    if detailed_list:
        print(f"\n--- DETAILED CLASS LIST ---")
        for action in detailed_list:
            print(f"{action}")

    get_my_bookings(wait, browser, all_classes)


def get_my_bookings(wait, browser, all_classes):
    my_bookings_button = browser.find_element(By.ID, "my-bookings-link")
    my_bookings_button.click()

    print(f"\n--- VERIFYING ON MY BOOKINGS PAGE ---")
    for current_class in all_classes:
        try:
            wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'class-name')]"))
            )
            print(f"✅ Verified: {current_class}")
        except (NoSuchElementException, TimeoutException):
            print(f"❌ Error: No {current_class} found on My Bookings page")

    bookings_section = browser.find_elements(
        By.CSS_SELECTOR,
        "#confirmed-bookings-section [id^='booking-card']"
    )
    num_bookings = len(bookings_section)

    waitlist_section = browser.find_elements(
        By.CSS_SELECTOR,
        "#waitlist-section [id^='waitlist-card']"
    )
    num_waitlist = len(waitlist_section)

    print(f"\n--- VERIFICATION RESULT ---"
          f"\nExpected: {my_bookings} bookings"
          f"\nFound: {num_bookings + num_waitlist} bookings")
    if my_bookings == num_bookings + num_waitlist:
        print("✅ SUCCESS: All bookings verified!")
    else:
        print(f"❌ MISMATCH: Missing {num_bookings + num_waitlist - my_bookings} bookings")


login()
