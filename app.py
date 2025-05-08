import os
import sys
from threading import Thread
from time import sleep

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Button,
    Checkbox,
    Input,
    DataTable,
    ListView,
    ListItem,
    Static,
    ProgressBar,
    Label,
)
from textual.reactive import reactive
from textual import work
from itertools import cycle

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LectureAutomationApp(App):
    """A Textual app for automating online lectures."""

    TITLE = "EX 강의 자동화 도구"
    BINDINGS = [
        ("d", "toggle_dark", "다크모드"),
        ("q", "quit", "종료"),
        ("r", "refresh_lectures", "강의 새로고침"),
    ]

    # Reactive state
    lecture_list = reactive([])
    is_connected = reactive(False)
    is_running = reactive(False)
    progress = reactive(0.0)
    status = reactive("대기 중")
    selected_lecture_index = reactive(-1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # Login section
        yield Static("로그인", classes="section-title")
        Inputs = Container(
            Input(placeholder="ex사번", id="username"),
            Input(placeholder="비밀번호", id="password", password=True),
            Checkbox("브라우저 보기", id="headless_mode", value=False),
        )
        Buttons = Container(
            Button("로그인", id="login", variant="primary"),
            Button("로그아웃", id="logout", variant="error"),
        )
        # 로그인 섹션
        Login_Container = Horizontal(
            Inputs,
            Buttons,
            id="login_container",
        )
        yield Login_Container

        # 강의 목록 섹션
        lms_container = DataTable(id="lms_table")
        lms_container.add_columns(
            "번호", "강의명", "수강기간", "강의시간", "수료상태"
        )

        LMS_buttons = Container(
            Button(
                "강의 시작",
                id="start_lecture",
                variant="success",
                disabled=True,
            ),
            Button("중지", id="stop_lecture", variant="error", disabled=True),
        )

        LMS_Section = Horizontal(lms_container, LMS_buttons)

        yield LMS_Section

        # Progress section
        yield Container(
            Static("진행 상태", classes="section-title"),
            ProgressBar(id="lecture_progress", total=100),
            id="progress_container",
        )

        # Status display
        yield Container(
            Static("현재 상태:", id="status_label"),
            Static("대기 중", id="status_value"),
            id="status_container",
        )

        yield Footer()

    def on_mount(self) -> None:
        """Actions to perform when the app is mounted."""
        table = self.query_one("#lms_table")
        table.cursor_type = "row"
        table.zebra_stripes = True
        self.add_class("app")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def watch_status(self, status: str) -> None:
        """Watch the status reactive variable and update the display."""
        self.query_one("#status_value").update(status)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "login":
            self.test_connection()
        elif button_id == "start_lecture":
            self.start_lecture()
        elif button_id == "stop_lecture":
            self.stop_lecture()

    def setup_driver(self, headless=True):
        """Setup Selenium web driver for Edge browser."""
        self.status = "드라이버 설정 중..."

        edge_options = Options()
        if headless:
            edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-notifications")
        edge_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        )

        # Platform detection
        if sys.platform == "darwin":  # macOS
            edge_bin_path = r"/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
            driver_path = os.path.join(
                os.getenv("HOME"), ".local/bin/msedgedriver"
            )
        else:  # Windows
            edge_bin_path = (
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            )
            driver_path = os.path.join(
                os.getenv("USERPROFILE"), ".local", "driver", "msedgedriver.exe"
            )

        edge_options.binary_location = edge_bin_path

        service = Service(driver_path)
        try:
            driver = webdriver.Edge(service=service, options=edge_options)
            return driver
        except Exception as e:
            self.notify(f"드라이버 설정 오류: {str(e)}", severity="error")
            self.status = "드라이버 설정 실패"
            return None

    @work
    async def test_connection(self) -> None:
        """Test connection to the lecture site using Selenium."""
        # Get login information
        username = self.query_one("#username").value
        password = self.query_one("#password").value
        show_browser = self.query_one("#headless_mode").value

        if not username or not password:
            self.notify("아이디와 비밀번호를 모두 입력하세요", severity="error")
            return

        self.status = "브라우저 실행 중..."

        # Setup the web driver in a separate thread to prevent UI blocking
        def setup_and_login():
            try:
                # Initialize the driver (headless mode is opposite of show_browser)
                self.driver = self.setup_driver(headless=(not show_browser))
                if not self.driver:
                    return

                # Go to the login page
                self.status = "사이트 접속 중..."
                self.driver.get("https://lc.multicampus.com/ex/?#/home")
                sleep(2)
                # Login
                self.status = "로그인 중..."
                try:
                    id_input = self.driver.find_element(
                        By.CSS_SELECTOR, "input[placeholder='ex사번']"
                    )
                    id_input.clear()
                    id_input.send_keys(username)

                    pwd_input = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "input[placeholder='비밀번호를 입력해 주세요.']",
                    )
                    pwd_input.clear()
                    pwd_input.send_keys(password)

                    login_btn = self.driver.find_element(
                        By.CSS_SELECTOR, "button[class='login-btn effect-1']"
                    )
                    login_btn.click()

                    # Wait for login to complete
                    sleep(2)

                    # Check if login successful
                    try:
                        # Go to learning management page
                        self.status = "나의 학습 페이지 접속 중..."
                        self.driver.get(
                            "https://lc.multicampus.com/ex/?#/me/lms"
                        )
                        sleep(2)

                        # Get lecture list
                        self.status = "강의 목록 가져오는 중..."
                        self.fetch_lectures()

                        # Mark as connected
                        self.status = "접속 완료"
                        self.is_connected = True
                        self.app.call_from_thread(
                            self.notify, "접속 성공!", severity="success"
                        )
                        self.app.call_from_thread(
                            lambda: setattr(
                                self.query_one("#start_lecture"),
                                "disabled",
                                False,
                            )
                        )
                    except WebDriverException:
                        self.status = "나의 학습 페이지 접속 실패"
                        self.app.call_from_thread(
                            self.notify,
                            "나의 학습 페이지를 찾을 수 없습니다.",
                            severity="error",
                        )
                except Exception as e:
                    self.status = "로그인 실패"
                    self.app.call_from_thread(
                        self.notify, f"로그인 실패: {str(e)}", severity="error"
                    )
            except Exception as e:
                self.status = "접속 오류"
                self.app.call_from_thread(
                    self.notify,
                    f"접속 중 오류 발생: {str(e)}",
                    severity="error",
                )

        # Run in a separate thread
        thread = Thread(target=setup_and_login)
        thread.daemon = True
        thread.start()

    def fetch_lectures(self):
        """Fetch lecture list from the website."""
        if not self.driver:
            return

        try:
            # Find lecture list
            article = self.driver.find_element(
                By.CSS_SELECTOR, "article[class='common-wrap']"
            )
            lms_items = article.find_elements(By.CSS_SELECTOR, "li")

            lecture_info = []
            for item in lms_items:
                text_lines = item.text.splitlines()
                title = text_lines[0]
                date_info = next(
                    (line for line in text_lines if "~" in line),
                    "기간 정보 없음",
                )
                lecture_time = next(
                    (
                        line
                        for line in text_lines
                        if "시간" in line and "~" not in line
                    ),
                    "시간 정보 없음",
                )
                status = "미수료" if "미수료" in item.text else "수료"

                lecture_info.append(
                    {
                        "title": title,
                        "date": date_info,
                        "time": lecture_time,
                        "status": status,
                        "element": item,
                    }
                )

            # Update the lecture list
            self.lecture_list = lecture_info

            # Update the data table on the UI thread
            def update_lecture_table():
                table = self.query_one("#lms_table")
                table.clear()

                for idx, lecture in enumerate(lecture_info):
                    table.add_row(
                        str(idx + 1),
                        lecture["title"],
                        lecture["date"],
                        lecture["time"],
                        lecture["status"],
                    )

            self.app.call_from_thread(update_lecture_table)

        except Exception as e:
            self.app.call_from_thread(
                self.notify,
                f"강의 목록 가져오기 실패: {str(e)}",
                severity="error",
            )

    def on_data_table_row_selected(self, event):
        """Handle data table row selection."""
        table = self.query_one("#lms_table")
        # if len(table.ordered_rows) > 0:
        # DataTable rows are 0-indexed
        # self.selected_lecture_index = event.cursor_row
        # if 0 <= self.selected_lecture_index < len(self.lecture_list):
        #     lecture = self.lecture_list[self.selected_lecture_index]
        #     self.notify(f"선택된 강의: {lecture['title']}")

    @work
    async def start_lecture(self) -> None:
        """Start the lecture automation."""
        if not self.is_connected or not self.driver:
            self.notify("먼저 접속 테스트를 진행하세요", severity="error")
            return

        if self.selected_lecture_index == -1:
            self.notify("먼저 강의를 선택하세요", severity="error")
            return

        self.is_running = True
        self.query_one("#start_lecture").disabled = True
        self.query_one("#stop_lecture").disabled = False

        # Start lecture in a thread
        def run_lecture():
            try:
                lecture = self.lecture_list[self.selected_lecture_index]
                self.status = f"강의 '{lecture['title']}' 시작 중..."

                # Click on the lecture to start
                lecture_element = lecture["element"]
                study_button = lecture_element.find_element(
                    By.XPATH, ".//button[contains(text(), '학습하기')]"
                )
                study_button.click()

                # Wait for the lecture to load
                sleep(5)

                # Switch to the new window if needed
                handles = self.driver.window_handles
                if len(handles) > 1:
                    self.driver.switch_to.window(handles[-1])

                self.status = "강의 진행 중..."

                # Simulate lecture progress
                for i in range(101):
                    if not self.is_running:
                        break

                    self.progress = i
                    self.app.call_from_thread(
                        lambda: self.query_one("#lecture_progress").update(
                            progress=i
                        )
                    )
                    sleep(1)  # Simulate time passing

                if self.progress >= 100:
                    self.status = "강의 완료"
                    self.app.call_from_thread(
                        self.notify,
                        f"'{lecture['title']}' 강의가 완료되었습니다!",
                        severity="success",
                    )
                    self.app.call_from_thread(self.refresh_lectures)

            except Exception as e:
                self.status = "강의 실행 오류"
                self.app.call_from_thread(
                    self.notify,
                    f"강의 실행 중 오류 발생: {str(e)}",
                    severity="error",
                )
            finally:
                self.is_running = False
                self.app.call_from_thread(
                    lambda: setattr(
                        self.query_one("#start_lecture"), "disabled", False
                    )
                )
                self.app.call_from_thread(
                    lambda: setattr(
                        self.query_one("#stop_lecture"), "disabled", True
                    )
                )

        # Run in a separate thread
        thread = Thread(target=run_lecture)
        thread.daemon = True
        thread.start()

    def stop_lecture(self) -> None:
        """Stop the lecture automation."""
        self.is_running = False
        self.status = "강의 중지됨"
        self.query_one("#start_lecture").disabled = False
        self.query_one("#stop_lecture").disabled = True
        self.notify("강의가 중지되었습니다", severity="warning")

    def action_refresh_lectures(self) -> None:
        """Refresh the lecture list."""
        if self.is_connected and self.driver:
            self.status = "강의 목록 새로고침 중..."

            def refresh():
                try:
                    self.driver.refresh()
                    sleep(2)
                    self.fetch_lectures()
                    self.status = "새로고침 완료"
                    self.app.call_from_thread(
                        self.notify,
                        "강의 목록이 새로고침 되었습니다.",
                        severity="success",
                    )
                except Exception as e:
                    self.status = "새로고침 실패"
                    self.app.call_from_thread(
                        self.notify,
                        f"새로고침 중 오류 발생: {str(e)}",
                        severity="error",
                    )

            thread = Thread(target=refresh)
            thread.daemon = True
            thread.start()
        else:
            self.notify("먼저 접속 테스트를 진행하세요", severity="error")

    def on_unmount(self) -> None:
        """Clean up resources when the app is closed."""
        if self.driver:
            self.driver.quit()


def run():
    """Run the application."""
    app = LectureAutomationApp()
    app.run()


if __name__ == "__main__":
    run()
