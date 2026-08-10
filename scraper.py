import requests
import sqlite3
import time
from bs4 import BeautifulSoup

BASE = 'https://www.technolife.com'
LISTING_URL = f'{BASE}/category/mobile/mobile-phone'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
    )
}


def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')


def get_spec_value(soup, label_variants):
    for label in label_variants:
        label_node = soup.find(string=lambda s: s and s.strip() == label)
        if not label_node:
            continue
        parent = label_node.parent
        value_tag = parent.find_next_sibling()
        if value_tag and value_tag.get_text(strip=True):
            return value_tag.get_text(strip=True)
        row = parent.find_parent()
        if row:
            children_text = [
                t.get_text(strip=True) for t in row.find_all(recursive=False)
                if t.get_text(strip=True)
            ]
            if len(children_text) >= 2:
                return children_text[-1]
    return None


def get_colors(soup):
    colors = []
    for tag in soup.select('[title]'):
        title = tag.get('title', '').strip()
        parent_classes = ' '.join(tag.get('class', []))
        if title and 'color' in parent_classes.lower():
            colors.append(title)
    colors = list(dict.fromkeys(colors))  
    return colors or None


def get_rating(soup):
    tag = soup.select_one('[class*="rating"], [class*="star"]')
    return tag.get_text(strip=True) if tag else None


def get_intro(soup):
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content'):
        return meta['content'].strip()
    desc = soup.select_one('[class*="description"] p, [class*="intro"] p')
    return desc.get_text(strip=True) if desc else None


def scrape_product_details(link):
    soup = get_soup(link)
    return {
        'intro': get_intro(soup),
        'brand': get_spec_value(soup, ['برند']),
        'storage': get_spec_value(soup, ['حافظه داخلی', 'ظرفیت حافظه داخلی']),
        'ram': get_spec_value(soup, ['حافظه RAM', 'رم', 'حافظه رم']),
        'colors': get_colors(soup),
        'rating': get_rating(soup),
    }


def main():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT,
         price TEXT,
         image TEXT,
         link TEXT,
         intro TEXT,
         brand TEXT,
         storage TEXT,
         ram TEXT,
         colors TEXT,
         rating TEXT)''')
    conn.commit()

    soup = get_soup(LISTING_URL)
    cards = soup.select('section.relative.w-full.rounded-\\[10px\\]')
    print(f'Found {len(cards)} product cards on the listing page')

    for card in cards:
        h2 = card.find('h2')
        if not h2:
            continue
        name = h2.text.strip()

        price_tag = card.select_one('p.font-semiBold.leading-5')
        if not price_tag:
            continue
        price = price_tag.text.strip()

        link_tag = card.select_one('a[href^="/product-"]')
        if not link_tag:
            continue
        link = BASE + link_tag.get('href')

        img_tag = link_tag.select_one('img')
        image = BASE + img_tag.get('src') if img_tag and img_tag.get('src') else None

        print(f'Scraping details for: {name}')
        try:
            details = scrape_product_details(link)
        except Exception as e:
            print(f'  Failed to fetch details: {e}')
            details = {}

        cursor.execute('''
            INSERT INTO products
                (name, price, image, link, intro, brand, storage, ram, colors, rating)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        ''', (
            name, price, image, link,
            details.get('intro'),
            details.get('brand'),
            details.get('storage'),
            details.get('ram'),
            ', '.join(details['colors']) if details.get('colors') else None,
            details.get('rating'),
        ))
        conn.commit()
        time.sleep(1)  

    conn.close()
    print('Done')


if __name__ == '__main__':
    main()