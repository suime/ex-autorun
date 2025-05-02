#!/usr/bin/env python3
"""
강의 자동 수강 셀레니움 CLI 앱
사용법: python course_automation.py --url [사이트URL] --id [아이디] --password [패스워드]
"""

import argparse
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


def parse_arguments():
    """커맨드 라인 인자 파싱"""
    parser = argparse.ArgumentParser(description="강의 자동 수강 셀레니움 CLI 앱")
    parser.add_argument("--url", required=True, help="강의 사이트 URL")
    parser.add_argument("--id", required=True, help="로그인 아이디")
    parser.add_argument("--password", required=True, help="로그인 패스워드")
    parser.add_argument("--headless", action="store_true", help="백그라운드 실행 모드")
    parser.add_argument(
        "--wait-time", type=int, default=5, help="각 페이지 로딩 대기 시간(초)"
    )
    return parser.parse_args()


def setup_driver(headless=False):
    """셀레니움 웹드라이버 설정"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")

    # 사용자 에이전트 설정
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    )

    # 웹드라이버 매니저를 통해 자동으로 크롬드라이버 설치 및 로드
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def login(driver, url, username, password, wait_time):
    """사이트에 로그인"""
    print(f"[+] {url}에 접속 중...")
    driver.get(url)

    try:
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("[+] 페이지 로드 완료")

        # 여기서는 일반적인 로그인 폼을 가정하지만, 실제 사이트의 HTML 구조에 맞게 수정 필요
        print("[+] 로그인 시도 중...")

        # ID 입력 필드 찾기 (이 부분은 실제 사이트의 HTML 구조에 맞게 수정 필요)
        # 일반적으로 많이 사용되는 id, name, class 속성 시도
        try:
            # id 필드 찾기 시도
            id_field = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "input[type='text'], input[type='email'], input[id*='id'], input[name*='id'], input[class*='id']",
                    )
                )
            )
        except TimeoutException:
            print("[!] 아이디 입력 필드를 찾을 수 없습니다.")
            print("[!] 로그인 페이지 HTML 구조 확인 후 스크립트를 수정해주세요.")
            return False

        id_field.clear()
        id_field.send_keys(username)
        print("[+] 아이디 입력 완료")

        # 비밀번호 입력 필드 찾기
        try:
            pw_field = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "input[type='password'], input[id*='pw'], input[name*='pw'], input[class*='pw']",
                    )
                )
            )
        except TimeoutException:
            print("[!] 비밀번호 입력 필드를 찾을 수 없습니다.")
            print("[!] 로그인 페이지 HTML 구조 확인 후 스크립트를 수정해주세요.")
            return False

        pw_field.clear()
        pw_field.send_keys(password)
        print("[+] 비밀번호 입력 완료")

        # 로그인 버튼 찾기
        try:
            login_button = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button[type='submit'], input[type='submit'], button[id*='login'], button[class*='login'], a[id*='login'], a[class*='login']",
                    )
                )
            )
        except TimeoutException:
            print("[!] 로그인 버튼을 찾을 수 없습니다.")
            print("[!] 로그인 페이지 HTML 구조 확인 후 스크립트를 수정해주세요.")
            return False

        login_button.click()
        print("[+] 로그인 버튼 클릭")

        # 로그인 성공 여부 확인 (이 부분도 사이트에 따라 수정 필요)
        # 예: 로그인 후 특정 요소가 나타나는지 확인
        try:
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".logged-in, .dashboard, .user-info")
                )
            )
            print("[+] 로그인 성공!")
            return True
        except TimeoutException:
            print("[!] 로그인 확인 실패. 로그인이 성공했는지 확인해주세요.")
            # 일단 계속 진행
            return True

    except Exception as e:
        print(f"[!] 로그인 중 오류 발생: {e}")
        return False


def find_courses(driver, wait_time):
    """강의 목록 찾기"""
    print("[+] 강의 목록을 찾는 중...")

    # 강의 목록 페이지로 이동하는 코드가 필요할 수 있음
    # 예: driver.get("https://example.com/courses")

    # 강의 목록을 찾는 코드 (사이트에 따라 수정 필요)
    try:
        # 일반적인 강의 링크 탐색
        course_links = WebDriverWait(driver, wait_time).until(
            EC.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "a[href*='course'], a[href*='lecture'], .course-item, .lecture-item",
                )
            )
        )

        if not course_links:
            print("[!] 강의 목록을 찾을 수 없습니다.")
            return []

        print(f"[+] {len(course_links)}개의 강의를 찾았습니다.")
        return course_links
    except TimeoutException:
        print("[!] 강의 목록을 찾을 수 없습니다.")
        return []
    except Exception as e:
        print(f"[!] 강의 목록을 찾는 중 오류 발생: {e}")
        return []


def attend_course(driver, course, wait_time):
    """강의 수강"""
    try:
        print(f"[+] 강의 수강 시작: {course.text}")
        course.click()

        # 강의 영상 페이지가 로드될 때까지 대기
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 비디오 플레이어 찾기 (사이트에 따라 수정 필요)
        try:
            video_player = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "video, iframe[src*='video'], .video-player")
                )
            )
            print("[+] 비디오 플레이어를 찾았습니다.")

            # 재생 버튼 클릭 (필요한 경우)
            try:
                play_button = WebDriverWait(driver, wait_time).until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            ".play-button, .vjs-play-button, button[aria-label*='재생']",
                        )
                    )
                )
                play_button.click()
                print("[+] 재생 버튼을 클릭했습니다.")
            except:
                print("[!] 재생 버튼을 찾을 수 없거나 이미 재생 중입니다.")

            # 강의 시간만큼 대기 (예시: 10분)
            print("[+] 강의 수강 중...")
            lecture_time = 600  # 10분 (필요에 따라 조정)
            time.sleep(lecture_time)

            print("[+] 강의 수강 완료")

            # 뒤로 돌아가기
            driver.back()
            time.sleep(2)  # 페이지 로드 대기

            return True
        except TimeoutException:
            print("[!] 비디오 플레이어를 찾을 수 없습니다.")
            driver.back()
            return False

    except Exception as e:
        print(f"[!] 강의 수강 중 오류 발생: {e}")
        return False


def main():
    """메인 함수"""
    args = parse_arguments()

    driver = setup_driver(args.headless)

    try:
        # 로그인
        login_success = login(driver, args.url, args.id, args.password, args.wait_time)
        if not login_success:
            print("[!] 로그인에 실패했습니다. 프로그램을 종료합니다.")
            driver.quit()
            sys.exit(1)

        # 강의 목록 찾기
        courses = find_courses(driver, args.wait_time)
        if not courses:
            print("[!] 강의 목록을 찾을 수 없습니다. 프로그램을 종료합니다.")
            driver.quit()
            sys.exit(1)

        # 각 강의 수강
        completed_courses = 0
        for course in courses:
            if attend_course(driver, course, args.wait_time):
                completed_courses += 1

        print(f"[+] 총 {len(courses)}개 강의 중 {completed_courses}개 수강 완료")

    except KeyboardInterrupt:
        print("\n[!] 사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"[!] 예기치 않은 오류 발생: {e}")
    finally:
        print("[+] 브라우저를 종료합니다.")
        driver.quit()


if __name__ == "__main__":
    main()
