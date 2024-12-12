import requests
import streamlit as st
import difflib

# APIキーを指定
api_key = "054f72271ae8d8ea2beea5ae520ca6d2"

# Streamlitアプリの構成
st.title("映画情報検索アプリ")
st.write("映画のタイトルを入力して、詳細情報を取得してください。")

# ユーザーが映画タイトルを入力
movie_title = st.text_input("") #説明なくてもよさそうなので空欄

#ユーザー入力前、APIリクエストをスキップするように条件分岐を追加
if movie_title:
    title = movie_title

    # APIのURLを生成
    search_url = "https://api.themoviedb.org/3/search/movie"
    search_params = {
        "api_key": api_key,
        "query": title,
        "include_adult": "false",
        "language": "ja",
    }

    # APIを呼び出す(映画ID取得用)
    search_response = requests.get(search_url, params=search_params)
    if search_response.status_code == 200:
        search_data = search_response.json()

        # タイトルの類似度を評価して最も近い映画を選択
        def get_title_similarity(s1, s2):
            return difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

        most_similar_movie = max(
            search_data["results"],
            key=lambda movie: get_title_similarity(movie["title"], title)
        )
        movie_id = most_similar_movie["id"]

        # 映画詳細情報の取得
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        detail_params = {"api_key": api_key, "language": "ja"}
        detail_response = requests.get(detail_url, params=detail_params)
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            
              # ポスター情報の取得
            images_url = f"https://api.themoviedb.org/3/movie/{movie_id}/images"
            poster_size = "w300" 

            images_params = {
                "api_key": api_key, 
                "include_image_language": "ja",
            }   
            images_response = requests.get(images_url, images_params)
            if images_response.status_code == 200:
                images_data = images_response.json()
                posters = images_data.get("posters", [])
                if posters:
                    file_path = posters[0].get("file_path")
                    full_image_url = f"https://image.tmdb.org/t/p/{poster_size}{file_path}"  # フルURLを構築st.write("### 映画情報")
                    
            #映画情報とポスターを表示
            st.subheader(f"{detail_data['title']} ({detail_data['original_title']})")
            if full_image_url:
                st.image(full_image_url)
            st.write(f" {detail_data.get('overview', 'N/A')}")
            st.write(f"**公開日**: {detail_data.get('release_date', 'N/A')}")
            st.write(f"**上映時間**: {detail_data.get('runtime', 'N/A')} 分")


            
        # 製作者、キャスト情報の取得
        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
        credits_params = {"api_key": api_key, "language": "ja"}
        credits_response = requests.get(credits_url, params=credits_params)
        if credits_response.status_code == 200:
            credits_data = credits_response.json()
            
            st.write("### 製作者情報")
            crew = credits_data.get("crew", []) 
            filtered_roles = ["Director", "Screenplay", "Producer", "Writer", "Composer"]
            filtered_crew = [
            member for member in crew if member.get("job") in filtered_roles
            ]
            for member in filtered_crew[:5]:  # 上位5人まで
                name = member.get("name", "N/A")
                job = member.get("job", "N/A")
                st.write(f"- {job}:{name}")

            st.write("### キャスト情報")
            cast = credits_data.get("cast", [])
            for actor in cast[:5]:
                name = actor.get("name", "N/A")
                character = actor.get("character", "N/A")
                profile_path = actor.get("profile_path", None)
                st.write((f"- {name} ( {character} )"))
                if profile_path:
                    profile_url = f"https://image.tmdb.org/t/p/w200{profile_path}"
                    st.image(profile_url,width=100)  
                    #画像サイズが大きかったので調整（url部分を直そうとしたらエラーとなったので、ここで調整）
                else:
                    st.write("(No image available)")

    else:
        st.write("映画情報の取得に失敗しました。")
   
    #　レビュー情報の取得
    reviews_url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews"
    reviews_params = {
        "api_key": api_key, 
        "language": "en-US",
    }    
    
    reviews_response = requests.get(reviews_url, params= reviews_params)

    reviews_data = reviews_response.json()
    reviews = reviews_data.get("results",[])
    if reviews:
        st.write("### レビュー")
        for review in reviews[:3]: 
            author = review.get("author", "Unknown")
            content = review.get("content", "No content")
            st.write(f"**Reviewer :  {author}さんのレビュー**")
            st.write(f"Review :  {content}\n")
    else:
        st.write("None")
else:
    st.write("") #説明なくてもよさそうなので空欄
    