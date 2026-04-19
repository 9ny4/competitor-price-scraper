import os
import csv
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import schedule
import time

DB_PATH = os.getenv('DB_PATH', 'prices.db')
BASE_URL = 'https://books.toscrape.com/catalogue/'
EXPORT_DIR = os.getenv('EXPORT_DIR', 'exports')


def init_db(conn):
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price REAL,
            rating TEXT,
            scraped_at TEXT
        )
        '''
    )
    conn.commit()


def parse_price(price_text):
    # price_text like "£53.74" or "£53.74 (sale)" or "£53.74 Sale"
    if not price_text:
        return None
    cleaned = price_text.replace('£', '').strip()
    cleaned = cleaned.split()[0]
    cleaned = cleaned.replace('(', '').replace(')', '')
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_page(page):
    items = []
    cards = page.query_selector_all('.product_pod')
    for card in cards:
        title = card.query_selector('h3 a').get_attribute('title')
        price_text = card.query_selector('.price_color').inner_text()
        rating = card.query_selector('.star-rating').get_attribute('class').replace('star-rating ', '')
        items.append({
            'title': title,
            'price': parse_price(price_text),
            'rating': rating,
            'scraped_at': datetime.utcnow().isoformat(),
        })
    return items


def save_to_db(conn, items):
    cur = conn.cursor()
    cur.executemany(
        'INSERT INTO prices (title, price, rating, scraped_at) VALUES (?, ?, ?, ?)',
        [(i['title'], i['price'], i['rating'], i['scraped_at']) for i in items],
    )
    conn.commit()


def export_csv(conn):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    filename = os.path.join(EXPORT_DIR, f"prices_{datetime.utcnow().date()}.csv")
    cur = conn.cursor()
    cur.execute('SELECT title, price, rating, scraped_at FROM prices ORDER BY id DESC')
    rows = cur.fetchall()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['title', 'price', 'rating', 'scraped_at'])
        writer.writerows(rows)
    return filename


def send_email(report_path):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    mail_to = os.getenv('MAIL_TO')

    if not smtp_host or not mail_to:
        print('SMTP not configured; skipping email')
        return

    msg = EmailMessage()
    msg['Subject'] = 'Daily competitor price report'
    msg['From'] = smtp_user or 'reports@example.com'
    msg['To'] = mail_to
    msg.set_content('Attached is the latest price report.')

    with open(report_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='text', subtype='csv', filename=os.path.basename(report_path))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)


def run_scrape():
    load_dotenv()
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL + 'page-1.html', timeout=60000)
        items = scrape_page(page)
        browser.close()

    save_to_db(conn, items)
    report = export_csv(conn)
    send_email(report)
    conn.close()


if __name__ == '__main__':
    schedule.every().day.at('08:00').do(run_scrape)
    run_scrape()

    while True:
        schedule.run_pending()
        time.sleep(1)
