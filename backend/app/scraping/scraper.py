import re
import json
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

import os
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, future=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NeusearchScraper/1.0; +https://example.com/bot)"
}

BASE = "https://hunnit.com"


def safe_get(url: str, timeout: int = 15) -> Optional[requests.Response]:
    try:
        return requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception as e:
        print(f"[http] failed GET {url}: {e}")
        return None

def extract_json_ld_product(soup: BeautifulSoup) -> Dict[str, Any]:
    """Return first product-like JSON-LD dict or empty dict."""
    for script in soup.select("script[type='application/ld+json']"):
        txt = script.string or ""
        if not txt or len(txt.strip()) < 10:
            continue
        try:
            obj = json.loads(txt)
        except Exception:
            # sometimes there are multiple JSON objects glued together or template tokens; skip
            continue
        objs = obj if isinstance(obj, list) else [obj]
        for cand in objs:
            if isinstance(cand, dict):
                t = str(cand.get("@type", "")).lower()
                if "product" in t or cand.get("name"):
                    return cand
    return {}

def node_is_variant_control(node: BeautifulSoup) -> bool:
    if node is None:
        return False
    if node.find("option"):
        return True
    html_snippet = str(node)[:2000].lower()
    if "data-price" in html_snippet or "data-image" in html_snippet or "data-id" in html_snippet or "data-compare-price" in html_snippet:
        return True
    cls = " ".join(node.get("class") or [])
    if re.search(r"(variant|swatch|selector|option|product-variants|product__variants)", cls, re.I):
        return True
    return False

def parse_price(candidate: Any) -> Optional[float]:
    if candidate is None:
        return None
    try:
        return float(candidate)
    except Exception:
        try:
            s = re.sub(r"[^\d.]+", "", str(candidate))
            return float(s) if s else None
        except Exception:
            return None

def extract_features(soup):
    tabs = {
        "Product Features": "tab-2",
        "Fabric Features": "tab-3",
        "Function": "tab-4",
    }

    features = {}

    for section, tab_id in tabs.items():
        items = []

        for tab in soup.find_all("div", id=tab_id):
            block = tab.select_one(".metafield-rich_text_field")
            if not block:
                continue

            for p in block.find_all("p"):
                strong = p.find("strong")
                full_text = p.get_text(" ", strip=True)

                if strong:
                    title = strong.get_text(strip=True).rstrip(":")
                    desc = full_text.replace(strong.get_text(strip=True), "", 1).lstrip(": ").strip()
                else:
                    title = None
                    desc = full_text

                if desc:
                    items.append({
                        "title": title,
                        "description": desc
                    })

            if items:
                break  # take first valid populated tab

        if items:
            features[section] = items

    return features

def infer_category(title: str) -> str:
    t = title.lower()
    if "leggings" in t:
        return "Leggings"
    if "skort" in t:
        return "Skorts"
    if "sports bra" in t or "bra" in t:
        return "Sports Bras"
    if "jacket" in t:
        return "Jackets"
    if "shorts" in t:
        return "Shorts"
    if "co-ord" in t or "set" in t:
        return "Co-ord Sets"
    return "Activewear"

def parse_product_detail(html: str, page_url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    ld = extract_json_ld_product(soup)

    # title
    title = None
    if ld.get("name"):
        title = str(ld.get("name")).strip()
    else:
        h = soup.select_one("h1, .product-single__title, .product-title")
        if h:
            title = h.get_text(" ", strip=True)

    # image
    image_url = None
    if ld.get("image"):
        img = ld.get("image")
        if isinstance(img, list):
            image_url = img[0]
        elif isinstance(img, str):
            image_url = img
    if image_url:
        image_url = urljoin(BASE, image_url) if image_url.startswith("//") else image_url

    # description
    description = ld.get("description") or ""
    if not description:
        desc_sel = soup.select_one(".product-description, .rte, .description, .product-single__description")
        description = desc_sel.get_text(" ", strip=True) if desc_sel else description

    # price
    price = None
    if ld.get("offers"):
        offers = ld.get("offers")
        offers = offers if isinstance(offers, list) else [offers]
        prices = [parse_price(o.get("price")) for o in offers if isinstance(o, dict) and o.get("price") is not None]
        prices = [p for p in prices if p is not None]
        if prices:
            price = min(prices)
    if price is None:
        # try finding price text
        psel = soup.select_one(".price, .product-price, .product-single__price, [itemprop='price']")
        if psel:
            price = parse_price(psel.get_text(" ", strip=True))

    # category: try breadcrumbs or meta
    category = infer_category(title)

    # features (primary)
    features = extract_features(soup)
    # print(features)
    # features = [f for f in (features or []) if f and len(f) > 1]

    return {
        "title": title,
        "price": price,
        "description": description,
        "features": features,
        "image_url": image_url,
        "category": category,
    }

def save_to_db(items, engine):
    inserted = 0
    skipped = 0

    insert_sql = text("""
        INSERT INTO products (
            title,
            price,
            description,
            features,
            image_url,
            category,
            source_url
        )
        VALUES (
            :title,
            :price,
            :description,
            :features,
            :image_url,
            :category,
            :source_url
        )
    """)

    exists_sql = text("""
        SELECT 1 FROM products
        WHERE title = :title AND image_url = :image_url
        LIMIT 1
    """)

    with engine.begin() as conn:  # auto-commit / auto-rollback
        for p in items:
            # hard validation (prevents your "missing title" crash)
            if not p.get("title") or not p.get("image_url"):
                skipped += 1
                continue

            exists = conn.execute(
                exists_sql,
                {
                    "title": p["title"],
                    "image_url": p["image_url"],
                },
            ).fetchone()

            if exists:
                skipped += 1
                continue

            try:
                conn.execute(
                    insert_sql,
                    {
                        "title": p["title"],
                        "price": p.get("price"),
                        "description": p.get("description"),
                        "features": json.dumps(p.get("features", []), ensure_ascii=False),
                        "image_url": p["image_url"],
                        "category": p.get("category"),
                        "source_url": p.get("source_url"),
                    },
                )
                inserted += 1
            except SQLAlchemyError as e:
                print(f"[db] insert failed for {p.get('title')} : {e}")
                # continue safely, transaction is still clean

    print(f"[db] inserted={inserted}, skipped={skipped}")

def collect_product_links_from_collection(collection_url: str, limit: int = 50) -> List[str]:
    """Grab product links from a collection listing page (pagination not implemented)."""
    resp = safe_get(collection_url)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue
        # product pages on hunniit often contain '/products/'
        if "/products/" in href:
            full = urljoin(BASE, href)
            if full not in links:
                links.append(full)
        if len(links) >= limit:
            break
    return links

def collect_and_save(collection_url: str = "https://hunnit.com/collections/all", min_products: int = 50):
    product_links = collect_product_links_from_collection(collection_url, limit=200)
    print(f"[collect] found {len(product_links)} product links")
    items = []
    for link in product_links:
        if len(items) >= min_products:
            break
        resp = safe_get(link)
        if not resp:
            continue
        parsed = parse_product_detail(resp.text, link)
        # attach source_url for debugging (not saved to DB since table lacks this column)
        parsed["source_url"] = link
        parsed["price"] = parsed.get("price") or None
        items.append(parsed)
        print("[collected]", parsed.get("title"))
        # time.sleep(0.6)

    print(f"[collect] collected {len(items)} items; saving to DB...")
    res = save_to_db(items, engine)
    print("[result]", res)

if __name__ == "__main__":
    collect_and_save()