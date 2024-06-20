import asyncio, json, os, traceback, random, time, sys, csv, requests
from typing import List, Any
from urllib.parse import urlparse, urlencode, parse_qs, ParseResult, urlunparse
from datetime import datetime

# ================================ UPDATE SCRIPT ================================

class UpdateScript:
    def __init__(self) -> None:
        self.contents_url = 'https://api.github.com/repos/nabilunnuha/shopee-scraper-pw/contents/'
        self.base_api_url = 'https://raw.githubusercontent.com/nabilunnuha/shopee-scraper-pw/main/'
        self.session = requests.Session()
        self.skip_name = ['README.md', 'tes.py', '.gitignore', 'shopee_list_category.csv']
    
    def get_content(self, url: str, text=False) -> str:
        response = self.session.get(url)
        response.raise_for_status()
        return response.json() if not text else response.text
    
    def write_file(self, path: str, data: str) -> None:
        with open(path, 'w') as f:
            f.write(data)
    
    def update_script(self) -> None:
        for data in self.get_content(self.contents_url):
            if data['name'] in self.skip_name:
                continue
            
            if data['type'] == 'dir':
                tree_url = data['git_url']
                tree_data = self.get_content(tree_url)
                
                for tree_item in tree_data['tree']:
                    file_url = f"{self.base_api_url}{data['name']}/{tree_item['path']}"
                    file_content = self.get_content(file_url, text=True)
                    self.write_file(f"./{data['name']}/{tree_item['path']}", file_content)
                    
            else:
                file_url = data['download_url']
                file_content = self.get_content(file_url, text=True)
                self.write_file(data['path'], file_content)
        
        print('script updated...')

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext
    from playwright.async_api._generated import Request, Page
    from rich import print
    from pydantic import BaseModel
    from pymongo import MongoClient
    from pymongo.cursor import Cursor
    from pymongo.errors import DuplicateKeyError
    
except ImportError as ie:
    print(ie)
    time.sleep(10)
    
except:
    traceback.print_exc()
    time.sleep(10)
    

# ================================ MONGODB ================================

def delete_under_score_from_key(data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any] | list[dict[str, Any]]:
    def process_dict(d: dict[str, Any]) -> dict[str, Any]:
        return {k.replace('_', ''): process_value(v) for k, v in d.items()}

    def process_list(lst: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [process_dict(item) if isinstance(item, dict) else item for item in lst]

    def process_value(value: Any) -> Any:
        if isinstance(value, dict):
            return process_dict(value)
        elif isinstance(value, list):
            return process_list(value)
        else:
            return value

    if isinstance(data, dict):
        return process_dict(data)
    elif isinstance(data, list):
        return process_list(data)
    else:
        return data

def convert_product_shopee_to_pdc(product: dict, namespace: str='hoki', from_data: bool=True, rnd: float=0.25390100699475204, Rnd: float=0.38799338406558054):
    data: dict[str, dict[str, dict]] = product['data'] if from_data else product
    public_source = {
        "productitem": delete_under_score_from_key(data['item']),
        "productprice": delete_under_score_from_key(data['product_price']),
        "productreview": delete_under_score_from_key(data['product_review']),
        "productimages": delete_under_score_from_key(data['product_images']),
        "productshop": delete_under_score_from_key(data['shop_detailed']),
        "productattributes": delete_under_score_from_key(data['product_attributes']),
        "productshipping": delete_under_score_from_key(data['product_shipping']),
        "shippingmeta": delete_under_score_from_key(data['shipping_meta']),
        "shopvouchers": delete_under_score_from_key(data['shop_vouchers']),
        "freereturn": delete_under_score_from_key(data['free_return']),
        'productinfo': {
            'agegate': delete_under_score_from_key(data['age_gate']),
            'coininfo': delete_under_score_from_key(data['coin_info']),
            'flashsale': delete_under_score_from_key(data['flash_sale']),
            'shopvouchers': delete_under_score_from_key(data['shop_vouchers'])},
        'itemid': data['item']['item_id'],
        "name": data['item']['title'],
        "sold": 0,
        "imageurl": data['item']['image'],
        "imageurls": data['product_images']['images'],
        "userid": data['shop_detailed']['userid'],
        "catid": [catid['catid'] for catid in data['item']['categories']][0],
        'bundledealid': 0,
        'canusebundledeal': False,
        'clipinfo': None,
        'codflag': 0,
        'coinearnlabel': None,
        'creditinsurancedata': {'insuranceproducts': None},
        'exclusivepriceinfo': None,
        'groupbuyinfo': None,
        'haslowestpriceguarantee': False,
        'isccinstallmentpaymenteligible': False,
        'isgroupbuyitem': None,
        'isnonccinstallmentpaymenteligible': False,
        'itemhaspost': False,
        'itemhassizerecommendation': False,
        'makeups': None,
        'presaleinfo': None,
        'shopeeverified': False,
        'showfreereturn': None,
        'showfreeshipping': False,
        'taxcode': None,
        'upcomingflashsale': None,
        'videoinfolist': [],
        'welcomepackageinfo': None,
        'wpeligibility': None,
        'ispc': True
    }
    
    return {
        'processed': False,
        'marketplace': 'shopee',
        'id': data['item']['item_id'],
        'productid': data['item']['item_id'],
        "name": data['item']['title'],
        'namespace': namespace,
        "rnd": rnd,
        "image": data['item']['image'],
        "images": data['product_images']['images'],
        "sold": sum([model['sold'] for model in data['item']['models']]),
        "price": int(data['item']['price'] / 100000),
        "price_before_discount": int(data['item']['price'] / 100000),
        "price_after_discount": int(data['item']['price'] / 100000),
        "shop": {
            "shopid": data['item']['shop_id'],
            "location": data['item']['shop_location']
        },
        "shop_location": data['item']['shop_location'],
        "catid": [catid['catid'] for catid in data['item']['categories']][0],
        "category": [catid['catid'] for catid in data['item']['categories']],
        "category_id": [catid['catid'] for catid in data['item']['categories']][-1],
        "cat_name": [catid['display_name'] for catid in data['item']['categories']][-1],
        "categories": data['item']['categories'],
        "brand_id": data['item']['brand_id'],
        "stock": data['item']['stock'],
        "desc": data['item']['description'],
        "url": f"https://shopee.co.id/product/{data['item']['shop_id']}/{data['item']['item_id']}/",
        "public_categ": [catid['catid'] for catid in data['item']['fe_categories']][1],
        'public_source': public_source,
        "type": "pc",
        "Rnd": Rnd
    }

def insert_one_item_to_db(cursor_item: Cursor, data: dict):
    try:
        cursor_item.collection.insert_one(data)
        return True
    except DuplicateKeyError as de:
        print(f'duplikat: {de}')
        return False
    except Exception as e:
        print(f'error: {e}')
        return False
    
def insert_many_item_to_db(cursor_item: Cursor, data: list[dict]):
    try:
        result = cursor_item.collection.insert_many(data)
        return True
    except DuplicateKeyError as de:
        print(f'duplikat: {de}')
        return False
    except Exception as e:
        print(f'error: {e}')
        return False

def get_client():
    return MongoClient('localhost', 27017)

def get_cursor(path: list[str]=['kampretcode2', 'item']):
    client = get_client()
    data_path = {} 
    for database_names in client.list_database_names():
        db = client[database_names]
        data_path[database_names] = {k: db[k].find() for k in db.list_collection_names()}
        
    cursor_item: Cursor = data_path[path[0]][path[1]]
    return cursor_item

def convert_to_pdc_from_json():
    try:
        name_space = str(input('masukkan namespace (default: "hoki"): '))
        if not file_json_path:
            raise ValueError('invalid input!')
    except:
        name_space = 'hoki'
        
    try:
        file_json_path = str(input('masukkan path file json (default: "result.json"): '))
        if not file_json_path or not os.path.exists(file_json_path):
            raise ValueError('invalid input!')
    except:
        file_json_path = 'result.json'
    
    if os.path.exists(file_json_path):
        with open(file_json_path, 'r') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            raise TypeError('type is not list[dict]')
        else:
            cursor = get_cursor()
            data_product_converted = [convert_product_shopee_to_pdc(product, name_space, from_data=False) for product in data]
            for data_produck in data_product_converted:
                insert_one_item_to_db(cursor, data_produck)
            os.remove(file_json_path)
            
# ================================ GENERATE CATEGORY ================================

def write_csv_file(file_path: str, data: list[dict]):
    header_exists = os.path.exists(file_path) and os.stat(file_path).st_size > 0

    with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = data[0].keys() if data else []
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if not header_exists:
            writer.writeheader()

        writer.writerows(data)

def get_facet():
    session = requests.Session()
    
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en;q=0.9,id;q=0.8',
        'cache-control': 'no-cache',
        # 'cookie': '_gcl_au=1.1.1152160299.1713526648; SPC_F=t0dR3a32sqwfzaQI509vHXU16qaQ7sfj; REC_T_ID=34079014-fe41-11ee-9ada-7a0fd56f7cda; SPC_CLIENTID=dDBkUjNhMzJzcXdmkcxjpuawfzmsckqi; SC_DFP=ovyadaefUiRVmWZKprItLwBvzReyUJNo; _med=refer; SPC_SC_TK=5ba70123eba26bc0df429cd244e0d2f3; SPC_SC_UD=995461028; SPC_SC_SESSION=559f3283ff46598777163fb233be7d79_1_995461028; SPC_STK=90wmCh2XkqRXb2u7ef5D9mf83MEDm/5FN1sMa1pw/SMjCn3ZqGxA89tz60sX6hBOD/91EAs0g3vIDmYwtjfntcOkUVSDtGIIQbSwFsDK9O+T1QWIgY6jeEqhQHw5Yy3vat3rKNoqT4GgXKq4ejuDxHWfcYGy1XB19BYZfAJtqgKi+tvnbf6DSW3ys0qxkGJhnmS91g5pWMh7tVMd63BclKEzjXnHVplV8rSgcx9Rmwc=; CTOKEN=jfgrCR9QEe%2BBtcJQ183DyQ%3D%3D; SPC_SI=Sk0vZgAAAAAxWGlvYk5XNckBOQUAAAAAenZJd1ZDSW4=; AMP_TOKEN=%24NOT_FOUND; _gid=GA1.3.571047445.1717593536; SPC_EC=.THU1cjdZWlpQM1ZrSG9MVPPBMZxL9LulPrUZy6TBJT2tuOdvJlYTIP8eZ0b49sc/cc9GYqJi/iZXQ/X5YWzwARAAuH+tVBYlTgXEhVTpcP/BAWqopvMQjvid4DqR+0Cqr0qg4J7g8Kni7M9+9cNdAKhE+o4T1h8j4pMdaPmnjrf5q8GemMVU1u+9JAPmzrrSnBM4+U9zuFYB4ltiAbDlRQ==; SPC_ST=.THU1cjdZWlpQM1ZrSG9MVPPBMZxL9LulPrUZy6TBJT2tuOdvJlYTIP8eZ0b49sc/cc9GYqJi/iZXQ/X5YWzwARAAuH+tVBYlTgXEhVTpcP/BAWqopvMQjvid4DqR+0Cqr0qg4J7g8Kni7M9+9cNdAKhE+o4T1h8j4pMdaPmnjrf5q8GemMVU1u+9JAPmzrrSnBM4+U9zuFYB4ltiAbDlRQ==; SPC_U=1135094525; SPC_R_T_IV=OU43Tms4a3BjcHhWbWU4eA==; SPC_T_ID=HmkU5znfqazik3n7akzcEsy6G8z7u9Rk/K8e5sFFtrPn+4zeZ4K+gjXubqnXzWLOtT5wTPEh/DAoztR1+KoMSWB5NIihWVFIWGrHeqcU/gZaHQ93aGrKkhjdEkE5njXbmE0z8qeJAfftKIgVt1AgM62ppl3nEmCHkTyWBXFRZq4=; SPC_T_IV=OU43Tms4a3BjcHhWbWU4eA==; SPC_R_T_ID=HmkU5znfqazik3n7akzcEsy6G8z7u9Rk/K8e5sFFtrPn+4zeZ4K+gjXubqnXzWLOtT5wTPEh/DAoztR1+KoMSWB5NIihWVFIWGrHeqcU/gZaHQ93aGrKkhjdEkE5njXbmE0z8qeJAfftKIgVt1AgM62ppl3nEmCHkTyWBXFRZq4=; SPC_CDS_CHAT=6c84ef30-4e83-41e5-927f-84aed657264c; SPC_CDS=81881f21-d1df-47c5-8a8e-4d9378bc9db0; SPC_CDS_VER=2; _ga=GA1.3.1561722333.1713618669; _dc_gtm_UA-61904553-8=1; _ga_SW6D8G0HXK=GS1.1.1717593535.62.1.1717594467.60.0.0',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://seller.shopee.co.id/edu/category-guide/',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }

    response = session.get(
        'https://seller.shopee.co.id/help/api/v3/global_category/list/',
        params={'page': '1', 'size': '16'},
        headers=headers,
    )
    print(response.status_code)
    response_json = response.json()
    
    result: list[dict] = []
    
    total: int = response_json['data']['total']
    for page in range(1, int(total/48) + 2):
        params = {'page': str(page), 'size': '48'}

        response = session.get(
            'https://seller.shopee.co.id/help/api/v3/global_category/list/',
            params=params,
            headers=headers,
        )
        res_json = response.json()
        global_cats = res_json['data']['global_cats']
        for data in global_cats:
            facet_id = data['category_id']
            facet_name = data['category_name']
            cat_name = data['path'][1]['category_name']
            # cat_name = data['path'][len(data['path']) - 2]['category_name']
            result.append({
                'facet_id': facet_id,
                'facet_name': facet_name,
                'cat_name': cat_name,
            })
            
    return result
        
def generate_category():
    with open('./data/category_list_from_shopee.json', 'r') as f:
        all_data: list[dict] = json.load(f)
        
    data_facet = get_facet()
    
    data_cat: list[dict] = []
    for data in all_data:
        name = data['display_name']
        if children:= data['children']:
            for child in children:
                child_name: str = child['display_name']
                catid: int = child['catid']
                parent_catid: int = child['parent_catid']
                to_url_name = child_name.strip().replace(' ', '-') + '-cat'
                url = f'https://shopee.co.id/{to_url_name}.{parent_catid}.{catid}'
                data_cat.append({
                    'type': 'category',
                    'parent_name': name,
                    'name': child_name,
                    'link': url,
                    'status': ''
                })
                
                for facet in data_facet:
                    facet_id: int = facet['facet_id']
                    facet_name: str = facet['facet_name']
                    cat_name: str = facet['cat_name']
                    if cat_name.strip() == child_name.strip():
                        data_cat.append({
                            'type': 'facet',
                            'parent_name': child_name,
                            'name': facet_name,
                            'link': f'{url}?facet={facet_id}',
                            'status': ''
                        })
                
    write_csv_file('./shopee_list_category.csv', data_cat)
    print(len(data_cat), 'category generated in "shopee_list_category.csv"')
    

# ================================ MODELS ================================

class FilterDataModel(BaseModel):
    filter_judul: List[str] = []
    price_min: int
    price_max: int
    min_sold: int
    max_sold: int = 9999
    min_stock: int
    max_stock: int = 9999
    min_rating: float
    max_page_scrape: int = 9
    name_space: str = 'tes_scrape'


# ================================ UTILS ================================

def append_data_product(data: list[dict], path: str='./result.json'):
    data_add = []
    if os.path.exists(path):
        with open(path, 'r') as f:
            data_add = json.load(f)
    
    data_add.extend(data)
    data_add_filter = filter_product_duplikat(data_add)
    
    with open(path, 'w') as f:
        json.dump(data_add_filter, f)

def create_not_exist_file():
    is_exist = True
    if not os.path.exists(path:='./data'):
        os.mkdir(path)
        
    if not os.path.exists(path:='./data/config.json'):
        filter_data = FilterDataModel(price_min=20000, price_max=150000, min_sold=25, min_stock=50, min_rating=4.0)
        with open(path, 'w') as f:
            json.dump(filter_data.model_dump(), f, indent=4)
            
    if not os.path.exists(path:='./akun.txt'):
        is_exist = False
        with open(path, 'w') as f:
            f.write('username|password')
            
    if not os.path.exists(path:='./list_url_or_keyword.txt'):
        is_exist = False
        with open(path, 'w') as f:
            f.write('https://shopee.co.id/Tas-Laptop-cat.11042642.11042645?facet=100336\ngamis')
            
    return is_exist

def phare_url_params(url: str, params: dict[str, str]):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    for k, v in params.items():
        query_params[k] = v

    updated_query = urlencode(query_params, doseq=True)
    new_url_parts = ParseResult(
        scheme=parsed_url.scheme,
        netloc=parsed_url.netloc,
        path=parsed_url.path,
        params=parsed_url.params,
        query=updated_query,
        fragment=parsed_url.fragment
    )

    return urlunparse(new_url_parts)

def corvert_cookie(driver_cookies: list[dict[str, Any]], user_agent: str='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'):
    def cookies_capitalize_first(dictionary: dict[str, Any]):
        new_dict = {}
        for key, value in dictionary.items():
            new_key = key[:1].upper() + key[1:]
            new_dict[new_key] = value
        return new_dict
    
    def timestamp_to_tz(timestamp):
        date = datetime.fromtimestamp(timestamp)
        return date.strftime('%Y-%m-%dT%H:%M:%S+07:00')
    
    cookie = []
    final = { "Cookies": cookie, "Ua": user_agent }
    for i in driver_cookies:
        datatitle = cookies_capitalize_first(i)
        datatitle['Expires'] = False
        datatitle['RawExpires'] = ""
        datatitle['MaxAge'] = 0
        datatitle['SameSite'] = 0
        datatitle['Raw'] = ""
        datatitle['Unparsed'] = None
        if 'Expiry' in datatitle:
            datatitle['Expires'] = timestamp_to_tz(datatitle['Expiry'])
            del datatitle['Expiry']
            
        else:
            datatitle['Expires'] = timestamp_to_tz(int(datetime.now().timestamp()))
        cookie.append(datatitle)
        
    return final

def get_cookies(username: str, dir_name: str='v2_shopee_session') -> list[dict] | None:
    current_directory = os.getcwd().split('\\')[0]
    if os.path.exists(path:=f'{current_directory}\\{dir_name}\\{username}.json'):
        with open(path, 'r') as f:
            data_cookies: dict = json.load(f)
        
        list_cookie: list[dict[str, str]] = data_cookies['Cookies']
        list_cookie_modifed = [{k[0].lower() + k[1:]: v for k, v in cookie.items() if k.lower() != 'expires'} for cookie in list_cookie]
        
        for c_dict in list_cookie_modifed:
            c_dict['sameSite'] = 'Lax'
        
        return list_cookie_modifed
    
    return None

def save_cookie(username: str, cookies: list[dict], dir_name: str='v2_shopee_session'):
    current_directory = os.getcwd().split('\\')[0]
    path = f'{current_directory}\\{dir_name}\\{username}.json'
    converted_cookie = corvert_cookie(cookies)
    with open(path, 'w') as f:
        json.dump(converted_cookie, f, indent=4)
    
    print(f'cookie saved: {username}')

def get_name_from_list_product(data: dict, filter_data: FilterDataModel):
    titles = []
    for product in data['items']:
        name: str = product['item_basic']['name']
        price_min: int = product['item_basic']['price_min']
        price_min_idr = price_min // 100000
        price_max: int = product['item_basic']['price_max']
        price_max_idr = price_max / 100000
        sold: int = product['item_basic']['sold']
        stock: int = product['item_basic']['stock']
        rating_star: float = product['item_basic']['item_rating']['rating_star']
        is_continue = False
        
        if filter_data.filter_judul:
            for string in filter_data.filter_judul:
                if string.lower().strip() in name.lower().strip():
                    # print(f'filter name {string.lower()} in {name.lower()}')
                    is_continue = True
                    break
            
        if price_min_idr < filter_data.price_min or price_max_idr > filter_data.price_max:
            # print(f'filter price {price_min_idr} < {filter_data.price_min} or {price_max_idr} > {filter_data.price_max}')
            is_continue = True
            
        if sold < filter_data.min_sold:
            # print(f'filter sold {sold}')
            is_continue = True
            
        if stock < filter_data.min_stock:
            # print(f'filter stock {stock}')
            is_continue = True
            
        if rating_star < filter_data.min_rating:
            # print(f'filter rating_star {rating_star}')
            is_continue = True
        
        if is_continue:
            continue
        
        titles.append(name)
        
    return titles 

def filter_product_duplikat(list_produk: list[dict]):
    titles_seen = set()
    return [d for d in list_produk if not (d['item']['title'] in titles_seen or titles_seen.add(d['item']['title']))]

def remove_complete_url(url_complete: str):
    with open('./list_url_or_keyword.txt', 'r') as f:
        data_cat = [url.strip() for url in f.readlines() if url.strip() and url_complete not in url]
        
    with open('./list_url_or_keyword.txt', 'w') as f:
        f.write('\n'.join(data_cat))
    

# ================================ SCRAPE ================================

async def filter_url_to_scrape(page: Page, url: str, page_int: int):
    if 'https://shopee.co.id/' in url:
        if page_int > 0:
            url = phare_url_params(url, params={'page': page_int})
            refer_before = page.url
            # print(f'referer: {refer_before}')
            await page.goto(url, referer=refer_before)
        else:
            await page.goto(url, referer='https://shopee.co.id/')
        
    else:
        try:
            if page.url != 'https://shopee.co.id/':
                await page.goto('https://shopee.co.id/')
        
            input_search = page.locator('input.shopee-searchbar-input__input')
            try:
                await input_search.scroll_into_view_if_needed(timeout=5000)
                await input_search.click(timeout=5000)
            except:
                await page.goto('https://shopee.co.id/')
                
            await input_search.scroll_into_view_if_needed()
            await input_search.click()
            await page.keyboard.type(url)
            await page.keyboard.press('Enter')
            
        except Exception as e:
            print(f'error input search produk: {e}')
            
    await asyncio.sleep(1)
    
    return page.url
        
async def loop_click_product(page: Page, list_link_product: list[str], current_url: str):
    for name in list(set(list_link_product)):
        captcha = await resolve_captcha(page, sleep=0.5)
        if captcha:
            raise ValueError(captcha)
        try:
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
                await page.wait_for_load_state('domcontentloaded', timeout=5000)
            except:
                pass
            
            locator_product = page.locator('a > div > div', has_text=name[:30].strip())
            
            try:
                await locator_product.scroll_into_view_if_needed(timeout=2000)
                await locator_product.click(timeout=2000)
            except:
                
                if current_url[:50] not in page.url:
                    await page.go_back()
                    
                prev = 0
                for iter in range(0, 7000, 500):
                    await page.evaluate(f'() => window.scrollTo({prev}, {iter})')
                    prev = iter
                    try:
                        try:
                            await page.wait_for_load_state('networkidle', timeout=1000)
                            await page.wait_for_load_state('domcontentloaded', timeout=1000)
                        except:
                            pass
                        
                        await locator_product.scroll_into_view_if_needed(timeout=500)
                        break
                    except:
                        pass
                        
                await locator_product.scroll_into_view_if_needed(timeout=10000)
                await locator_product.click(timeout=10000)
                
            captcha = await resolve_captcha(page, sleep=0.5)
            if captcha:
                raise ValueError(captcha)
            await page.go_back()
            
        except Exception as e:
            # traceback.print_exc()
            print(f'error click product: {e}')

async def resolve_captcha(page: Page, sleep: int | float = 2):
    await asyncio.sleep(sleep)
    laporkan = page.locator('button.cHPMhq', has_text='Laporkan Permasalahan')
    masalah = page.locator('div.uUcrOy', has_text='kami mendeteksi masalah dari koneksi jaringanmu')
    terjadi = page.locator('div.D4kY48', has_text='terjadi kesalahan saat memuat halaman')
    cobalagi = page.locator('button.hKaCPY', has_text='Coba Lagi')
    start = time.time()
    while True:
        if (time.time() - start) > 600:
            return 'resolve_captcha traffic error captcha'
            raise ValueError('resolve_captcha tidak ada pergerakan')
        
        if '/verify/' in page.url:
            print('captcha')
            await asyncio.sleep(1)
        else:
            break
        
        if '/verify/traffic/error' in page.url:
            print('error traffic captcha')
            return 'resolve_captcha traffic error captcha'
            raise ValueError('resolve_captcha traffic error captcha')
        
        try:
            await laporkan.scroll_into_view_if_needed(timeout=300)
            print('error traffic captcha: Laporkan Permasalahan')
            return 'resolve_captcha traffic error captcha'
            raise ValueError('resolve_captcha traffic error captcha')
        except:
            pass
        
        try:
            await terjadi.scroll_into_view_if_needed(timeout=300)
            print('error traffic captcha: Laporkan Permasalahan')
            return 'resolve_captcha traffic error captcha'
            raise ValueError('resolve_captcha traffic error captcha')
        except:
            pass
        
        try:
            await masalah.scroll_into_view_if_needed(timeout=300)
            print('Maaf, kami mendeteksi masalah dari koneksi jaringanmu.')
            return 'resolve_captcha traffic error captcha'
            raise ValueError('resolve_captcha traffic error captcha')
        except:
            pass
        
        try:
            await cobalagi.scroll_into_view_if_needed(timeout=300)
            print('Maaf, kami mendeteksi masalah dari koneksi jaringanmu.')
            return 'resolve_captcha traffic error captcha'
            raise ValueError('resolve_captcha traffic error captcha')
        except:
            pass
        
async def login_account(page: Page, username: str, password: str):
    input_login_username = page.locator('input[type=text].Z7tNyT')
    input_login_password = page.locator('input[type=password].Z7tNyT')
    if 'shopee.co.id/buyer/login' not in page.url:
        await page.goto('https://shopee.co.id/buyer/login?next=https%3A%2F%2Fshopee.co.id%2F')
        
    await input_login_username.scroll_into_view_if_needed(timeout=500)
    print('akun belum login: isi form login!')
    await input_login_username.click()
    await input_login_username.clear()
    await asyncio.sleep(0.5)
    await page.keyboard.type(username)
    await input_login_password.scroll_into_view_if_needed()
    await input_login_password.click()
    await input_login_password.clear()
    await asyncio.sleep(0.5)
    await page.keyboard.type(password)
    await asyncio.sleep(0.5)
    await page.keyboard.press('Enter')
    await asyncio.sleep(2)

async def loop_starting(page: Page, context: BrowserContext, username: str, password: str):
    account_container = page.locator('div.navbar__link--account__container')
    input_login_username = page.locator('input[type=text].Z7tNyT')
    try:
        await page.wait_for_load_state('domcontentloaded', timeout=5000)
        await page.wait_for_load_state('networkidle', timeout=5000)
    except:
        print('error timeout: domcontentloaded or networkidle in 10s')
        await page.reload()
        
    while True:
        try:
            await account_container.scroll_into_view_if_needed(timeout=1000)
            cookies = await context.cookies()
            save_cookie(username, cookies)
            break
        
        except:
            pass
        
        try:
            await input_login_username.scroll_into_view_if_needed(timeout=500)
            await login_account(page, username, password)
        except:
            pass
            
        captcha = await resolve_captcha(page, sleep=0.5)
        if captcha:
            raise ValueError(captcha)
    
async def scrape(cursor: Cursor, url: str, filter_data: FilterDataModel, username: str, password: str):
    data_product = []
    list_link_product = []
    is_nol_to_scrape = False
    is_running_scrape = False
    
    async def capture_request(request: Request):
        nonlocal is_nol_to_scrape, data_product, list_link_product, is_running_scrape
        if 'api/v4/pdp/get_pc' in request.url:
            response = await request.response()
            res_json: dict = await response.json()
            data = res_json.get('data', None)
            if data:
                converted_data = convert_product_shopee_to_pdc(res_json, namespace=filter_data.name_space)
                status_product_db = insert_one_item_to_db(cursor, converted_data)
                if status_product_db:
                    data_product.append(data)
                    title: str = data['item']['title']
                    print(f'scraped: {title[:70]}')
            else:
                print(f'error scrape | response: {res_json}')
                
            
        if 'api/v4/search/search_items' in request.url:
            response = await request.response()
            res_json = await response.json()
            if 'scenario' in request.url:
                if not is_running_scrape:
                    name_to_scrape = get_name_from_list_product(res_json, filter_data)
                    if len(name_to_scrape) == 0:
                        is_nol_to_scrape = True
                    
                    list_link_product.extend(name_to_scrape)
                    
            else:
                print(f'error request url: {request.url}')
    
    async with async_playwright() as p:
        browser: Browser = await p.firefox.launch(headless=False)
        context: BrowserContext = await browser.new_context()
        
        is_cookie: list[dict] | None = get_cookies(username)
        if is_cookie:
            print(f'add_cookies: {username}')
            await context.add_cookies(is_cookie)
        
        else:
            raise FileNotFoundError(f'cookie not found {username}')
            
        page = await context.new_page()
        
        try:
            page.on('request', capture_request)
        except Exception as e:
            print(e)

        await page.goto('https://shopee.co.id/buyer/login?next=https%3A%2F%2Fshopee.co.id%2F', referer='https://www.google.com/search?q=shopee')

        await loop_starting(page, context, username, password) 
        
        empty_result = page.locator('div.shopee-search-empty-result-section')
        is_error_url = False 
        
        for page_int in range(filter_data.max_page_scrape):
            list_link_product = []
            
            if is_error_url:
                break
            
            try:
                captcha = await resolve_captcha(page, sleep=0.5)
                if captcha:
                    raise ValueError(captcha)
                print('get url to scrape')
                is_running_scrape = False
                current_url = await filter_url_to_scrape(page, url, page_int)
                captcha = await resolve_captcha(page, sleep=0.5)
                if captcha:
                    raise ValueError(captcha)
                
                print(f'get product to scrape: page {page_int}')
                start_while = time.time()
                while (time.time() - start_while) < 300:
                    if len(list_link_product) > 0:
                        print(f'product to scrape: {len(list_link_product)} product')
                        is_running_scrape = True
                        break
                    
                    if page.url == 'https://shopee.co.id/' or page.url == 'https://shopee.co.id':
                        current_url = await filter_url_to_scrape(page, url, page_int)
                    
                    if is_nol_to_scrape:
                        raise ValueError('error: tidak ada produk untuk di scrape!')
                    
                    try:
                        await empty_result.scroll_into_view_if_needed(timeout=1000)
                        print('error url invalid')
                        is_error_url = True
                        break
                    
                    except:
                        pass
                    
                    if 'verify/traffic/error' in page.url:
                        raise ValueError('error: verify/traffic/error')
                    
                    captcha = await resolve_captcha(page, sleep=0.5)
                    if captcha:
                        raise ValueError(captcha)
                    
                await loop_click_product(page, list_link_product, current_url)
                
            except:
                traceback.print_exc()
            
        cookies = await context.cookies()
        save_cookie(username, cookies)
        await browser.close()
    
    return data_product
    
def main_scrape():
    try:
        try:
            cursor = get_cursor()
        except:
            raise Exception('error: Mongodb disconnect!!!')
        
        exist = create_not_exist_file()
        if not exist:
            print('silakan isi datanya dulu !!!')
            time.sleep(10)
            return
        
        with open('./data/config.json', 'r') as f:
            config = json.load(f)
            
        filter_data = FilterDataModel(**config)
        
        with open('./data/config.json', 'w') as f:
            json.dump(filter_data.model_dump(), f, indent=4)
            
        with open('./list_url_or_keyword.txt', 'r') as f:
            list_url = [i.strip() for i in f.readlines() if i]
            
        with open('./akun.txt', 'r') as f:
            list_akun = [i.strip() for i in f.readlines() if i]
            
        data_akun: list[dict] = []
        for akun in list_akun:
            username, password, *_ = akun.split('|')
            data_akun.append({'username': username, 'password': password})
            
        print(filter_data)
        for url in list_url:
            random_pick_akun = random.choice(data_akun)
            try:
                result = asyncio.run(scrape(cursor, url, filter_data, random_pick_akun['username'], random_pick_akun['password']))
            except:
                traceback.print_exc()
            
            remove_complete_url(url)
            # append_data_product(result)
            print(len(result))
        
        print('selesai...')
    except:
        traceback.print_exc()
        

# ================================ MAIN ================================

def main(arg: list[str]):
    try:
        create_not_exist_file()
        if len(arg) == 1:
            main_scrape()
            
        elif len(arg) > 1:
            if arg[1] == 'generate_category':
                generate_category()
            elif arg[1] == 'update':
                try:
                    update = UpdateScript()
                    update.update_script()
                except Exception as e:
                    print(f'error: {e}\nUnduh script "main.py" manual disini "https://raw.githubusercontent.com/nabilunnuha/shopee-scraper-pw/main/main.py"')
                    
            elif arg[1] == 'convert_from_json_file':
                convert_to_pdc_from_json()
            else:
                print('invalid argv index[1]')
        else:
            print('invalid argv')
    except:
        traceback.print_exc()
    finally:
        time.sleep(10)
        
if __name__ == '__main__':
    arg = sys.argv
    main(arg)
