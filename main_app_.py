# WEBサイト内の表記ゆれをチェック
# 検索結果の最後に『UnicodeDecodeError』が出るときありますが、動作に問題ないです。

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urldefrag, unquote
import re
import chardet

visited_pages = set()

def search_keywords(url, keywords, original_domain):
    # ドメインを比較する
    current_domain = urlparse(url).netloc
    if current_domain != original_domain:
        return

    # 既に訪問されたページかどうかを確認する
    # URLをデコードし、visited_pagesセットに追加する
    decoded_url = unquote(url)
    decoded_url = urldefrag(decoded_url).url
    if decoded_url in visited_pages:
        return
    visited_pages.add(decoded_url)

    # 指定されたURLに対してリクエストを行う
    page = requests.get(url)
    encoding = chardet.detect(page.content)['encoding']
    if encoding is None:
        encoding = 'utf-8'

    #  HTMLコンテンツのパース
    soup = BeautifulSoup(page.content.decode(encoding), 'html.parser')

    # 特定のHTMLタグ内の全テキストを検索
    texts = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    # すべてのタグのテキストを連結する
    text = '\n'.join([t.get_text() for t in texts])
    
    # 半角と全角のスペースを含むキーワードを特定する
    for keyword in keywords:
        if keyword in [' ', '\u3000']:
            text = text.replace(' ', '_').replace('\u3000', '_')
            keywords = ['_']
            break

    # テキストを行に分割する
    lines = text.splitlines()

    # キーワード検索する
    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword in line:
                # 行番号を表示する
                line_number = i + 1
                # キーワードを含む行を太字で表示する
                line = line.replace(keyword, f"\033[1m {keyword} \033[0m")
                print(f' {decoded_url}\r\n{line_number}行目\r\n', line ,'\r\n')

    # ページ内の全リンクを検索する
    links = soup.find_all('a')

    # リンクを繰り返し、各リンクに対して再帰的に関数を呼び出す
    for link in links:
        link_url = link.get('href')
        if link_url:
            if "#" in link_url:
                continue
            if link_url.startswith('http') and re.search(original_domain, link_url):
                search_keywords(link_url, keywords, original_domain)

                
######### 以下に検索したいURLを入れてください ########
######### （例）https://●●●.com #########
url = 'https://tokyo-dc-idogaya.jp/wp/'

######## 以下に検索したい表記ゆれを入れてください ########
keywords = [chr(i) for i in range(65296, 65296 + 26 + 26 + 10)]

# ['患者様' , '患者さま', '患者さん']
# ['カ月' , 'ヶ月', 'ヵ月', 'か月']
# ['お母様' , 'お母さま', 'お母さん']
# ['皆様' , '皆さま', 'みなさま', 'みなさん', '皆さん']
# ['お子様' , 'お子さま', 'お子さん', 'お子さま', '子どもさん', 'こどもさん']
# ['子供' , '子ども', 'こども']
# ['当院' , '当クリニック']
# ['致し' , 'いたし']
# ['事' , 'こと']
# ['頂' , 'いただ']
# ['下さ' , 'くださ']
# ['行な' , '行']
# ['参りま' , 'まいりま']
# ['むし歯' , '虫歯']
# ['根管' , '根幹']
# ['骨粗鬆症' , '骨粗しょう症']
# ['癌' , 'がん', 'ガン']
# ['ドック' , 'ドッグ']
# ['●●●', 'xxx']
# [' ', '　']
### 以下は全角英数字を探します
# [chr(i) for i in range(65296, 65296 + 26 + 26 + 10)]

######## 以下は指定したドメイン以外の検索を行わないようにするための設定です ########
######## これを設定しないと、リンク先のURL（外部リンク）をどこまでも検索し永遠に終わらなくなります ########
######### （例）●●●.com #########
domain = 'tokyo-dc-idogaya.jp'

search_keywords(url , keywords, domain)