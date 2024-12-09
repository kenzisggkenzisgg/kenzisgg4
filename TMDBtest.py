import streamlit as st
import requests

# TMDB APIキー
TMDB_API_KEY = "054f72271ae8d8ea2beea5ae520ca6d2"

def search_movie_by_title(api_key, movie_title):
    """映画タイトルから映画IDを検索"""
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": api_key,
        "query": movie_title,
        "language": "ja"
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return None, "該当する映画が見つかりませんでした。"
        
        first_result = results[0]
        return first_result.get("id"), None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTPエラー: {e}"
    except Exception as e:
        return None, f"エラー: {e}"

def get_movie_details_with_crew_and_reviews(api_key, movie_id):
    """映画IDから詳細情報、製作者、出演俳優、レビュー情報を取得"""
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
    reviews_url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews"
    movie_params = {"api_key": api_key, "language": "ja"}
    credits_params = {"api_key": api_key, "language": "ja"}
    
    try:
        # 映画の基本情報を取得
        movie_response = requests.get(movie_url, params=movie_params)
        movie_response.raise_for_status()
        movie_data = movie_response.json()
        
        # 映画の出演者・製作者情報を取得
        credits_response = requests.get(credits_url, params=credits_params)
        credits_response.raise_for_status()
        credits_data = credits_response.json()
        
        # 映画のレビュー情報を取得（まず日本語を試す）
        reviews_params = {"api_key": api_key, "language": "ja"}
        reviews_response = requests.get(reviews_url, params=reviews_params)
        reviews_data = reviews_response.json()
        reviews = reviews_data.get("results", [])
        
        # 日本語レビューがない場合、英語のレビューを試す
        if not reviews:
            reviews_params["language"] = "en-US"
            reviews_response = requests.get(reviews_url, params=reviews_params)
            reviews_data = reviews_response.json()
            reviews = reviews_data.get("results", [])
        
        # 必要な情報を整理
        details = {
            "original_title": movie_data.get('original_title', '原題不明'),
            "title": movie_data.get('title', 'タイトル不明'),
            "overview": movie_data.get('overview', '概要なし'),
            "release_date": movie_data.get('release_date', 'リリース日不明'),
            "runtime": movie_data.get('runtime', 0),
            "vote_average": movie_data.get('vote_average', 0.0),
            "vote_count": movie_data.get('vote_count', 0),
            "poster_path": movie_data.get('poster_path'),
            "crew": [
                {
                    "name": member.get("name", "名前不明"),
                    "job": member.get("job", "役割不明")
                }
                for member in credits_data.get("crew", [])
                if member.get("job") in ["Director", "Screenplay", "Producer", "Writer"]
            ],
            "cast": [
                {
                    "name": actor.get("name", "名前不明"),
                    "character": actor.get("character", "役柄不明"),
                    "profile_url": f"https://image.tmdb.org/t/p/w500{actor.get('profile_path')}" if actor.get("profile_path") else "プロフィール画像なし"
                }
                for actor in credits_data.get("cast", [])[:5]
            ],
            "reviews": [
                {
                    "author": review.get("author", "匿名"),
                    "content": review.get("content", "レビューなし")
                }
                for review in reviews[:3]  # 最大3件表示
            ]
        }
        
        return details
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTPエラー: {e}"}
    except Exception as e:
        return {"error": f"エラー: {e}"}
    # Streamlitアプリの構成
st.title("映画情報検索アプリ")
st.write("映画のタイトルを入力して、詳細情報を取得してください。")

# ユーザーが映画タイトルを入力
movie_title = st.text_input("映画タイトルを入力してください:")

if movie_title:
    with st.spinner("検索中..."):
        movie_id, error = search_movie_by_title(TMDB_API_KEY, movie_title)
        if error:
            st.error(error)
        else:
            movie_details = get_movie_details_with_crew_and_reviews(TMDB_API_KEY, movie_id)
            if "error" in movie_details:
                st.error(movie_details["error"])
            else:
                st.subheader(f"{movie_details['title']} ({movie_details['original_title']})")
                poster_url = (
                    f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}"
                    if movie_details['poster_path'] else "ポスター画像が見つかりませんでした。"
                )
                st.image(poster_url, width=300)
                st.write(f"**概要:** {movie_details['overview']}")
                st.write(f"**リリース日:** {movie_details['release_date']}")
                runtime = movie_details["runtime"]
                hours, minutes = divmod(runtime, 60)
                runtime_str = f"{hours}時間 {minutes}分" if runtime > 0 else "情報なし"
                st.write(f"**映画の長さ:** {runtime_str}")
                st.write(f"**評価スコア:** {movie_details['vote_average']} / 10")
                st.write(f"**評価数:** {movie_details['vote_count']}件")
                
                st.write("### 製作者")
                for member in movie_details["crew"]:
                    st.write(f"- {member['job']}: {member['name']}")
                
                st.write("### 主演俳優")
                for actor in movie_details["cast"]:
                    st.write(f"- {actor['name']} ({actor['character']})")
                    if actor["profile_url"] != "プロフィール画像なし":
                        st.image(actor["profile_url"], width=100)
                
                st.write("### レビュー")
                reviews = movie_details["reviews"]
                if reviews:
                    for idx, review in enumerate(reviews, start=1):
                        st.write(f"**{idx}. {review['author']}さんのレビュー:**")
                        st.write(f"{review['content']}")
                        st.write("---")
                else:
                    st.write("レビューは見つかりませんでした。")


