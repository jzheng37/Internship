import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

from mysql_helper import MySQLHelper


class BaiduTrendScraper:
    def __init__(self, db_name = "trend_db"):
        self.target_url = "https://top.baidu.com/board?tab=realtime"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        self.db = MySQLHelper(database=db_name)
        self.init_db_table()

    def init_db_table(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS baidu_trends (
            id INT AUTO_INCREMENT PRIMARY KEY,
            rank_num INT,
            title VARCHAR(255),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        self.db.execute_modify(create_table_sql)

    def fetch_html(self):
        try:
          response = requests.get(self.target_url, headers=self.headers)
          response.raise_for_status()
          return response.text
        except requests.exceptions.RequestException as e:
          print(f"Error fetching the URL: {e}")
          return None

    def extract_title_from_url(self, url_string):
        parsed_url = urlparse(url_string)

        query_params = parse_qs(parsed_url.query)

        encoded_title = query_params.get('wd', [None])[0]

        if encoded_title:
            return unquote(encoded_title)
        return "Title Not Found"


    def extract_searches(self):
        html = self.fetch_html()
        soup = BeautifulSoup(html, 'html.parser')
        trending_list = []
        items = soup.find_all('a', class_='img-wrapper_29V76')

        for rank, item in enumerate(items[:10], start=1):
            link = item.get('href')
            title = self.extract_title_from_url(link)

            trending_list.append({
             'rank': rank,
             'title': title
            })

        return trending_list

    def save_trends_to_db(self, trends):

        truncate_sql = "TRUNCATE TABLE baidu_trends;"
        self.db.execute_modify(truncate_sql)

        if not trends:
            print("No trends data available to save.")
            return

        insert_sql = "INSERT INTO baidu_trends (rank_num, title) VALUES (%s, %s);"

        saved_count = 0
        for item in trends:
            success = self.db.execute_modify(insert_sql, (item['rank'], item['title']))
            if success:
                saved_count += 1

        print(f"Database sync complete: Saved {saved_count}/10 entries successfully.")



if __name__ == "__main__":
    scraper = BaiduTrendScraper(db_name="school_db")
    top_trends = scraper.extract_searches()

    if top_trends:
        scraper.save_trends_to_db(top_trends)
        saved_records = scraper.db.execute_query("SELECT * FROM baidu_trends ORDER BY id DESC LIMIT 10;")
        for row in reversed(saved_records):
            print(f"DB ID: {row['id']} | Rank: {row['rank_num']} | Topic: {row['title']} | Saved: {row['scraped_at']}")
    else:
        print("Extraction pipeline returned empty. Nothing added to DB.")
