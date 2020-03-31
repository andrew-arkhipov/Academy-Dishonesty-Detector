from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time


COURSES = ["2613530", "2617873", "2617884", "2617896", "2617902", "2617909", "2617919", "2617929", "2617934"\
           "2617940", "2617947", "2617951", "2617962", "2617975", "2617985", "2617987", "2618002", "2618012"\
           "2618022", "2618030", "2618039", "2618053", "2618057", "2618062", "2618068", "2618075", "2618085"]


def read_credentials(filename):
    credentials = json.load(open(filename))

    return credentials['username'], credentials['password']


def init_driver(credentials):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get("https://onramps.instructure.com")
    username = driver.find_element_by_name("j_username")
    username.send_keys(credentials[0])
    password = driver.find_element_by_name("j_password")
    password.send_keys(credentials[1])
    submit = driver.find_element_by_xpath("//input[@type='submit']")
    submit.click()

    return driver


def get_assignments(driver, course):
    driver.get("https://onramps.instructure.com/courses/" + course + "/assignments")
    data = driver.page_source
    soup = BeautifulSoup(data, "html.parser")
    scripts = soup.find_all("script")
    uncleaned = scripts[4].get_text()[4396:5259]

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

    return "Canvas Exam" == title.get_text()[0:11]


def get_log(driver):
    driver.switch_to.frame(driver.find_element_by_id("speedgrader_iframe"))
    log_link = driver.find_elements_by_xpath("//a[@href]")[5].get_attribute("href")

    driver.get(log_link)
    time.sleep(1.2)

    logs = driver.find_elements_by_tag_name("li")

    name = ""
    potential = []

    for i, log in enumerate(logs):
        if i == 13:
            name = log.text
        if log.text[5:12] == 'Stopped' or log.text[5:12] == 'Resumed':
            potential.append(log.text[:5])

    driver.back()

    return driver, potential, name


def is_cheating(times):
    seconds = []
    for timestamp in times:
        seconds.append(int(timestamp[:2]) * 60 + int(timestamp[3:]))

    flag = False
    for i in range(1, len(times), 2):
        if seconds[i] - seconds[i-1] > 20:
            flag = True

    return flag


def main():
    credentials = read_credentials("credentials.json")
    driver = init_driver(credentials)

    f = open('names.txt', 'w')

    for course in COURSES[1:]:
        assignments = get_assignments(driver, course)

        canvas_exams = []
        for assignment in assignments:
            if is_exam(driver, assignment, course):
                canvas_exams.append(assignment)

        for exam in canvas_exams:
            driver.get(
                "https://onramps.instructure.com/courses/" + course + "/gradebook/speed_grader?assignment_id=" + exam)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "speedgrader_iframe")))
            except TimeoutError:
                continue

            num_students = driver.find_elements_by_id("x_of_x_students_frd")
            print(num_students[0].text)

            for i in range(int(num_students[0].text[3:])):
                driver, times, name = get_log(driver)
                if is_cheating(times):
                    f.write(name + "\n")

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "speedgrader_iframe")))
                driver.find_element_by_id("next-student-button").click()

    f.close()


if __name__ == '__main__':
    main()
