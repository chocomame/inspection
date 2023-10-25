# WEBサイト内の表記ゆれをチェック
# 検索結果の最後に『UnicodeDecodeError』が出るときありますが、動作に問題ないです。

import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urldefrag, unquote
import re
import chardet
from PIL import Image

visited_pages = set()

def search_keywords(url, keywords, original_domain):
    # ドメインを比較する
    current_domain = urlparse(url).netloc
    if current_domain != original_domain:
        st.write(f"ドメインが一致しません: {current_domain} != {original_domain}")
        return []

    # 既に訪問されたページかどうかを確認する
    # URLをデコードし、visited_pagesセットに追加する
    decoded_url = unquote(url)
    decoded_url = urldefrag(decoded_url).url
    if decoded_url in visited_pages:
        return []
    visited_pages.add(decoded_url)

    # 指定されたURLに対してリクエストを行う
    page = requests.get(url)
    encoding = chardet.detect(page.content)['encoding']
    if encoding is None:
        encoding = 'utf-8'

    #  HTMLコンテンツのパース
    soup = BeautifulSoup(page.content.decode(encoding), 'html.parser')

    # 特定のHTMLタグ内の全テキストを検索
    # texts = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    texts = soup.find_all(text=True)

    # すべてのタグのテキストを連結する
    text = '\n'.join([t.get_text() for t in texts])
    
    # 半角と全角のスペースを含むキーワードを特定する
    search_keywords_list = keywords.copy()
    #for keyword in keywords:
    #    if keyword in [' ', '\u3000']:
    #        text = text.replace(' ', '_').replace('\u3000', '_')
    #        search_keywords_list = ['_']
    #        break

    # デバッグ情報の表示
    #st.write(f"検索キーワードリスト: {search_keywords_list}")

    # テキストを行に分割する
    lines = text.splitlines()

    # キーワード検索する
    if full_width_alphanumeric in search_keywords_list:
        # 全角半角英数字が選択された時だけ、結果をURLごとにカテゴライズ
        results = {decoded_url: []}
    else:
        # それ以外の場合は、結果をキーワードごとにカテゴライズ
        results = {keyword: [] for keyword in search_keywords_list}
        
    # 全角英数字の各文字をキーとして追加
    if full_width_alphanumeric in search_keywords_list:
        for char in full_width_alphanumeric:
            results[char] = []

    for i, line in enumerate(lines):
        for keyword in search_keywords_list:
            # 全角英数字を一文字ずつ検索する
            if keyword in full_width_alphanumeric:
                for char in keyword:
                    if char in line:
                        # 行番号を表示する
                        line_number = i + 1
                        # キーワードを含む行を赤色で表示する
                        line = line.replace(char, f"<span style='color:red;'>{char}</span>")
                        # 結果のフォーマットを変更
                        result = f"'<span style='color:red;'>{char}</span>' : {decoded_url} ({line_number}行目)\r\n{line}\r\n"
                        results[decoded_url].append(result)
            else:
                if keyword in line:
                    # 行番号を表示する
                    line_number = i + 1
                    # キーワードを含む行を赤色で表示する
                    if keyword == ' ':
                        display_keyword = '_'
                    elif keyword == '\u3000':
                        display_keyword = '＿'
                    else:
                        display_keyword = keyword
                    line = line.replace(keyword, f"<span style='color:red;'>{display_keyword}</span>")
                    # 結果のフォーマットを変更
                    result = f"'<span style='color:red;'>{keyword}</span>' : {decoded_url} ({line_number}行目)\r\n{line}\r\n"
                    if keyword in results:
                        results[keyword].append(result)
                    else:
                        results[keyword] = [result]
                
    # ページ内の全リンクを検索する
    links = soup.find_all('a')

    # リンクを繰り返し、各リンクに対して再帰的に関数を呼び出す
    for link in links:
        link_url = link.get('href')
        if link_url:
            if "#" in link_url:
                continue
            if link_url.startswith('http') and re.search(original_domain, link_url):
                st.session_state['results'].update(search_keywords(link_url, search_keywords_list, original_domain))
    return results

def start_search(url, keywords, domain):
    results = search_keywords(url, keywords, domain)
    st.success('検索が終了しました。')
    return results

# Streamlitのタイトル設定
st.title('WEBサイト内の表記ゆれをチェック')
st.markdown('選択されたキーワードごとにカテゴライズされるので、多いキーワードがどれかを判断しやすくなりました！  \n全角英数字を選択した場合のみ、ページごとのカテゴライズになり作業しやすくしています。  \nฅ^• ·̫ •^ฅ')

# 画像
image = Image.open('ima01.jpg')
st.image(image,use_column_width=True)

# ユーザーが入力する欄
url = st.text_input('検索するURLを入力してください', '')
# 全角英数字を一つの文字列として生成
full_width_alphanumeric = ''.join([chr(i) for i in range(65296, 65296 + 26 + 26 + 10)])

keywords = st.multiselect('検索したいキーワードを選択してください', ['患者様' , '患者さま', '患者さん', 'カ月' , 'ヶ月', 'ヵ月', 'か月', 'お母様' , 'お母さま', 'お母さん', '皆様' , '皆さま', 'みなさま', 'みなさん', '皆さん', 'お子様' , 'お子さま', 'お子さん', 'お子さま', '子どもさん', 'こどもさん', '子供' , '子ども', 'こども', '当院' , '当クリニック', '致し' , 'いたし', '事' , 'こと', '頂' , 'いただ', '下さ' , 'くださ', '行な' , '行', '参りま' , 'まいりま', 'むし歯' , '虫歯', '根管' , '根幹', '骨粗鬆症' , '骨粗しょう症', '癌' , 'がん', 'ガン', 'ドック' , 'ドッグ', '●●●', 'xxx', ' ', '　', full_width_alphanumeric])
additional_keywords = st.text_area('他に検索したいキーワードがあれば、各キーワードを新しい行に入力してください', '')
if additional_keywords:
    keywords.extend(additional_keywords.splitlines())
domain = st.text_input('検索したいURLのドメインを入力してください', '')

# 検索結果と検索終了フラグを保存するためのSession Stateを初期化
if 'results' not in st.session_state:
    st.session_state['results'] = {}  # 辞書型に変更
if 'search_finished' not in st.session_state:
    st.session_state['search_finished'] = False
if 'search_started' not in st.session_state:  # 新しいセッションステート変数を追加
    st.session_state['search_started'] = False

# 検索時に全角英数字を一文字ずつ検索する
search_keywords_list = []
for keyword in keywords:
    if keyword == full_width_alphanumeric:
        search_keywords_list.extend(list(full_width_alphanumeric))
    else:
        search_keywords_list.append(keyword)
        
if st.button('検索開始'):
    with st.spinner('検索中...キーワードごとにカテゴライズしてるから、ちょっと待っててね！ฅ^•ω•^ฅ'):
        results = search_keywords(url, keywords, domain)
    st.session_state['results'] = results
    st.session_state['search_finished'] = True  # 検索が終了したことを示すフラグを更新
    st.session_state['search_started'] = True  # 検索が開始したことを示すフラグを更新

# 検索結果の表示
if st.session_state['search_finished']:  # 検索が終了したときだけ結果を表示
    for keyword, results in st.session_state['results'].items():
        if results:  # 結果が存在する場合のみ表示
            # URLの場合は表示を変更
            if keyword.startswith('http'):
                st.markdown(f"<h2 style='font-weight: bold; font-size: 18px;'>URL '{keyword}' の検索結果：</h2>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h2 style='font-weight: bold; font-size: 18px;'>キーワード '{keyword}' の検索結果：</h2>", unsafe_allow_html=True)
            for result in results:
                st.markdown(result, unsafe_allow_html=True)
elif not st.session_state['results'] and st.session_state['search_started']:  # 検索が開始されたときだけエラーメッセージを表示
    st.error('該当するキーワードが見つかりませんでした。')

# 検索が終了したときにメッセージを表示
if st.session_state['search_finished']:
    st.success('検索が終了しました。')
    st.session_state['search_finished'] = False  # フラグをリセット
        