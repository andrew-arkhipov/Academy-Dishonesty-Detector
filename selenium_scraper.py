from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time


COURSES = ["2613530", "2617873", "2617884", "2617896", "2617902", "2617909", "2617919", "2617929", "2617934"\
           "2617940", "2617947", "2617951", "2617962", "2617975", "2617985", "2617987", "2618002", "2618012"\
           "2618022", "2618030", "2618039", "2618053", "2618057", "2618062", "2618068", "2618075", "2618085"]


def read_credentials(filename):
    credentials = json.load(open(filename))
    print("Using credentials for", credentials['username'])

    return credentials['username'], credentials['password']


def init_driver(credentials):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--window-size=1420, 1080')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-gpu')

    print('Initializing Chrome driver...')

    driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
    driver.get("https://onramps.instructure.com")
    username = driver.find_element_by_name("j_username")
    username.send_keys(credentials[0])
    password = driver.find_element_by_name("j_password")
    password.send_keys(credentials[1])
    submit = driver.find_element_by_xpath("//input[@type='submit']")
    submit.click()

    print('Successfully logged in!')

    return driver


def get_assignments(driver, course):
    driver.get("https://onramps.instructure.com/courses/" + course + "/assignments")
    data = driver.page_source
    soup = BeautifulSoup(data, "html.parser")
    scripts = soup.find_all("script")
    uncleaned = scripts[4].get_text()[4396:5259]

    print('Getting assignments...')

    assignments = []
    temp = ""
    for i in range(1, 863):
        if uncleaned[i].isnumeric():
            temp += uncleaned[i]
        elif uncleaned[i-1].isnumeric():
            assignments.append(temp)
            temp = ""

    return assignments


def is_exam(driver, assignment, course):
    driver.get("https://onramps.instructure.com/courses/" + course + "/assignments/" + assignment)
    data = driver.page_source
    soup = BeautifulSoup(data, "html.parser")
    title = [title for title in soup.find_all("title")][0]

    if "Canvas Exam Unit 4B" == title.get_text()[0:19]:
        return True, title.get_text()
    else:
        return False, None


def get_log(driver):
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "speedgrader_iframe")))
    except:
        return driver, [], ""

    driver.switch_to.frame(driver.find_element_by_id("speedgrader_iframe"))
    log_link = driver.find_elements_by_xpath("//a[@href]")[5].get_attribute("href")

    driver.get(log_link)
    time.sleep(1.5)

    '''
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "ic-Icon icon-empty")))
    except TimeoutError:
        return driver, [], "null"
    '''

    logs = driver.find_elements_by_tag_name("li")

    name = ""
    potential = []

    for i, log in enumerate(logs):
        if i == 13:
            name = log.text
        if log.text[5:12] == 'Stopped' or log.text[5:12] == 'Resumed':
            potential.append(log.text[:5])

    driver.back()
    print('Successfully scraped log!')

    return driver, potential, name


def is_cheating(times):
    seconds = []
    for timestamp in times:
        seconds.append(int(timestamp[:2]) * 60 + int(timestamp[3:]))

    flag = False
    for i in range(1, len(times), 2):
        if seconds[i] - seconds[i-1] > 20:
            flag = True
            break

    return flag


def main():
    credentials = read_credentials("credentials.json")
    driver = init_driver(credentials)

    f = open('names.txt', 'w')

    for course in COURSES[1:]:
        assignments = get_assignments(driver, course)

        canvas_exams = {}
        print('Testing assignments for criteria...')

        for assignment in assignments:
            flag, title = is_exam(driver, assignment, course)
            if flag:
                canvas_exams[assignment] = title

        for exam in canvas_exams.keys():
            driver.get(
                "https://onramps.instructure.com/courses/" + course + "/gradebook/speed_grader?assignment_id=" + exam)
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "speedgrader_iframe")))
            except TimeoutError:
                continue

            num_students = driver.find_elements_by_id("x_of_x_students_frd")
            print(num_students[0].text[2:] + ' students detected.')

            no_log_count = 0
            for i in range(int(num_students[0].text[2:])):
                driver, times, name = get_log(driver)
                if name != 'Home':
                    print('Testing', name + '...')
                else:
                    print('Action log not detected.')

                '''
                if not times:
                    no_log_count += 1
                if no_log_count == 5:
                    break
                '''

                if is_cheating(times):
                    print(name + ' detected.')
                    f.write(name + ", " + canvas_exams[exam][0:19] + "\n")

                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "speedgrader_iframe")))
                except:
                    pass

                driver.find_element_by_id("next-student-button").click()

            print('Finished exam! Moving onto the next course...')

    f.close()


main()
