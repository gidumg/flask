from flask import Flask, render_template, request
from markupsafe import Markup
import pandas as pd
import os
import logging
import requests
from tqdm import tqdm
from requests.exceptions import MissingSchema
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)

# Flask routes and other code follow


app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        result = ""
        if uploaded_file.filename != '':
            # Ensure the upload directory exists
            upload_dir = 'C:\\Users\\Owner\\Documents\\GitHub\\Flask\\uploads'
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
        
        # Save the uploaded file
        file_path = os.path.join(upload_dir, uploaded_file.filename)
        uploaded_file.save(file_path)  # save file
        result = process_file(file_path)  # process file
        os.remove(file_path)  # delete file after processing

    else:
        result = "No file uploaded"

    return render_template('index.html', result=result)

def process_file(filename):

    file_list = pd.read_excel(filename)

    login_url = "https://comsmart.co.kr/cmart/bbs/login_check.php"
    username = "fred"
    password = "123"

    payload = {
        'mb_id': username,
        'mb_password': password
    }

    session = requests.Session()
    res = session.post(login_url, data=payload)

    final_model_name = []
    final_link_address = []
    final_description_list = []
    final_access_link_list = []
    final_stock_list = []

    for r in tqdm(range(len(file_list))):
        url = "https://www.comsmart.co.kr/cmart/shop/search.php?wk=&q="
        item_name = str(file_list.loc[r, '모델명'])
        url_link = url + item_name
        comsmart = session.get(url_link)
        soup = BeautifulSoup(comsmart.text, 'html.parser')

        table = soup.select("div.tgslider")

        model_name = []
        image_link = []
        description_list = []
        access_link_list = []


        for i in table:
            for e in i.select("div.red.it_5") :
                model = e.get_text().replace("[","").replace("]","").strip()
                model_name.append(model)

        for i in table:
            for e in i.select("div.inner_inner img") :
                link = e['src']
                image_link.append(link)

        for i in table :
            for e in i.select("div.it_name") :
                description = e.get_text()
                description_list.append(description)

        for i in table :
            for e in i.select("div.inner_inner a") :
                access_link = e['href']
                access_link_list.append(access_link)

        df = pd.DataFrame({"모델명" : model_name, "링크주소" : image_link, "상세정보" : description_list, "접속링크" : access_link_list})


        image_link_address = df[df['모델명']  == item_name]['링크주소']
        if not image_link_address.empty:
            image_link_address = image_link_address.values[0]
        else:
            image_link_address = ""

        description_list_df = df[df['모델명']  == item_name]['상세정보']
        if not description_list_df.empty:
            description_list_df = description_list_df.values[0]
        else:
            description_list_df = ""

        access_link_list_df = df[df['모델명']  == item_name]['접속링크']
        if not access_link_list_df.empty:
            access_link_list_df = access_link_list_df.values[0]
        else:
            access_link_list_df = ""



        try : 
            product_url = access_link_list_df
            stock = session.get(product_url)
            soup = BeautifulSoup(stock.text, 'html.parser')
            access_link_table = soup.select("#goods_price_inner tr")

            for i in access_link_table :
                for e in i.select("#erpchk") :
                    stocks = e.get_text().split()
                    if stocks[0] == "총재고" :
                        total_stocks = stocks[2]
                        
        except MissingSchema:
            total_stocks = ""


        final_model_name.append(item_name)
        final_link_address.append(image_link_address)
        final_description_list.append(description_list_df)
        final_stock_list.append(total_stocks)

    final_df = pd.DataFrame( {"모델명" : final_model_name, "상세정보" : final_description_list, "총재고" : final_stock_list, "이미지주소" : final_link_address})


    from IPython.display import display, HTML

    # 각 이미지 링크를 HTML 이미지 태그로 변환
    final_df['이미지주소'] = final_df['이미지주소'].apply(lambda x: f'<img src="{x}" width="100">')
    # 데이터프레임을 HTML로 변환
    html = final_df.to_html(escape=False)

    #with open('output.html', 'w') as f:
    #    f.write(html)

    return Markup(html)

if __name__ == "__main__":
    app.run(port=5000)
