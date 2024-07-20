from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError
from tenacity import retry, stop_after_attempt, retry_if_exception_type
import urllib.parse
import re
from datetime import date, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HorseInfo:
    id: int
    name: str
    sex: str
    sire: str
    mare: str
    trainer: str
    stable_location: str
    prize_jra: int
    prize_nra: int
    race_records: str
    retired: bool

    @property
    def race_place_counts(self) -> list[int]:
        return [int(count) for count in self.race_records.split("-")]


@dataclass(frozen=True)
class HorseQueryResult:
    id: int
    name: str


@dataclass(frozen=True)
class RaceHorse:
    id: int
    name: str
    jockey: Optional[str] = None
    rank: Optional[str] = None


@dataclass(frozen=True)
class RaceInfo:
    name: str
    kaisai_no: str
    kaisai_day: str
    course: str
    race_no: str
    distance: str
    grade: Optional[str] = None


@dataclass(frozen=True)
class Race:
    info: RaceInfo
    horses: list[RaceHorse]


class Netkeiba:
    def __init__(self, timeout=5000):
        self.timeout = timeout

    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def get_all_shutuba_info(self) -> list[Race]:
        kaisai_list = self._get_kaisai_list()

        all_race_urls = []
        for kaisai_url in kaisai_list:
            race_urls = self._get_race_list(kaisai_url, page_type="shutuba")
            all_race_urls.extend(race_urls)

        all_races = []
        for race_url in all_race_urls:
            print(race_url)
            race = self._get_shutuba_info(race_url)
            print(race.info)
            all_races.append(race)

        return all_races

    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def get_all_result_info(self) -> list[Race]:
        kaisai_list = self._get_kaisai_list()

        all_race_urls = []
        for kaisai_url in kaisai_list:
            race_urls = self._get_race_list(kaisai_url, page_type="result")
            all_race_urls.extend(race_urls)

        all_races = []
        for race_url in all_race_urls:
            print(race_url)
            race = self._get_result_info(race_url)
            print(race.info)
            all_races.append(race)

        return all_races

    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def get_horse_info(self, horse_id: str) -> HorseInfo:
        horse_url = f"https://db.sp.netkeiba.com/horse/{horse_id}"

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(horse_url, timeout=self.timeout)

            name = page.locator("div.Name > h1").text_content().strip()
            sire = page.locator("table#DetailTable > tbody > tr > td.Sire").text_content().strip()
            mare = page.locator("table#DetailTable > tbody > tr > td.Dam").text_content().strip().split("\n")[0]

            rows = page.locator("table#DetailTable > tbody > tr")
            for i in range(rows.count()):
                if rows.nth(i).locator("th").text_content() == "調教師":
                    trainer_and_location = rows.nth(i).locator("td").text_content().strip()
                    if trainer_and_location == "-":
                        stable_location = ""
                        trainer = ""
                    else:
                        stable_location, trainer = trainer_and_location.split("\n")
                elif rows.nth(i).locator("th").text_content() == "中央獲得賞金":
                    prize_jra = self._parse_prize_text(rows.nth(i).locator("td").text_content().strip())
                elif rows.nth(i).locator("th").text_content() == "地方獲得賞金":
                    prize_nra = self._parse_prize_text(rows.nth(i).locator("td").text_content().strip())

            if page.is_visible("div.NoData"):
                race_records = "0-0-0-0"
            else:
                rows = page.locator("div.ResultsDetail > table > tbody > tr")
                results = rows.nth(0).locator("td").text_content()
                m = re.search(r'\[\d+-\d+-\d+-\d+\]', results)
                race_records = m.group().lstrip("[").rstrip("]")

            spans = page.locator("div.Data > span")
            sex_age = spans.nth(1).text_content()
            if "牡" in sex_age:
                sex = "牡"
            elif "牝" in sex_age:
                sex = "牝"
            elif "セ" in sex_age:
                sex = "セ"

            labels = page.locator("div.Data > span.label")
            labels = [labels.nth(i).text_content() for i in range(labels.count())]
            if "抹消" in labels or "繁殖" in labels:
                retired = True
            else:
                retired = False

            horse_info = HorseInfo(horse_id, name, sex, sire, mare, trainer,
                                   stable_location, prize_jra, prize_nra,
                                   race_records, retired)
            context.close()
            browser.close()
        return horse_info

    def _parse_prize_text(self, prize_text: str) -> int:
        if "億" in prize_text:
            prize_text = prize_text.replace("億円", "億0万円")
            n_hundred_million = int(prize_text.split("億")[0])
            rest = int(prize_text.split("億")[1].replace("万円", "").replace(",", ""))
            prize = n_hundred_million * 10000 + rest
        else:
            prize = int(prize_text.replace("万円", "").replace(",", ""))
        return prize

    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def query_horse_by_mare(self, mare_name: str, under_age: int = 2, over_age: int = 3) -> list[HorseQueryResult]:
        query_results = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()

            encoded_name = urllib.parse.quote(mare_name, encoding="euc-jp")
            query_url = f"https://db.sp.netkeiba.com/?pid=horse_list&word=&match=partial_match&mare={encoded_name}&under_age={under_age}&over_age={over_age}&sort=birthyear&submit="
            page.goto(query_url, timeout=self.timeout)

            loc_links = page.locator("ul.BreederList > li > a")
            for i in range(loc_links.count()):
                url = loc_links.nth(i).get_attribute("href")
                m = re.search(r"\d\d\d\d\d\d\d\d\d\d", url)
                netkeiba_id = int(m.group())
                name = loc_links.nth(i).get_attribute("title")
                query_results.append(HorseQueryResult(netkeiba_id, name))

            context.close()
            browser.close()
        return query_results

    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def _get_kaisai_list(self) -> list[str]:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://race.netkeiba.com/top/race_list.html', timeout=self.timeout)

            kaisai_links = page.locator('a.ui-tabs-anchor')
            kaisai_urls = []
            for i in range(kaisai_links.count()):
                url = "https://race.netkeiba.com/top/" + kaisai_links.nth(i).get_attribute("href")
                kaisai_urls.append(url)

            context.close()
            browser.close()
        return kaisai_urls

    def _filter_kaisai_urls(self, urls: list[str], date_from: date, date_to: date | None) -> list[str]:
        if date_to is None:
            date_to = date_from + timedelta(year=1)
        from_as_number = int(str(date_from).replace("-", ""))
        to_as_number = int(str(date_to).replace("-", ""))

        def extract_date(url):
            return int(re.search(r"\d\d\d\d\d\d\d\d", url).group())

        return list(filter(lambda x: from_as_number <= extract_date(x) <= to_as_number, urls))


    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def _get_race_list(self, race_list_url: str, page_type: str = "shutuba") -> list[str]:
        assert page_type in ("shutuba", "result")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(race_list_url, timeout=self.timeout)

            race_links = page.locator('li.RaceList_DataItem > a')
            race_urls = []

            for i in range(race_links.count()):
                url = race_links.nth(i).get_attribute("href")
                if f"{page_type}.html" in url:
                    race_urls.append(url)

            context.close()
            browser.close()

        race_urls = ["https://race.netkeiba.com/" + url.lstrip("../") for url in race_urls]
        return race_urls

    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def _get_shutuba_info(self, race_url: str) -> Race:
        horses = []

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(race_url, timeout=self.timeout)

            race_no = page.locator('div.RaceList_Item01').text_content().strip()
            race_name = page.locator('h1.RaceName').text_content().strip()
            distance = page.locator('div.RaceData01 > span').nth(0).text_content().strip()

            loc_race_data = page.locator('div.RaceData02 > span')
            kaisai_no = loc_race_data.nth(0).text_content()
            course = loc_race_data.nth(1).text_content()
            kaisai_day = loc_race_data.nth(2).text_content()
            race_grade = loc_race_data.nth(4).text_content()
            race_info = RaceInfo(race_name, kaisai_no, kaisai_day, course, race_no, distance, race_grade)

            loc_horses = page.locator("tr.HorseList")
            for i in range(loc_horses.count()):
                horse_name = loc_horses.nth(i).locator("span.HorseName").text_content().strip()
                url = loc_horses.nth(i).locator("span.HorseName > a").get_attribute("href")
                horse_id = int(url.split("/")[-1])
                jockey = loc_horses.nth(i).locator("td.Jockey").text_content().strip()
                horses.append(RaceHorse(horse_id, horse_name, jockey, None))

            context.close()
            browser.close()
        race = Race(race_info, horses)
        return race

    @retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(TimeoutError))
    def _get_result_info(self, race_url: str) -> Race:
        horses = []

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(race_url, timeout=self.timeout)

            race_no = page.locator("span.RaceNum").text_content().strip()
            race_name = page.locator("h1.RaceName").text_content().strip()
            distance = page.locator("div.RaceData01 > span").nth(0).text_content().strip()
            course = page.locator("div.RaceData02 > span").nth(1).text_content()
            kaisai_no = page.locator("div.RaceData02 > span").nth(0).text_content()
            kaisai_day = page.locator("div.RaceData02 > span").nth(2).text_content()
            race_grade = None
            race_info = RaceInfo(race_name, kaisai_no, kaisai_day, course, race_no, distance, race_grade)

            loc_horses = page.locator("table#All_Result_Table > tbody > tr.HorseList")
            for i in range(loc_horses.count()):
                rank = loc_horses.nth(i).locator("div.Rank").text_content().strip()
                if re.match(r'^\d+$', rank):
                    rank = rank + "着"
                horse_name = loc_horses.nth(i).locator("span.Horse_Name").text_content().strip()
                url = loc_horses.nth(i).locator("span.Horse_Name > a").get_attribute("href")
                horse_id = int(url.split("/")[-1])
                horses.append(RaceHorse(horse_id, horse_name, None, rank))

            context.close()
            browser.close()

        race = Race(race_info, horses)
        return race
