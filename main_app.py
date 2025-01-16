# WEBサイト内の表記ゆれをチェック
# 検索結果の最後に『UnicodeDecodeError』が出るときありますが、動作に問題ないです。

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import chardet
from PIL import Image
import time
import re
from urllib.parse import urlparse, urldefrag, unquote, urljoin, quote

# セッション状態の初期化
if 'results' not in st.session_state:
    st.session_state['results'] = {}
if 'search_finished' not in st.session_state:
    st.session_state['search_finished'] = False
if 'search_started' not in st.session_state:
    st.session_state['search_started'] = False

visited_pages = set()
max_depth = 4  # 最大探索深度を設定

def normalize_url(url):
    # URLをデコードしてから再エンコード
    decoded_url = unquote(url)
    url = quote(decoded_url, safe=':/?=&')
    # フラグメント識別子（アンカーリンク）を削除
    url = url.split('#')[0]
    # クエリパラメータを削除
    url = url.split('?')[0]
    # 末尾のスラッシュを削除（ただし、/wp/は保持）
    if not url.endswith('/wp/'):
        url = re.sub(r'/+$', '', url)
    # 末尾の引用符を削除
    url = url.rstrip('"')
    return url

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# 進捗状況を表示する関数
def update_progress(message):
    if 'progress_placeholder' not in st.session_state:
        st.session_state.progress_placeholder = st.empty()
    st.session_state.progress_placeholder.text(message)

def search_keywords(url, keywords, original_domain, depth=0):
    if depth > max_depth:
        return {}

    url = normalize_url(url)
    update_progress(f"処理中のURL: {url} (深さ: {depth})")

    try:
        # URLの検証
        if not is_valid_url(url):
            return {}

        # ドメインを比較する
        current_domain = urlparse(url).netloc
        if current_domain != original_domain:
            return {}

        # 既に訪問されたページかどうかを確認する
        if url in visited_pages:
            return {}
        visited_pages.add(url)

        # 指定されたURLに対してリクエストを行う
        page = requests.get(url, timeout=10)
        page.raise_for_status()  # HTTPエラーをチェック

        # HTMLコンテンツのパース
        soup = BeautifulSoup(page.content, 'html.parser')
        
        # 特定のHTMLタグ内の全テキストを検索
        texts = soup.find_all(string=True)

        # すべてのタグのテキストを連結する
        text = '\n'.join([t.get_text() for t in texts])
        
        # 半角と全角のスペースを含むキーワードを特定する
        search_keywords_list = keywords.copy()

        # テキストを行に分割する
        lines = text.splitlines()

        # キーワード検索する
        results = {keyword: [] for keyword in keywords}
        full_width_results = {}  # 全角英数字の結果を格納する辞書

        for i, line in enumerate(lines):
            for keyword in keywords:
                if keyword == full_width_alphanumeric:
                    for char in full_width_alphanumeric:
                        if char in line:
                            line_number = i + 1
                            highlighted_line = line.replace(char, f"<span style='color:red;'>{char}</span>")
                            decoded_url = unquote(url)  # URLをデコード
                            result = f"'{char}' : {decoded_url} ({line_number}行目)\r\n{highlighted_line}\r\n"
                            if url not in full_width_results:
                                full_width_results[url] = []
                            full_width_results[url].append(result)
                elif keyword in line:
                    line_number = i + 1
                    display_keyword = '_' if keyword == ' ' else '＿' if keyword == '\u3000' else keyword
                    highlighted_line = line.replace(keyword, f"<span style='color:red;'>{display_keyword}</span>")
                    decoded_url = unquote(url)  # URLをデコード
                    result = f"'<span style='color:red;'>{keyword}</span>' : {decoded_url} ({line_number}行目)\r\n{highlighted_line}\r\n"
                    results[keyword].append(result)
                elif keyword in line:
                    line_number = i + 1
                    display_keyword = '_' if keyword == ' ' else '＿' if keyword == '\u3000' else keyword
                    highlighted_line = line.replace(keyword, f"<span style='color:red;'>{display_keyword}</span>")
                    result = f"'<span style='color:red;'>{keyword}</span>' : {url} ({line_number}行目)\r\n{highlighted_line}\r\n"
                    results[keyword].append(result)

        # 全角英数字の結果を results に追加
        if full_width_results:
            results[full_width_alphanumeric] = full_width_results

        # 空の結果を削除
        results = {k: v for k, v in results.items() if v}

        # ページ内の全リンクを検索する
        links = soup.find_all('a')

        # リンクを繰り返し、各リンクに対して再帰的に関数を呼び出す
        for link in links:
            link_url = link.get('href')
            if link_url:
                # URLが相対パスの場合、絶対URLに変換する
                if not link_url.startswith('http'):
                    link_url = urljoin(url, link_url)
                link_url = normalize_url(link_url)
                # 電話番号のリンクを除外
                if link_url.startswith('tel:'):
                    continue
                # ドメインが一致し、有効なURLの場合のみ再帰的に関数を呼び出す
                if urlparse(link_url).netloc == original_domain and is_valid_url(link_url):
                    new_results = search_keywords(link_url, keywords, original_domain, depth + 1)
                    if new_results:  # 空の辞書をチェック
                        for keyword, new_result in new_results.items():
                            if keyword in results:
                                if keyword == full_width_alphanumeric:
                                    results[keyword].update(new_result)
                                else:
                                    results[keyword].extend(new_result)
                            else:
                                results[keyword] = new_result

        return results  # 辞書を返す

    except requests.RequestException:
        pass
    except Exception:
        pass

    return results

def start_search(url, keywords, domain):
    results = search_keywords(url, keywords, domain)
    st.success('検索が終了しました。')
    return results

# Streamlitのタイトル設定
st.title('WEBサイト内の表記ゆれチェック')
st.markdown('▼ver1.0.6/2025.01.17  \n・Streamlitの仕様に合わせて修正を行ないました  \n\n▼ver1.0.5/2024.08.29  \n・「全てのキーワードをチェック」を追加して全部チェックできるようになりました！  \n・「全て解除」を1回ポチるだけで全解除されるようになりました！')

# 画像
image = Image.open('ima01.jpg')
st.image(image, use_container_width=True)

# ユーザーが入力する欄
url = st.text_input('検索するURLを入力してください', '')

domain = st.text_input('検索したいURLのドメインを入力してください', '')

# 全角英数字を一つの文字列として生成
full_width_alphanumeric = ''.join([chr(i) for i in range(65296, 65296 + 26 + 26 + 10)])

keywords = []
keyword_options = ['患者様' , '患者さま', '患者さん', 'カ月' , 'ヶ月', 'ヵ月', 'か月', 'お母様' , 'お母さま', 'お母さん', '皆様' , '皆さま', 'みなさま', 'みなさん', '皆さん', 'お子様' , 'お子さま', 'お子さん', 'お子さま', '子どもさん', 'こどもさん', '子供' , '子ども', 'こども', '当院' , '当クリニック', '致し' , 'いたし', '事' , 'こと', '頂' , 'いただ', '下さ' , 'くださ', '行な' , '行', '参りま' , 'まいりま', 'むし歯' , '虫歯', '根管' , '根幹', '骨粗鬆症' , '骨粗しょう症', '癌' , 'がん', 'ガン', 'ドック' , 'ドッグ', '●●●', 'xxx', ' ', '　', full_width_alphanumeric]

# チェックボックスの状態を管理するためのSession Stateを初期化
if 'checkbox_states' not in st.session_state:
    st.session_state['checkbox_states'] = [False] * len(keyword_options)

# チェックされたキーワードの順序を保持するリスト
if 'checked_keywords_order' not in st.session_state:
    st.session_state['checked_keywords_order'] = []

# 3列のレイアウトを作成
col1, col2, col3 = st.columns(3)

# 全て解除フラグの初期化
if 'reset_all' not in st.session_state:
    st.session_state.reset_all = False

# 全てチェックフラグの初期化
if 'check_all' not in st.session_state:
    st.session_state.check_all = False

# 全てのキーワードをチェックするオプションを追加
all_checked = st.checkbox('全てのキーワードをチェック', key='all_checked', 
                          value=st.session_state.check_all)

# 全てチェックの状態が変更された場合、再実行
if all_checked != st.session_state.check_all:
    st.session_state.check_all = all_checked
    st.session_state.reset_all = False
    st.rerun()

# 各キーワードに対してチェックボックスを作成
for i, option in enumerate(keyword_options):
    # チェックボックスを配置するカラムを決定
    if i % 3 == 0:
        col = col1
    elif i % 3 == 1:
        col = col2
    else:
        col = col3
    
    # チェックボックスの初期状態を設定
    if st.session_state.reset_all:
        initial_state = False
    else:
        initial_state = all_checked or st.session_state.get(f"{option}-{i}", False)
    
    # チェックボックスを作成し、状態をSession Stateから取得
    checkbox_state = col.checkbox(option, key=f"{option}-{i}", value=initial_state)
    
    if checkbox_state:
        if option not in keywords:
            keywords.append(option)
        if option not in st.session_state['checked_keywords_order']:
            st.session_state['checked_keywords_order'].append(option)
    else:
        if option in keywords:
            keywords.remove(option)
        if option in st.session_state['checked_keywords_order']:
            st.session_state['checked_keywords_order'].remove(option)

# 全てのチェックボックスを解除するボタンを作成
if st.button('全て解除'):
    st.session_state.reset_all = True
    st.session_state.check_all = False
    st.rerun()

# リセットフラグをクリア
if st.session_state.reset_all:
    st.session_state.reset_all = False
    keywords.clear()
    st.session_state['checked_keywords_order'] = []

st.markdown('<span style="color:red; font-size:14px">※「全て解除」ボタンを押すと、全てのチェックが解除されます。</span>', unsafe_allow_html=True)

# 追加キーワードの状態を保存するためのSession State
if 'additional_keywords' not in st.session_state:
    st.session_state.additional_keywords = ''

# 追加キーワード入力欄
additional_keywords = st.text_area('他に検索したいキーワードがあれば、各キーワードを新しい行に入力してください', 
                                   value=st.session_state.additional_keywords)

# 追加キーワードの状態を更新
if additional_keywords != st.session_state.additional_keywords:
    st.session_state.additional_keywords = additional_keywords

# キーワードリストの更新
keywords = [option for i, option in enumerate(keyword_options) if st.session_state.get(f"{option}-{i}", False)]
additional_keywords_list = []
if st.session_state.additional_keywords:
    additional_keywords_list = [kw.strip() for kw in st.session_state.additional_keywords.splitlines() if kw.strip()]
    keywords.extend(additional_keywords_list)

# 検索時に全角英数字を一文字ずつ検索する
search_keywords_list = []
for keyword in keywords:
    if keyword == full_width_alphanumeric:
        search_keywords_list.extend(list(full_width_alphanumeric))
    else:
        search_keywords_list.append(keyword)
        
if st.button('検索開始'):
    with st.spinner('検索中...キーワードごとにカテゴライズしてるから、ちょっと待っててね！ฅ^•ω•^ฅ'):
        start_time = time.time()
        results = search_keywords(url, search_keywords_list, domain)
        end_time = time.time()
        if results:  # 結果が空でない場合のみ結果を保存
            # 全角英数字の結果を一つにまとめる
            if full_width_alphanumeric in keywords:
                full_width_results = {}
                for char in full_width_alphanumeric:
                    if char in results:
                        if isinstance(results[char], list):
                            for result in results[char]:
                                url = result.split(' : ')[1].split(' (')[0]
                                if url not in full_width_results:
                                    full_width_results[url] = []
                                full_width_results[url].append(result)
                        elif isinstance(results[char], dict):
                            for url, url_results in results[char].items():
                                if url not in full_width_results:
                                    full_width_results[url] = []
                                full_width_results[url].extend(url_results)
                        del results[char]
                if full_width_results:
                    results[full_width_alphanumeric] = full_width_results
            
            # 追加キーワードの結果を処理
            for keyword in additional_keywords_list:
                if keyword in results:
                    if keyword not in st.session_state['checked_keywords_order']:
                        st.session_state['checked_keywords_order'].append(keyword)

            st.session_state['results'] = results
            st.session_state['search_finished'] = True
            st.session_state['search_started'] = True
            st.success(f'検索が終了しました。処理時間: {end_time - start_time:.2f}秒')
        else:
            st.session_state['search_started'] = True
            st.session_state['search_finished'] = False
            st.error('該当するキーワードが見つかりませんでした。')

# 検索結果の表示
if 'results' in st.session_state and st.session_state['results']:
    # チェックされたキーワードの順序に基づいて結果を表示
    for keyword in st.session_state.get('checked_keywords_order', []):
        if keyword in st.session_state['results'] and st.session_state['results'][keyword]:
            results = st.session_state['results'][keyword]
            if keyword == full_width_alphanumeric:
                st.markdown(f"<h2 style='font-weight: bold; font-size: 20px;'>全角英数字の検索結果：</h2>", unsafe_allow_html=True)
                for url, url_results in results.items():
                    decoded_url = unquote(url)  # URLをデコード
                    st.markdown(f"<h3 style='font-weight: bold; font-size: 18px;'>URL: {decoded_url}</h3>", unsafe_allow_html=True)
                    for result in url_results:
                        st.markdown(result, unsafe_allow_html=True)
            else:
                num_results = len(results)
                st.markdown(f"<h2 style='font-weight: bold; font-size: 20px;'>キーワード '{keyword}' の検索結果 ({num_results}件)：</h2>", unsafe_allow_html=True)
                for result in results:
                    st.markdown(result, unsafe_allow_html=True)
    
    # 追加キーワードの結果を表示
    for keyword in additional_keywords_list:
        if keyword in st.session_state['results'] and st.session_state['results'][keyword]:
            results = st.session_state['results'][keyword]
            num_results = len(results)
            st.markdown(f"<h2 style='font-weight: bold; font-size: 20px;'>キーワード '{keyword}' の検索結果 ({num_results}件)：</h2>", unsafe_allow_html=True)
            for result in results:
                st.markdown(result, unsafe_allow_html=True)

elif st.session_state.get('search_started', False):
    st.error('該当するキーワードが見つかりませんでした。')

# 検索が終了したときにメッセージを表示
if st.session_state['search_finished']:
    st.success('検索が終了しました。')
    st.session_state['search_finished'] = False  # フラグをリセット

# 2列のレイアウトを作成
col1, col2 = st.columns(2)