from flask import Flask, render_template, request
from markupsafe import Markup
import pandas as pd
import os
import logging
import requests
from tqdm import tqdm
from requests.exceptions import MissingSchema
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import pandas as pd

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
        result = "아직 파일이 업로드 되지 않았습니다."

    return render_template('index.html', result=result)



def process_file(filename):

    file_list = pd.read_excel(filename, header=0, sheet_name=0)
    find_prokit = file_list


    #######################################################################

    password = quote_plus('!!@Ll752515')

    # SQL에서 프로킷 / 컴스마트 정보 가져오기

    engine = create_engine(f'mysql+pymysql://fred:{password}@fred1234.synology.me/fred')
    query = """select `주문코드`, `바코드`, `상품명`, `모델명`, `총재고(H)`, `허브매장(U)`, `본사재고(B)`, `판매가`, ` 상품이미지1`  from comsmart_web """
    comsmart_df = pd.read_sql(query, con=engine)


    engine = create_engine(f'mysql+pymysql://fred:{password}@fred1234.synology.me/fred')
    query = """select * from prokit """
    prokit_df = pd.read_sql(query, con=engine)
    engine.dispose()


    # prokit 데이터프레임 정리하기
    prokit_df = prokit_df[['item_name', 'description','price','location','invoice_number','date','po']]

    # 열값 변경, 오름차순 정렬, date를 기준으로 가장 최근값 정렬, 2차 재정렬 = prokit_html_df
    prokit_df = prokit_df.rename(columns={'item_name' : '모델명'})
    prokit_df = prokit_df[prokit_df['모델명'].notna() & prokit_df['date'].notna()]  # 모델명과 date 모두 NaN 값이 아닌 행만 선택
    prokit_df = prokit_df.sort_values("date", ascending=False)
    idx = prokit_df.groupby("모델명")['date'].idxmax()
    prokit_df_latest = prokit_df.loc[idx]
    prokit_html_df = prokit_df_latest[['모델명','description','price','location']]


    prokit_html = find_prokit.merge(comsmart_df, on="모델명", how="left")
    prokit_html2 = prokit_html.merge(prokit_html_df, on="모델명", how="left")
    prokit_html2 = prokit_html2[['주문코드', '모델명', '바코드', '상품명','description', '총재고(H)', '허브매장(U)','본사재고(B)','판매가','price', 'location', ' 상품이미지1' ]]

    prokit_html2 = prokit_html2.fillna("")


    from IPython.display import display, HTML

    # 각 이미지 링크를 HTML 이미지 태그로 변환
    prokit_html2[' 상품이미지1'] = prokit_html2[' 상품이미지1'].apply(lambda x: f'<img src="{x}" width="100">')
    # 데이터프레임을 HTML로 변환
    html = prokit_html2.to_html(escape=False)

    css_style = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
    </style>
    """

    # CSS 스타일을 HTML에 적용합니다.
    html_with_style = css_style + html

    return Markup(html_with_style)


    #######################################################################

if __name__ == "__main__":
    app.run(port=5000)
