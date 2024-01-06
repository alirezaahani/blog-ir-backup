import xml.etree.ElementTree as ET
import io
from pathlib import Path
import webbrowser
import logging
import re

NON_HTTP_MATCH = re.compile(r'"((?!http.:)\/\/.+?)"')

logger = logging.getLogger('main')

def post_html(title, content, creation_date, modify_date, categories, tags):    
    return f'''
    <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="../statics/main.css">
        </head>
        <body>
        <main class="wrp">
                <h1 class="title">{title}</h1>
                <p>ایجاد در تاریخ : <span class="date">{creation_date}</span></p>
                <p>آخرین تغییرات در : <span class="date">{modify_date}</span></p>
                <p>با موضوع : <span class="category">{",".join(categories)}</span></p>
                <hr />
                {content}
                <hr>
                <p>کلمات کلیدی : <span class="category">{",".join(tags)}</span></p>
        </div>
        </body>
    </html>
    '''


def home_html(title, desc, authors, posts):
    posts_html = '<ol reversed>'

    for post in posts:
        posts_html += f'''<li><a href="./{post["idx"]}.html">{post["title"]}</a></li>'''

    posts_html += '</ol>'
    return f'''
    <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="../statics/main.css">
        </head>
        <body>
        <main class="wrp">
                <h1 class="title">{title}</h1>
                <h3>{desc}</h3>
                <h4>نویسندگان: {",".join(authors)}</h4>
                {posts_html}
        </div>
        </body>
    </html>
    '''

def style():
    return '''
        body {
          background-color: lightgray;
          font-weight: normal;
          font-size: 1em;
          font-family: "Vazir", "B Nazanin", "Tahoma", "Noto sans";
          direction: rtl;
        }
        pre {
            font-size: 0.7em;
            font-family: Monospace;
            direction: ltr;
        }
        .title {
            text-align: center;
        }
        .date {
            font-size: 1em;
        }
        .category {
            color:gray;
            font-size: 1em;
        }
        .wrp {
          background-color: white;
          margin: 10px;
          padding: 10px;
          box-shadow: 0 1px 6px 0 rgba(32, 33, 36, .78);
        }
    '''

files_posts = Path('posts')
files_statics = Path('statics')
if not files_posts.exists():
    files_posts.mkdir()

if not files_statics.exists():
    files_statics.mkdir()

with io.open("./statics/main.css", 'w', encoding='utf8') as file:
    file.write(style())

path = input("XML Path: ")

try:
    tree = ET.parse(path)
    blog = tree.getroot()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    exit()

posts = []
for post in blog.find('POSTS').findall('POST'):
    _atter = lambda x, y=post: y.find(x).text.strip()

    idx = _atter('NUMBER')
    title = _atter('TITLE')
    
    content = _atter('CONTENT')
    content = NON_HTTP_MATCH.sub(r'https:\1', content)

    creation_date = _atter('CREATED_DATE')
    modify_date = _atter('LAST_MODIFIED_DATE')

    categories = []
    for category in post.find('CATEGORIES').findall('CATEGORY'):
        categories.append(_atter('NAME', category))

    tags = []
    for tag in post.find('TAGS').findall('TAG'):
        tags.append(_atter('NAME', tag))

    with io.open(f"./posts/{idx}.html", 'w', encoding='utf8') as file:
        file.write(post_html(
            title=title, 
            content=content, 
            creation_date=creation_date, 
            modify_date=modify_date,
            categories=categories, 
            tags=tags
        ))
    
    posts.append({'title': title, 'idx': idx})

info = blog.find('BLOG_INFO')
_atter = lambda x, y=info: y.find(x).text.strip()
title = _atter('TITLE')
desc = _atter('FULL_DESCRIPTION')
authors = [f"{_atter('FIRST_NAME', author)} {_atter('LAST_NAME', author)}" for author in info.find('AUTHORS').findall('USER')]

with io.open(f"./posts/index.html", 'w', encoding='utf8') as file:
    file.write(home_html(
        title=title, 
        desc=desc, 
        authors=authors, 
        posts=posts
    ))


try:
    webbrowser.open_new_tab(str(files_posts.cwd()) + '/posts/index.html')
except webbrowser.Error:
    print(f'Backup files written to: {str(files_posts.cwd()) + "/posts"}')
