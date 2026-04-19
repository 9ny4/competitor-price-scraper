import sqlite3
from scraper import init_db, parse_price, save_to_db


def test_parse_price_handles_sale_text():
    assert parse_price('£53.74 (sale)') == 53.74
    assert parse_price('£40.00 Sale') == 40.0


def test_save_to_db_inserts_rows(tmp_path):
    db_path = tmp_path / 'test.db'
    conn = sqlite3.connect(db_path)
    init_db(conn)  # create the prices table before inserting
    items = [
        {'title': 'Book A', 'price': 9.99, 'rating': 'Three', 'scraped_at': '2024-01-01T00:00:00Z'},
        {'title': 'Book B', 'price': 12.50, 'rating': 'Five', 'scraped_at': '2024-01-01T00:05:00Z'},
    ]
    save_to_db(conn, items)

    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM prices')
    count = cur.fetchone()[0]
    conn.close()

    assert count == 2
