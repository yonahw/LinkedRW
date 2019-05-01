import json
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10


def main():
    with open('config.json') as f:
        credentials = json.load(f)

    driver = webdriver.Chrome()
    driver.get('https://www.linkedin.com/login/')

    # Login to LinkedIn
    driver.find_element_by_id('username').send_keys(credentials['email'])
    driver.find_element_by_id('password').send_keys(credentials['password'])
    driver.find_element_by_class_name('login__form_action_container').submit()

    # Navigate to profile page
    driver.find_element(
        By.CSS_SELECTOR,
        '.tap-target.profile-rail-card__actor-link.block.link-without-hover-visited.ember-view').click()
    exp_section = WebDriverWait(driver, TIMEOUT).until(ec.presence_of_element_located((By.ID, 'oc-background-section')))

    summary = get_summary(driver)
    experience = get_experience(driver, exp_section)
    print(summary)
    print(json.dumps(experience, indent=4))

    driver.quit()


def get_summary(driver):
    # Check if summary section exists
    try:
        driver.find_element(
            By.CSS_SELECTOR, '.pv-top-card-section__summary.pv-top-card-section__summary--with-content.mt4.ember-view')
    except NoSuchElementException:
        return ''

    # Check if there is a show more button
    try:
        driver.find_element_by_class_name('pv-top-card-section__summary-toggle-button-icon').click()
    except NoSuchElementException:
        pass

    return driver.find_element(
        By.CSS_SELECTOR, '.pv-top-card-section__summary-text.text-align-left.mt4.ember-view').text


def get_experience(driver, exp_section):
    # Load experience section
    driver.execute_script("arguments[0].scrollIntoView(true);", exp_section)
    time.sleep(1)

    # Locate individual experiences
    exp_ul = exp_section.find_element(
        By.CSS_SELECTOR, '.pv-profile-section__section-info.section-info.pv-profile-section__section-info--has-no-more')
    exp_divs = exp_ul.find_elements(
        By.CSS_SELECTOR, '.pv-entity__position-group-pager.pv-profile-section__list-item.ember-view')
    exps = []

    for exp_div in exp_divs:
        try:
            exp_summary = exp_div.find_element(
                By.CSS_SELECTOR, '.pv-entity__summary-info.pv-entity__summary-info--background-section')
            exps.append(get_single_role(exp_div, exp_summary))
        except NoSuchElementException:
            exp_summary = exp_div.find_element_by_class_name('pv-entity__company-summary-info-v2')
            exps.append(get_multiple_roles(exp_div, exp_summary))

    return exps


def get_single_role(exp_div, exp_summary):
    title = exp_summary.find_element(By.CSS_SELECTOR, '.t-16.t-black.t-bold').text
    company = exp_summary.find_element_by_class_name('pv-entity__secondary-title').text
    dates = get_span_text(exp_summary, '.pv-entity__date-range.t-14.t-black--light.t-normal')
    location = get_experience_location(exp_summary)
    description = get_experience_description(exp_div)

    results = {
        'company': company,
        'roles': [{
            'title': title,
            'dates': dates,
            'location': location,
            'description': description
        }]
    }

    return results


def get_multiple_roles(exp_div, exp_summary):
    company = get_span_text(exp_summary, '.t-16.t-black.t-bold')

    # Show all roles
    try:
        exp_div.find_element_by_class_name('pv-profile-section__toggle-detail-icon').click()
        time.sleep(1)
    except NoSuchElementException:
        pass

    roles = []
    for role_section in exp_div.find_elements_by_class_name('pv-entity__position-group-role-item'):
        title = get_span_text(role_section, '.t-14.t-black.t-bold')
        dates = get_span_text(role_section, '.pv-entity__date-range.t-14.t-black.t-normal')
        location = get_experience_location(role_section)
        description = get_experience_description(role_section)

        roles.append({
            'title': title,
            'dates': dates,
            'location': location,
            'description': description
        })

    results = {
        'company': company,
        'roles': roles
    }

    return results


def get_span_text(element, name):
    return element.find_element(By.CSS_SELECTOR, name).find_elements_by_tag_name('span')[1].text.replace('–', '-')


def get_experience_location(element):
    try:
        return get_span_text(element, '.pv-entity__location.t-14.t-black--light.t-normal.block')
    except NoSuchElementException:
        return ''


def get_experience_description(element):
    try:
        description_section = element.find_element(
            By.CSS_SELECTOR, '.pv-entity__description.t-14.t-black.t-normal.ember-view')
        more_btn_section = description_section.find_element_by_class_name('lt-line-clamp__ellipsis')

        if 'lt-line-clamp__ellipsis--dummy' in more_btn_section.get_attribute('class'):
            description = description_section.text
        else:
            more_btn_section.find_element_by_class_name('lt-line-clamp__more').click()
            description = description_section.find_element_by_class_name('lt-line-clamp__raw-line').text
    except NoSuchElementException:
        description = ''

    return description


if __name__ == '__main__':
    main()
