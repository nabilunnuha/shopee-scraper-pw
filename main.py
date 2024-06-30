import asyncio, json, os, traceback, random, time, sys, csv, requests, math
from typing import List, Any, Literal, Dict
from urllib.parse import urlparse, urlencode, parse_qs, ParseResult, urlunparse
from datetime import datetime
from collections import Counter, defaultdict


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
    from tqdm import tqdm
    
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
            

# ================================ CONVERT COLLECTION TO QLOBOT ================================

def fix_url(url: str) -> str:
    if url and 'https://cf.shopee.co.id' not in url:
        url = f'https://cf.shopee.co.id/file/{url}'
        
    return url

def filter_duplicates_list_dict(list_dicts: list[dict], key='url') -> list[dict]:
    seen_urls = set()
    filtered_list = [d for d in list_dicts if not (d[key] in seen_urls or seen_urls.add(d[key]))]
    return filtered_list

def filter_collection_from_pdc(data_list: list[dict]) -> tuple[list,list]:
    data_produk = []
    data_produk_variant = []
    for data in tqdm(data_list, desc='Filter Product', ncols=100):
        try:
            to_items = data
            images = data
            public_source = to_items['public_source'] if 'public_source' in to_items else to_items['publicsource']
            productitem = public_source['productitem']
            url = data['url']
            name: str = to_items['name']
            price = to_items['price']
            thumbnail_1 = to_items['image']
            thumbnail_2 = fix_url(images['images'][1]) if len(images['images']) >= 2 else ""
            thumbnail_3 = fix_url(images['images'][2]) if len(images['images']) >= 3 else ""
            thumbnail_4 = fix_url(images['images'][3]) if len(images['images']) >= 4 else ""
            thumbnail_5 = fix_url(images['images'][4]) if len(images['images']) >= 5 else ""
            thumbnail_6 = fix_url(images['images'][5]) if len(images['images']) >= 6 else ""
            thumbnail_7 = fix_url(images['images'][6]) if len(images['images']) >= 7 else ""
            thumbnail_8 = fix_url(images['images'][7]) if len(images['images']) >= 8 else ""
            thumbnail_9 = fix_url(images['images'][8]) if len(images['images']) >= 9 else ""
            thumbnail_10 = fix_url(images['images'][9]) if len(images['images']) >= 10 else ""
            video = ''
            description: str = to_items['desc']
            description_html = ''
            weight = 0
            if 'condition' in productitem:
                condition = 'Baru' if productitem['condition'] == 1 else 'Bekas'
            else:
                condition = 'Baru'
            min_order = 1
            category_1 = productitem['categories'][0]['displayname'] if len(productitem['categories']) >= 1 else ""
            category_2 = productitem['categories'][1]['displayname'] if len(productitem['categories']) >= 2 else ""
            category_3 = productitem['categories'][2]['displayname'] if len(productitem['categories']) >= 3 else ""
            category_4 = productitem['categories'][3]['displayname'] if len(productitem['categories']) >= 4 else ""
            category_5 = productitem['categories'][4]['displayname'] if len(productitem['categories']) >= 5 else ""
            sold = to_items['sold']
            views = 0
            rating = public_source['productreview'].get('ratingstar', 0)
            if public_source['productreview'].get('ratingcount', 0):
                rating_by = sum(public_source['productreview']['ratingcount'])
            else:
                rating_by = 0
                
            stock = to_items['stock']
            size_image = ''
            description = description.strip()
            
            new_data = {'url': url,
                        'name': name,
                        'price': price,
                        'thumbnail_1': fix_url(thumbnail_1),
                        'thumbnail_2': fix_url(thumbnail_2),
                        'thumbnail_3': fix_url(thumbnail_3),
                        'thumbnail_4': fix_url(thumbnail_4),
                        'thumbnail_5': fix_url(thumbnail_5),
                        'thumbnail_6': fix_url(thumbnail_6),
                        'thumbnail_7': fix_url(thumbnail_7),
                        'thumbnail_8': fix_url(thumbnail_8),
                        'thumbnail_9': fix_url(thumbnail_9),
                        'thumbnail_10': fix_url(thumbnail_10),
                        'video': video,
                        'description': description,
                        'description_html': description_html,
                        'weight': weight,
                        'condition': condition,
                        'min_order': min_order,
                        'category_1': category_1,
                        'category_2': category_2,
                        'category_3': category_3,
                        'category_4': category_4,
                        'category_5': category_5,
                        'sold': sold,
                        'views': views,
                        'rating': rating,
                        'rating_by': rating_by,
                        'stock': stock,
                        'size_image': size_image}
            
            models = productitem['models']
            tier_variations = productitem['tiervariations'] if 'tiervariations' in productitem else productitem['tier_variations']
            for model in models:
                if len(tier_variations) >= 1:
                    v_stock = model['stock']
                    v_price = math.ceil(int(str(model['price'])[:-5]) / 100) * 100
                    tier_index = model['extinfo']['tierindex']
                    v_image = ''
                    v2_name = ''
                    v2_value = ''
                    if len(tier_variations) >= 2:
                        v1_name = tier_variations[0]['name']
                        v2_name = tier_variations[1]['name'] if len(tier_variations) >= 2 else ""
                        if tier_variations[0]['images']:
                            v_image = fix_url(tier_variations[0]['images'][tier_index[0]])
                        if len(tier_variations[0]['options']) >= 1:
                            v1_value = tier_variations[0]['options'][tier_index[0]]
                        if v2_name and len(tier_variations[1]['options']) >= 1:
                            v2_value = tier_variations[1]['options'][tier_index[1]]
                    elif len(tier_variations) < 2:
                        v1_name = tier_variations[0]['name']
                        if tier_variations[0]['images']:
                            v_image = fix_url(tier_variations[0]['images'][tier_index[0]])
                        if len(tier_variations[0]['options']) >= 1:
                            v1_value = tier_variations[0]['options'][tier_index[0]]
                            
                v_new_data = {
                    'url': url,
                    'v_stock': v_stock,
                    'v_price': v_price,
                    'v_image': v_image,
                    'v1_name': v1_name,
                    'v1_value': v1_value,
                    'v2_name': v2_name,
                    'v2_value': v2_value,
                }
                data_produk_variant.append(v_new_data)
                
            data_produk.append(new_data)
            
        except Exception as e:
            # traceback.print_exc()
            # print(e)
            pass
              
    return data_produk, data_produk_variant

def merge_product_variant(products: List[Dict], variants: List[Dict]) -> List[Dict]:
    url_to_variants = defaultdict(list)
    
    for variant in variants:
        url_to_variants[variant['url']].append(variant)
    
    result_merge = []
    
    for product in tqdm(products, desc='Combining Variations', ncols=100):
        url = product['url']
        
        if url in url_to_variants:
            data_variants = url_to_variants[url]
            variant_count = min(len(data_variants), 100) 
            
            product['v_name1'] = data_variants[0]['v1_name'] if variant_count >= 1 else ''
            product['v_name2'] = data_variants[0]['v2_name'] if variant_count >= 1 else ''
            
            for i in range(1, variant_count + 1):
                index = i - 1
                product[f'v{i}_value1'] = data_variants[index]['v1_value']
                product[f'v{i}_value2'] = data_variants[index]['v2_value']
                product[f'v{i}_price'] = data_variants[index]['v_price']
                product[f'v{i}_stock'] = data_variants[index]['v_stock']
                product[f'v{i}_image'] = data_variants[index]['v_image']
        
        result_merge.append(product)
    
    return result_merge

def write_csv_file_qlobot(file_path: str, data: list[dict[str, Any]]):
    header_exists = os.path.exists(file_path) and os.stat(file_path).st_size > 0

    with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['url','name','price','thumbnail_1','thumbnail_2','thumbnail_3','thumbnail_4','thumbnail_5','thumbnail_6','thumbnail_7','thumbnail_8','thumbnail_9','thumbnail_10','video','description','description_html','weight','condition','min_order','category_1','category_2','category_3','category_4','category_5','sold','views','rating','rating_by','stock','size_image','v_name1','v_name2','v1_value1','v1_value2','v1_price','v1_stock','v1_image','v2_value1','v2_value2','v2_price','v2_stock','v2_image','v3_value1','v3_value2','v3_price','v3_stock','v3_image','v4_value1','v4_value2','v4_price','v4_stock','v4_image','v5_value1','v5_value2','v5_price','v5_stock','v5_image','v6_value1','v6_value2','v6_price','v6_stock','v6_image','v7_value1','v7_value2','v7_price','v7_stock','v7_image','v8_value1','v8_value2','v8_price','v8_stock','v8_image','v9_value1','v9_value2','v9_price','v9_stock','v9_image','v10_value1','v10_value2','v10_price','v10_stock','v10_image','v11_value1','v11_value2','v11_price','v11_stock','v11_image','v12_value1','v12_value2','v12_price','v12_stock','v12_image','v13_value1','v13_value2','v13_price','v13_stock','v13_image','v14_value1','v14_value2','v14_price','v14_stock','v14_image','v15_value1','v15_value2','v15_price','v15_stock','v15_image','v16_value1','v16_value2','v16_price','v16_stock','v16_image','v17_value1','v17_value2','v17_price','v17_stock','v17_image','v18_value1','v18_value2','v18_price','v18_stock','v18_image','v19_value1','v19_value2','v19_price','v19_stock','v19_image','v20_value1','v20_value2','v20_price','v20_stock','v20_image','v21_value1','v21_value2','v21_price','v21_stock','v21_image','v22_value1','v22_value2','v22_price','v22_stock','v22_image','v23_value1','v23_value2','v23_price','v23_stock','v23_image','v24_value1','v24_value2','v24_price','v24_stock','v24_image','v25_value1','v25_value2','v25_price','v25_stock','v25_image','v26_value1','v26_value2','v26_price','v26_stock','v26_image','v27_value1','v27_value2','v27_price','v27_stock','v27_image','v28_value1','v28_value2','v28_price','v28_stock','v28_image','v29_value1','v29_value2','v29_price','v29_stock','v29_image','v30_value1','v30_value2','v30_price','v30_stock','v30_image','v31_value1','v31_value2','v31_price','v31_stock','v31_image','v32_value1','v32_value2','v32_price','v32_stock','v32_image','v33_value1','v33_value2','v33_price','v33_stock','v33_image','v34_value1','v34_value2','v34_price','v34_stock','v34_image','v35_value1','v35_value2','v35_price','v35_stock','v35_image','v36_value1','v36_value2','v36_price','v36_stock','v36_image','v37_value1','v37_value2','v37_price','v37_stock','v37_image','v38_value1','v38_value2','v38_price','v38_stock','v38_image','v39_value1','v39_value2','v39_price','v39_stock','v39_image','v40_value1','v40_value2','v40_price','v40_stock','v40_image','v41_value1','v41_value2','v41_price','v41_stock','v41_image','v42_value1','v42_value2','v42_price','v42_stock','v42_image','v43_value1','v43_value2','v43_price','v43_stock','v43_image','v44_value1','v44_value2','v44_price','v44_stock','v44_image','v45_value1','v45_value2','v45_price','v45_stock','v45_image','v46_value1','v46_value2','v46_price','v46_stock','v46_image','v47_value1','v47_value2','v47_price','v47_stock','v47_image','v48_value1','v48_value2','v48_price','v48_stock','v48_image','v49_value1','v49_value2','v49_price','v49_stock','v49_image','v50_value1','v50_value2','v50_price','v50_stock','v50_image','v51_value1','v51_value2','v51_price','v51_stock','v51_image','v52_value1','v52_value2','v52_price','v52_stock','v52_image','v53_value1','v53_value2','v53_price','v53_stock','v53_image','v54_value1','v54_value2','v54_price','v54_stock','v54_image','v55_value1','v55_value2','v55_price','v55_stock','v55_image','v56_value1','v56_value2','v56_price','v56_stock','v56_image','v57_value1','v57_value2','v57_price','v57_stock','v57_image','v58_value1','v58_value2','v58_price','v58_stock','v58_image','v59_value1','v59_value2','v59_price','v59_stock','v59_image','v60_value1','v60_value2','v60_price','v60_stock','v60_image','v61_value1','v61_value2','v61_price','v61_stock','v61_image','v62_value1','v62_value2','v62_price','v62_stock','v62_image','v63_value1','v63_value2','v63_price','v63_stock','v63_image','v64_value1','v64_value2','v64_price','v64_stock','v64_image','v65_value1','v65_value2','v65_price','v65_stock','v65_image','v66_value1','v66_value2','v66_price','v66_stock','v66_image','v67_value1','v67_value2','v67_price','v67_stock','v67_image','v68_value1','v68_value2','v68_price','v68_stock','v68_image','v69_value1','v69_value2','v69_price','v69_stock','v69_image','v70_value1','v70_value2','v70_price','v70_stock','v70_image','v71_value1','v71_value2','v71_price','v71_stock','v71_image','v72_value1','v72_value2','v72_price','v72_stock','v72_image','v73_value1','v73_value2','v73_price','v73_stock','v73_image','v74_value1','v74_value2','v74_price','v74_stock','v74_image','v75_value1','v75_value2','v75_price','v75_stock','v75_image','v76_value1','v76_value2','v76_price','v76_stock','v76_image','v77_value1','v77_value2','v77_price','v77_stock','v77_image','v78_value1','v78_value2','v78_price','v78_stock','v78_image','v79_value1','v79_value2','v79_price','v79_stock','v79_image','v80_value1','v80_value2','v80_price','v80_stock','v80_image','v81_value1','v81_value2','v81_price','v81_stock','v81_image','v82_value1','v82_value2','v82_price','v82_stock','v82_image','v83_value1','v83_value2','v83_price','v83_stock','v83_image','v84_value1','v84_value2','v84_price','v84_stock','v84_image','v85_value1','v85_value2','v85_price','v85_stock','v85_image','v86_value1','v86_value2','v86_price','v86_stock','v86_image','v87_value1','v87_value2','v87_price','v87_stock','v87_image','v88_value1','v88_value2','v88_price','v88_stock','v88_image','v89_value1','v89_value2','v89_price','v89_stock','v89_image','v90_value1','v90_value2','v90_price','v90_stock','v90_image','v91_value1','v91_value2','v91_price','v91_stock','v91_image','v92_value1','v92_value2','v92_price','v92_stock','v92_image','v93_value1','v93_value2','v93_price','v93_stock','v93_image','v94_value1','v94_value2','v94_price','v94_stock','v94_image','v95_value1','v95_value2','v95_price','v95_stock','v95_image','v96_value1','v96_value2','v96_price','v96_stock','v96_image','v97_value1','v97_value2','v97_price','v97_stock','v97_image','v98_value1','v98_value2','v98_price','v98_stock','v98_image','v99_value1','v99_value2','v99_price','v99_stock','v99_image','v100_value1','v100_value2','v100_price','v100_stock','v100_image']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if not header_exists:
            writer.writeheader()

        writer.writerows(data)
    
def get_convert_items_from_db_to_qlobot(result_path = './qlobot_collection'):
    print('connect to mongodb...')
    cursor = get_cursor()
    try:
        name_space = str(input('masukkan namespace (default: semua produk shopee): ')).strip()
        print('get items...')
        if not name_space:
            raise ValueError('namespace')
        
        data: list[dict] = [c for c in cursor if c and 'marketplace' in c and c['marketplace'] == 'shopee' and c['namespace'] == name_space]
    except:
        data: list[dict] = [c for c in cursor if c and 'marketplace' in c and c['marketplace'] == 'shopee']
        
    try:
        max_product_per_csv = int(input(f'max product per csv (default: semua produk shopee [{len(data)}]): '))
        if not max_product_per_csv:
            raise ValueError('max_product_per_csv')
    except:
        max_product_per_csv = None
    
    products, variants = filter_collection_from_pdc(data)
    result_m = merge_product_variant(products, variants)
    print('filtering duplicate product...')
    result = filter_duplicates_list_dict(result_m)
    
    if isinstance(max_product_per_csv, int) and max_product_per_csv > 0:
        for i in range(0, len(result), max_product_per_csv):
            pecahan = result[i:i + max_product_per_csv]
            path_csv_file = f'{result_path}/products-{random.randint(10000, 99999)}.csv'
            write_csv_file_qlobot(path_csv_file, pecahan)
            print(path_csv_file)
    else:
        path_csv_file = f'{result_path}/products-{random.randint(10000, 99999)}.csv'
        write_csv_file_qlobot(path_csv_file, result)
        print(path_csv_file)
    

# ================================ COLLECTION MANAGER ================================

class CollectionManager:
    def __init__(self) -> None:
        self.all_name_space = {}
        
    def get_all_name_space(self):
        return dict(Counter([name['namespace'] for name in get_cursor() if 'namespace' in name]))
    
    def delete_col_by_name_space(self, name_space: str) -> int:
        if name_space in list(self.all_name_space.keys()):
            rslt_delete = get_cursor().collection.delete_many({'namespace': name_space})
            return rslt_delete.deleted_count
        
        print(f'"{name_space}" not found')
        return 0
    
    def filter_collection(self) -> list[dict]:
        list_data = []
        for col in get_cursor():
            del col['_id']
            col['processed'] = False
            list_data.append(col)
            
        return list_data
    
    def save_to_json_file(self, data: Any,  path: str):
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def export_collection(self, name_space: str, path_export: str):
        collection = self.filter_collection()
        if name_space == 'ALL':
            self.save_to_json_file(collection, path_export)
            return True
        elif name_space in list(self.all_name_space.keys()):
            data = [col for col in collection if col['namespace'] == name_space.strip()]
            self.save_to_json_file(data, path_export)
            return True
        
        print(f'"{name_space}" not found')
        return False
        
    def import_collection_from_file(self, mode: Literal['pdc', 'pdp'], path_file: str, name_space: str | None):
        if os.path.exists(path_file):
            with open(path_file, 'r') as f:
                data: list[dict] = json.load(f)
                
            cursor = get_cursor()
            names_space_date_or_input = f'collection_{datetime.now().strftime("%d_%m_%Y")}' if not name_space else name_space
            if isinstance(data, list):
                if mode == 'pdc':
                    issuccess = 0
                    for col in data:
                        if '_id' in col:
                            del col['_id']
                            
                        col['namespace'] = names_space_date_or_input
                            
                        rslt = insert_one_item_to_db(cursor, col)
                        if rslt:
                            issuccess += 1
                            
                    return issuccess
                
                elif mode == 'pdp':
                    issuccess = 0
                    for col in data:
                        if '_id' in col:
                            del col['_id']
                            
                        col['namespace'] = names_space_date_or_input
                            
                        product = convert_product_shopee_to_pdc(col, namespace=names_space_date_or_input, from_data=True if 'data' in col else False)
                        rslt = insert_one_item_to_db(cursor, product)
                        if rslt:
                            issuccess += 1
                        
                    return issuccess

                else:
                    raise ValueError(f'invalid mode: {mode}')
                
            else:
                print(f'file harus format Array / List "[]"')
                
        else:
            print(f'"{path_file}" file not found')
            
        return 0
        
    def main_usage(self):
        self.all_name_space = self.get_all_name_space()
        while True:
            try:
                items = ['get all count collection', 'export collection', 'import collection from file', 'delete collection by namespace', 'export to qlobot', 'exit']
                for no, select in enumerate(items, start=1):
                    print(f'{no}. {select.capitalize()}')
                
                selected_user = int(input('\npilih nomor: '))
                if selected_user == 1:
                    self.all_name_space = self.get_all_name_space()
                    print(self.all_name_space)
                    
                elif selected_user == 2:
                    try:
                        name_space = str(input('masukkan nama collection (default: "ALL" untuk semua collection): '))
                        if not name_space:
                            raise ValueError('name_space')
                    except:
                        name_space = 'ALL'
                    try:
                        path_export = str(input('masukkan path export (default: "result_product.json"): '))
                        if not path_export:
                            raise ValueError('path_export')
                    except:
                        path_export = 'result_product.json'
                        
                    result = self.export_collection(name_space, path_export)
                    print(f'success export: {result}')
                
                elif selected_user == 3:
                    path_file = str(input('masukkan path file: (ex: "result_product.json"): '))
                    
                    try:
                        type_data = int(input('produk dari [ 1.pdc_collection | 2.original_from_shopee ] (default: 1): '))
                        if type_data == 2:
                            mode = 'pdp'
                        else:
                            mode = 'pdc'
                    except:
                        mode = 'pdc'
                    
                    try:
                        name_space = str(input('masukkan nama collection ( optional ): '))
                        if not name_space:
                            raise ValueError('name_space')
                    except:
                        name_space = None
                        
                    result = self.import_collection_from_file(mode, path_file, name_space)
                    print(f'success import: {result} product')
                
                elif selected_user == 4:
                    name_space = str(input('masukkan nama collection yang ingin di hapus: '))
                    count_deleted = self.delete_col_by_name_space(name_space)
                    print(f'deleted: {count_deleted} product')
                
                elif selected_user == 5:
                    get_convert_items_from_db_to_qlobot()
                
                elif selected_user == 6:
                    break
                
                print('\n')
                
            except:
                traceback.print_exc()
                print('\n')
        
        
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
                url = f'https://shopee.co.id/{to_url_name}.{parent_catid}.{catid}'.replace(' ', '').replace('\t', '').strip()
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
                            'link': f'{url}?facet={facet_id}'.replace(' ', '').replace('\t', '').strip(),
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
        
    if not os.path.exists(path:='./qlobot_collection'):
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

def phare_url_params(url: str, params: dict[str, Any] = {}):
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

def get_value_params(url: str, key: str):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)
    if key in query_params:
        max_price = query_params[key][0]
        return max_price
    
    return None

def corvert_cookie(driver_cookies: list[dict[str, Any]], user_agent: str='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'):
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
            if 'domain' in c_dict:
                if 'shopee' not in c_dict['domain']:
                    c_dict['domain'] = '.shopee.co.id'
            else:
                c_dict['domain'] = '.shopee.co.id'
                
            if 'path' not in c_dict:
                c_dict['path'] = '/'
                
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
        data_cat = [url.strip() for url in f.readlines() if url.strip() and url_complete.strip() != url.strip()]
        
    with open('./list_url_or_keyword.txt', 'w') as f:
        f.write('\n'.join(data_cat))


# ================================ SCRAPE ================================

async def filter_url_to_scrape(page: Page, url: str, page_int: int, filter_data: FilterDataModel):
    try:
        await page.wait_for_load_state('load', timeout=10000)
    except:
        pass
    
    if 'https://shopee.co.id/' in url:
        'https://shopee.co.id/Alat-&-Aksesoris-Musik-cat.11043572.11043648?facet=102019&maxPrice=150000&minPrice=20000&page=0&ratingFilter=4&sortBy=pop'
        if page_int == 0:
            await page.goto(url, referer='https://shopee.co.id/')
            
        url_pharse = phare_url_params(url, params={'page': page_int, 'minPrice': filter_data.price_min, 'maxPrice': filter_data.price_max, 'ratingFilter': int(filter_data.min_rating), 'sortBy': 'pop'})
        refer_before = page.url
        # print(f'referer: {refer_before}')
        await page.goto(url_pharse, referer=refer_before)
        
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
    empty_result = page.locator('div.shopee-search-empty-result-section')
    empty_result_2 = page.locator('div.shopee-search-empty-result-section__hint')
    
    for name in list(set(list_link_product)):
        captcha = await resolve_captcha(page, sleep=0.5)
        if captcha:
            raise ValueError(captcha)

        try:
            await empty_result.scroll_into_view_if_needed(timeout=500)
            print('error url invalid')
            raise ValueError('is_error_url')
        
        except Exception as e:
            if str(e) == 'is_error_url':
                raise ValueError('is_error_url')
        
        try:
            await empty_result_2.scroll_into_view_if_needed(timeout=500)
            print('error url invalid')
            raise ValueError('is_error_url')
        
        except Exception as e:
            if str(e) == 'is_error_url':
                raise ValueError('is_error_url')
        try:
            try:
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
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
                for iter in range(0, 5000, 500):
                    await page.evaluate(f'() => window.scrollTo({prev}, {iter})')
                    prev = iter
                    try:
                        try:
                            await page.wait_for_load_state('domcontentloaded', timeout=5000)
                        except:
                            pass
                        
                        await locator_product.scroll_into_view_if_needed(timeout=500)
                        break
                    except:
                        pass
                        
                await locator_product.scroll_into_view_if_needed(timeout=5000)
                await locator_product.click()
                
            captcha = await resolve_captcha(page, sleep=1)
            if captcha:
                raise ValueError(captcha)
            
            await page.go_back()
            
        except Exception as e:
            # traceback.print_exc()
            if 'resolve_captcha' in str(e):
                raise ValueError(str(e))
            
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
    alert_login = page.locator('div > div.y9KyC1')
    try:
        print('waiting for load state')
        await page.wait_for_load_state('load', timeout=10000)
    except:
        pass
    try:
        print('waiting for networkidle state')
        await page.wait_for_load_state('networkidle', timeout=10000)
    except:
        pass
    try:
        print('waiting for domcontentloaded state')
        await page.wait_for_load_state('domcontentloaded', timeout=10000)
    except:
        pass
        
    while True:
        try:
            await account_container.scroll_into_view_if_needed(timeout=1000)
            cookies = await context.cookies()
            save_cookie(username, cookies)
            break
        
        except:
            pass
        
        try:
            await alert_login.scroll_into_view_if_needed(timeout=500)
            raise ValueError('login gagal')
        except Exception as e:
            if str(e) == 'login gagal':
                raise ValueError(str(e))
            
        try:
            await input_login_username.scroll_into_view_if_needed(timeout=500)
            await login_account(page, username, password)
        except:
            pass
        
            
        captcha = await resolve_captcha(page, sleep=0.5)
        if captcha:
            raise ValueError(captcha)
    
async def scrape(cursor: Cursor, url: str, filter_data: FilterDataModel, username: str, password: str):
    last_data = {
        'data_product': [],
        'last_url': url,
        'username': username,
        'error': None
    }
    
    list_link_product = []
    is_nol_to_scrape = False
    is_running_scrape = False
    
    try:
        async def capture_request(request: Request):
            nonlocal is_nol_to_scrape, list_link_product, is_running_scrape, last_data
            try:
                if 'api/v4/pdp/get_pc' in request.url:
                    response = await request.response()
                    res_json: dict = await response.json()
                    data = res_json.get('data', None)
                    if data:
                        converted_data = convert_product_shopee_to_pdc(res_json, namespace=filter_data.name_space)
                        status_product_db = insert_one_item_to_db(cursor, converted_data)
                        if status_product_db:
                            last_data['data_product'].append(data)
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
            except Exception as e:
                print(f'error http request: {str(e)}')
        
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
            empty_result_2 = page.locator('div.shopee-search-empty-result-section__hint')
            
            resume_page = get_value_params(url, 'page')
            
            for page_int in range(int(resume_page) if resume_page is not None else 0, filter_data.max_page_scrape):
                list_link_product = []
                
                
                try:
                    captcha = await resolve_captcha(page, sleep=0.5)
                    if captcha:
                        raise ValueError(captcha)
                    
                    print('get url to scrape')
                    is_running_scrape = False
                    current_url = await filter_url_to_scrape(page, url, page_int, filter_data)
                    last_data['last_url'] = current_url
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
                            current_url = await filter_url_to_scrape(page, url, page_int, filter_data)
                        
                        if is_nol_to_scrape:
                            raise ValueError('error: tidak ada produk untuk di scrape!')
                        
                        try:
                            await empty_result.scroll_into_view_if_needed(timeout=700)
                            print('error url invalid')
                            raise ValueError('is_error_url')
                        
                        except Exception as e:
                            if str(e) == 'is_error_url':
                                raise ValueError('is_error_url')
                        
                        try:
                            await empty_result_2.scroll_into_view_if_needed(timeout=700)
                            print('error url invalid')
                            raise ValueError('is_error_url')
                        
                        except Exception as e:
                            if str(e) == 'is_error_url':
                                raise ValueError('is_error_url')
                        
                        if 'verify/traffic/error' in page.url:
                            raise ValueError('error: verify/traffic/error')
                        
                        captcha = await resolve_captcha(page, sleep=0.5)
                        if captcha:
                            raise ValueError(captcha)
                        
                    await loop_click_product(page, list_link_product, current_url)
                    
                except Exception as e:
                    last_data['error'] = str(e)
                    if 'resolve_captcha' in str(e):
                        raise ValueError(str(e))
                
            cookies = await context.cookies()
            save_cookie(username, cookies)
            await browser.close()
    
    except Exception as e:
        # traceback.print_exc()
        last_data['error'] = str(e)
        
    finally:
        return last_data
    
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
            list_akun = list(set([i.strip() for i in f.readlines() if i]))
            
        data_akun: list[dict] = []
        for akun in list_akun:
            username, password, *_ = akun.split('|')
            data_akun.append({'username': username, 'password': password})
            
        print(filter_data)
        account_used = []
        for index_url, url in enumerate(list_url, start=1):
            last_url = url
            while True:
                print(f'{index_url}. {last_url}')
                if len(account_used) >= int(len(data_akun) / 2):
                    account_used = []
                    
                while True:
                    random_pick_akun = random.choice(data_akun)
                    if random_pick_akun['username'] not in account_used:
                        account_used.append(random_pick_akun['username'])
                        break
                    
                result = asyncio.run(scrape(cursor, last_url, filter_data, random_pick_akun['username'], random_pick_akun['password']))
                last_url = result['last_url']
                error = result['error']
                len_data_product = len(result['data_product'])
                last_page = get_value_params(last_url, 'page')
                
                if error and 'captcha' in error:
                    print('continue', error)
                    continue
                
                if error and 'login gagal' in error:
                    print('continue', error)
                    continue
                
                if error and 'error_url' in error:
                    print('break', error)
                    break
                
                print(len_data_product)
                
                if error:
                    print(error)
                    
                if last_page and int(last_page) - 1 >= filter_data.max_page_scrape:
                    print('break last_page', last_page)
                    break
                
                if len_data_product == 0:
                    print('break len_data_product', len_data_product)
                    break
                
            remove_complete_url(url)
        
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
                
            elif arg[1] == 'collection_manager':
                collection_manager = CollectionManager()
                collection_manager.main_usage()
                
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
