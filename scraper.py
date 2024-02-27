from bs4 import BeautifulSoup
import requests, json, csv

headers = {
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Referer': 'https://gopher1.extrkt.com/?paged=1',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'sec-ch-ua-platform': '"Windows"',
}

def product_listings():
    page_number = 1
    max_page = 1
    product_lists = []
    while page_number <= max_page:
        start_url = f'https://gopher1.extrkt.com/?paged={page_number}'
        response = requests.get(start_url, headers=headers).content.decode()
        soup = BeautifulSoup(response, features = "lxml")
        a_tags = soup.select('a.woocommerce-LoopProduct-link.woocommerce-loop-product__link')

        for a_tag in a_tags:
            get_href = a_tag.get('href')
            product_lists.append(get_href)
        print(f"Getting product listings from page {page_number}: {len(a_tags)} links found")
        page_number += 1

    
    product_variants = []
    for product_list in product_lists:
        res = requests.get(product_list, headers=headers).content.decode()
        s = BeautifulSoup(res, features = "lxml")
        form = s.select_one('form.variations_form.cart')


        if form:
            data_product_variations = form.get('data-product_variations')
            json_attributes = json.loads(data_product_variations)

            first_pair = []
            second_pair = []
            for attributes in json_attributes:
                get_attr = attributes.get('attributes')
                if len(get_attr) > 1:
                    item_list = list(get_attr.items())
                    first_pair.append(item_list[0])
                    second_pair.append(item_list[1])
                elif len(get_attr) == 0:
                    print(f"Getting product links {product_list}")
                    product_variants.append(product_list)
                else:
                    item_list = list(get_attr.items())
                    first_pair.append(item_list[0])

            if first_pair is not None and second_pair is not None:
                for first, second in zip(first_pair, second_pair):
                    variant_link = f"{product_list}&{first[0]}={first[1]}&{second[0]}={second[1]}"
                    product_variants.append(variant_link)
                    print(f"Getting product links {variant_link}")
            else:
                for first in first_pair:
                    variant_link = f"{product_list}&{first[0]}={first[1]}"
                    product_variants.append(variant_link)
                    print(f"Getting product links {variant_link}")
        else:
            print(f"Getting product links {product_list}")
            product_variants.append(product_list)

    return product_variants


def product_scraping(product_variants):
    parsed_products = []
    for variant in product_variants:
        response = requests.get(variant, headers=headers).content.decode()

        if requests.get(variant, headers=headers).status_code == 200:
            print(f"Scraping {variant}")
            soup = BeautifulSoup(response, features='lxml')
            product_element = soup.select_one('div.summary.entry-summary')
            size_element = soup.select('select#size option')
            color_element = soup.select('select#color option')
            form = soup.select_one('form.variations_form.cart')

            title = product_element.find('h1').get_text(strip=True)
            product_url = variant
            price = product_element.select_one('p.price span').get_text()
            sku_element= soup.select_one('span.sku').get_text(strip=True).strip('SKU:')
            category = soup.select_one('span.posted_in a').get_text()
            size = ""
            color = ""

            if form:

                for _size in size_element:
                    if _size.get('selected') == 'selected':
                        size = _size.get_text()
                
                for _color in color_element:
                    if _color.get('selected') == 'selected':
                        color = _color.get_text()

                sku = f'{sku_element}-{size}-{color}'
                data_product_variations = form.get('data-product_variations')
                json_attributes = json.loads(data_product_variations)

                availability = ''
                stock = ''
                image = ''
                for attributes in json_attributes:
                    get_sku = attributes.get('sku')
                    if sku == get_sku:
                        get_availability = attributes.get('availability_html')
                        availability_soup = BeautifulSoup(get_availability, features='lxml')
                        availability = availability_soup.get_text(strip=True)
                        stock = availability
                        image = attributes['image']['url']    
            else:
                sku = sku_element= soup.select_one('span.sku').get_text(strip=True).strip('SKU:')
                stock = soup.select_one('p.stock.in-stock').get_text()
                image = soup.select_one('div.woocommerce-product-gallery__image a').get('href')
                

            product_info = {
                "Title": title,
                "Product URL": product_url,
                "Image URL": image,
                "SKU": sku if sku else "",
                "Price": price,
                "Stock": stock,
                "Category": category,
                "Size": size if size else "",
                "Color": color if color else "",
                }
            parsed_products.append(product_info)
    return parsed_products


def result(parsed_products, filename):
    if not parsed_products:
        print("No product found")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title','Product URL', 'Image URL', 'SKU', 'Price', 'Stock', 'Category', 'Size', 'Color']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for product in parsed_products:
            writer.writerow(product)
    
    print(f"Successfully wrote {len(parsed_products)} products to {filename}")


def main():
    listings = product_listings()
    scrape_products = product_scraping(listings)
    result(scrape_products, 'products.csv')


main()