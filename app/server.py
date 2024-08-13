import sqlite3

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


# chainを定義
template = """
    ユーザーの嗜好に合わせて、次に渡す作品に採点してください。

    # 採点方法
    作品の内容を説明する文章を渡しますので、ユーザーの嗜好に合わせて、その作品を評価してください。
    ユーザーの嗜好については以下のようなオブジェクト形式で渡します。
    例:'素人:2,人妻:1,乱行:-2'
    -2,-1,0,1,2の5段階で、プラスは好き、マイナスは嫌いを示しています。
    単純に単語の有無で判断するのではなく、意味的な距離や上位・下位概念も加味してください

    # データ
    紹介文章:{description}
    ユーザーの嗜好:{preference}

    # 出力
    -2から2の5段階評価です。
    -2は嫌い、0は普通、2は好きです。
    数値だけを出力してください
"""

prompt = ChatPromptTemplate.from_template(template=template)



model =ChatOpenAI(model="gpt-4o-mini",openai_api_key=OPENAI_API_KET) # 自分自身のAPI KEYを入れてください

chain = prompt | model

# ユーザーの嗜好を定義
preference = {'素人':2,'美女':1,'乱行':-2}

# databaseを作成
@app.get("/setup_database")
async def setup_database():
    with sqlite3.connect('sample.db') as conn:
        c = conn.cursor()

        c.execute(f'''
            CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY AUTOINCREMENT,title STRING, description TEXT, ai_score TEXT)
        ''')

# 指定したidのデータを取得し、AIが評価をつける
@app.post("/set_score")
async def set_score(id:str):
    with sqlite3.connect('sample.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM movies WHERE id = ?',(id,))
        result = c.fetchone()

        id, title, description,ai_score = result

        res = chain.invoke(input={'preference':preference ,'description':title})

        ai_score = res.content

        c.execute('UPDATE movies SET ai_score = ? WHERE id = ?', (ai_score, id))


# add_routes(
#     app,
#     prompt | model,
#     path = '/question'
# )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
