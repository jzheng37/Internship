import requests
import re
from bs4 import BeautifulSoup

from mysql_helper import MySQLHelper

class doubanFilmScraper:
    def __init__(self, db_name = "school_db"):
        self.target_url = "https://movie.douban.com/top250"
        self.db = MySQLHelper(database=db_name)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.init_db_table()

    def init_db_table(self):
        self.db.execute_modify("DROP TABLE IF EXISTS doubanFilm_trends;")
        create_table_sql = """
        CREATE TABLE doubanFilm_trends (
            id INT AUTO_INCREMENT PRIMARY KEY,
            rank_num INT,
            title_CHI VARCHAR(255),
            title_FOR VARCHAR(255),
            rating DECIMAL(3,1),
            vote_count INT,
            release_year INT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        self.db.execute_modify(create_table_sql)

    def fetch_html(self,url):
        try:
          response = requests.get(url, headers=self.headers)
          response.raise_for_status()
          return response.text
        except requests.exceptions.RequestException as e:
          print(f"Error fetching the URL: {e}")
          return None

    def extract_searches(self):
        trending_list = []
        rank_counter = 1

        for start_index in range(0, 100, 25):
            page_url = f"{self.target_url}?start={start_index}"
            print(f"Scraping page starting at index {start_index}...")

            html = self.fetch_html(page_url)
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.find_all('div', class_='item')

            for item in items:
                hd_div = item.find('div', class_='hd')
                title_spans = hd_div.find_all('span', class_='title')
                chinese_name = title_spans[0].get_text(strip=True)

                english_name = ""
                if len(title_spans) > 1:
                    raw_english = title_spans[1].get_text(strip=True)
                    english_name = raw_english.replace('/', '').strip()

                    rating_span = item.find('span', class_='rating_num')
                    rating = float(rating_span.get_text(strip=True)) if rating_span else 0.0

                    votes_text = item.find(string=re.compile(r'\d+人评价'))
                    vote_count = 0
                    if votes_text:
                        vote_count = int(re.search(r'\d+', votes_text).group())

                    bd_div = item.find('div', class_='bd')
                    p_tag = bd_div.find('p') if bd_div else None
                    release_year = 0
                    if p_tag:
                        p_text = p_tag.get_text()
                        # Searches for the first standalone 4-digit number block
                        year_match = re.search(r'\b\d{4}\b', p_text)
                        if year_match:
                            release_year = int(year_match.group())

                trending_list.append({
                    'rank_num': rank_counter,
                    'title_CHI': chinese_name,
                    'title_FOR': english_name,
                    'rating': rating,
                    'vote_count': vote_count,
                    'release_year': release_year
                })

                rank_counter += 1
        return trending_list

    def save_trends_to_db(self, trends):

        truncate_sql = "TRUNCATE TABLE doubanFilm_trends;"
        self.db.execute_modify(truncate_sql)

        insert_sql = "INSERT INTO doubanFilm_trends (rank_num, title_CHI, title_FOR,rating, vote_count, release_year) VALUES (%s, %s, %s,%s, %s, %s);"
        values_to_insert = [
            (
                item['rank_num'],
                item['title_CHI'],
                item['title_FOR'],
                item['rating'],
                item['vote_count'],
                item['release_year']
            )
            for item in trends
        ]

        saved_count = self.db.execute_modify_many(insert_sql, values_to_insert)
        print(f"Saved {saved_count} entries successfully in a single batch.")

if __name__ == "__main__":
    scraper = doubanFilmScraper(db_name="school_db")
    topFilms = scraper.extract_searches()

    if topFilms:
        scraper.save_trends_to_db(topFilms)
        saved_records = scraper.db.execute_query("SELECT * FROM doubanFilm_trends ORDER BY id DESC LIMIT 100;")
        for row in reversed(saved_records):
            print(f"DB ID: {row['id']} | Rank: {row['rank_num']} | Title_CHI: {row['title_CHI']}"
                  f" | Title_FOR: {row['title_FOR']} | Rating: {row['rating']}"
                  f" | Votes: {row['vote_count']} | Year: {row['release_year']} | Saved: {row['scraped_at']}")
    else:
        print("Nothing added to DB.")