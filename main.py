import xml.etree.ElementTree as ET
import io
from pathlib import Path
import webbrowser
import logging
import re

NON_HTTP_MATCH = re.compile(r'"((?!http.:)\/\/.+?)"')
PICTURE_MATCH = re.compile(r'https?:\/\/\S+(?:jpe?g|png|bmp|gif|webp)', flags=re.IGNORECASE)

logger = logging.getLogger('main')

def post_html(title, content, creation_date, modify_date, categories, tags, blog_name):    
    return f'''
    <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="../statics/main.css">
        </head>
        <body>
        <main class="wrp">
            <h1 class="title"><a href='./index.html'>{blog_name}</a></h1>
            <h2 class="title">{title}</h2>
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
          font-size: 1em;
          font-family: "Vazir", "B Nazanin", "Tahoma", "Noto sans";
          direction: rtl;
        }
        pre {
            text-align: left;
            direction: ltr;
        }        
        a:hover, a:active, a:focus, a:visited, a:link, a {
            text-decoration: none;
        }
        .title {
            text-align: center;
        }
        .wrp {
          background-color: white;
          margin: 0.5em;
          padding: 0.5em;
        }
    '''

import urllib3
import shutil
from urllib.parse import urlparse
request_pool = urllib3.PoolManager()

def download_file(url, path):
    with open(path, 'wb') as out:
        try:
            r = request_pool.request('GET', url, preload_content=False)
            shutil.copyfileobj(r, out)
            return True
        except urllib3.exceptions.HTTPError:
            return False

posts_path = Path('posts')
posts_path.mkdir(exist_ok=True)

statics_path = Path('statics')
statics_path.mkdir(exist_ok=True)

images_path = Path(statics_path / 'images')
images_path.mkdir(exist_ok=True)

with io.open("./statics/main.css", 'w', encoding='utf8') as file:
    file.write(style())

path = input("XML Path: ")

try:
    tree = ET.parse(path)
    blog = tree.getroot()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    exit()

static_download = input('Download (PNG/JPG/WEBP) statically? (N/y)').lower() == 'y'

info = blog.find('BLOG_INFO')
_atter = lambda x, y=info: y.find(x).text.strip()
blog_title = _atter('TITLE')
blog_desc = _atter('FULL_DESCRIPTION')
blog_authors = [f"{_atter('FIRST_NAME', author)} {_atter('LAST_NAME', author)}" for author in info.find('AUTHORS').findall('USER')]

posts = []
for post in blog.find('POSTS').findall('POST'):
    _atter = lambda x, y=post: y.find(x).text.strip()

    idx = _atter('NUMBER')
    title = _atter('TITLE')
    
    content = _atter('CONTENT')
    content = NON_HTTP_MATCH.sub(r'https:\1', content)

    if static_download:
        for image_url in PICTURE_MATCH.findall(content):
            file_name = images_path / Path(urlparse(image_url).path).name
            if not download_file(image_url, file_name):
                logger.error(f'Could not download `{image_url}`.')
                continue
            content = content.replace(image_url, str('..' / file_name))
    
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
            tags=tags,
            blog_name=blog_title
        ))
    
    posts.append({'title': title, 'idx': idx})


with io.open(f"./posts/index.html", 'w', encoding='utf8') as file:
    file.write(home_html(
        title=blog_title, 
        desc=blog_desc, 
        authors=blog_authors, 
        posts=posts
    ))

try:
    webbrowser.open_new_tab(str(posts_path.cwd()) + '/posts/index.html')
except webbrowser.Error:
    print(f'Backup files written to: {str(posts_path.cwd()) + "/posts"}')
