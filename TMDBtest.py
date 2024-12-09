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

def get_movie_details_with_crew_and_cast(api_key, movie_id):
    """映画IDから詳細情報、製作者、主演俳優情報を取得"""
    config_url = f"https://api.themoviedb.org/3/configuration"
    config_params = {"api_key": api_key}
    
    try:
        config_response = requests.get(config_url, params=config_params)
        config_response.raise_for_status()
        config_data = config_response.json()
        
        base_url = config_data['images']['secure_base_url']
        poster_size = "w500"
        
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        movie_params = {"api_key": api_key, "language": "ja"}
        
        movie_response = requests.get(movie_url, params=movie_params)
        movie_response.raise_for_status()
        movie_data = movie_response.json()
        
        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
        credits_params = {"api_key": api_key, "language": "ja"}
        credits_response = requests.get(credits_url, params=credits_params)
        credits_response.raise_for_status()
        credits_data = credits_response.json()
        
        original_title = movie_data.get('original_title', '原題不明')
        title = movie_data.get('title', 'タイトル不明')
        overview = movie_data.get('overview', '概要なし')
        release_date = movie_data.get('release_date', 'リリース日不明')
        runtime = movie_data.get('runtime', 0)  # 映画の長さ（分）
        hours, minutes = divmod(runtime, 60)  # 分を「時間:分」に変換
        runtime_str = f"{hours}時間 {minutes}分" if runtime > 0 else "情報なし"
        poster_path = movie_data.get('poster_path')
        poster_url = f"{base_url}{poster_size}{poster_path}" if poster_path else "ポスター画像が見つかりませんでした。"
        
        crew = [
            {
                "name": member.get("name", "名前不明"),
                "job": member.get("job", "役割不明")
            }
            for member in credits_data.get("crew", [])
            if member.get("job") in ["Director", "Screenplay", "Producer", "Writer"]
        ]
        
        cast = [
            {
                "name": actor.get("name", "名前不明"),
                "character": actor.get("character", "役柄不明"),
                "profile_url": f"{base_url}{poster_size}{actor.get('profile_path')}" if actor.get('profile_path') else "プロフィール画像なし"
            }
            for actor in credits_data.get("cast", [])[:5]
        ]
        
        return {
            "original_title": original_title,
            "title": title,
            "overview": overview,
            "release_date": release_date,
            "runtime": runtime_str,  # 映画の長さ（文字列形式）
            "poster_url": poster_url,
            "crew": crew,
            "cast": cast
        }
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
            movie_details = get_movie_details_with_crew_and_cast(TMDB_API_KEY, movie_id)
            if "error" in movie_details:
                st.error(movie_details["error"])
            else:
                st.subheader(f"{movie_details['title']} ({movie_details['original_title']})")
                st.image(movie_details["poster_url"], width=300)
                st.write(f"**概要:** {movie_details['overview']}")
                st.write(f"**リリース日:** {movie_details['release_date']}")
                st.write(f"**映画の長さ:** {movie_details['runtime']}")  # 映画の長さを表示
                
                st.write("### 製作者")
                for member in movie_details["crew"]:
                    st.write(f"- {member['job']}: {member['name']}")
                
                st.write("### 主演俳優")
                for actor in movie_details["cast"]:
                    st.write(f"- {actor['name']} ({actor['character']})")
                    if actor["profile_url"] != "プロフィール画像なし":
                        st.image(actor["profile_url"], width=100)

