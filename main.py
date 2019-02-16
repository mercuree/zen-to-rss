
import requests
import requests_cache
from flask import Flask
from flask import request
from flask import Response
from flask import abort
import dateparser
from urllib.parse import urlparse
from urllib.parse import quote_plus
import re
from feedgen.feed import FeedGenerator
from lxml.html import fromstring
import json


requests_cache.install_cache(expire_after=300)

app = Flask(__name__)

IMAGE_URL = 'https://avatars.mds.yandex.net/get-{namespace}/{groupId}/{imageName}/orig'

ENTRY_URL = 'https://zen.yandex.ru/media/{publisherId}/{titleForUrl}-{id}'

TG_URL = 'http://t.me/iv?url={url}&rhash={rhash}'


@app.route('/')
def main_page():
    return "Just an empty page :\ "


@app.route('/zenrss', methods=['GET'])
def get_rss():
    zen_url = request.args.get('url')
    # set telegram instant view rhash if available
    tg_rhash = request.args.get('tg_rhash')

    limit_description = request.args.get('limit_description', type=int)

    if not zen_url:
        return 'url (?url=https://zen.yandex.ru/media/.../) must be set'
    parsed_url = urlparse(zen_url)
    if parsed_url.netloc != 'zen.yandex.ru':
        return 'Domain must be zen.yandex.ru'

    # validate tg_rhash
    if tg_rhash and not re.match(r'^[a-fA-F\d]+$', tg_rhash):
        return 'Invalid tg_rhash. Please, check rhash value from instant view template'

    if not re.match(r'^/(media/)?(id/[\da-f]+|[a-z\d_]+)/?$', parsed_url.path):
        return 'Url is unsupported. Supported formats:<br>' \
               '• https://zen.yandex.ru/media/id/01234567890abcdef0123456 <br>' \
               '• https://zen.yandex.ru/media/nickname'

    resp = requests.get(zen_url, headers={
        'User-Agent': 'TelegramBot (like TwitterBot)'
    })
    doc = fromstring(resp.text)

    try:
        text = re.search(r'{.+}', doc.xpath('.//script[contains(text(), "window.__SERVER_STATE__")]')[0].text)[0]
        json_data = json.loads(text)
    except:
        return abort(404)

    items = json_data['feed'].get('items')
    items_order = json_data['feed'].get('itemsOrder')
    publisher = next(iter(json_data.get('sources').values()))

    feed = FeedGenerator()
    feed.id('http://zen.yandex.ru/')
    feed.title(publisher.get('title'))
    feed.subtitle(publisher.get('description').strip())
    feed.language('ru')
    feed.author({'name': '-', 'email': '-'})
    feed.link(href=zen_url, rel='alternate')
    try:
        image_logo_url = publisher.get('logo')
        feed.logo(image_logo_url)
    except:
        pass

    for oItem in items_order:
        item = items.get(oItem)
        if item.get('type') != 'card':
            continue

        entry = feed.add_entry()

        entry.title(
            item.get('title').strip()
        )

        entry.description(
            item.get('text').strip()[:limit_description]
        )

        if item.get('image'):
            item_image_url = item.get('image')
            entry.enclosure(
                url=item_image_url,
                type='image/webp',
                length='2048'
            )

        entry_url = item.get('link').split('?')[0]
        # convert to instant view link if tg hash is provided
        if tg_rhash:
            # write original url into author field
            entry.author({'name': '', 'email': entry_url})
            entry.link({'href': TG_URL.format(url=quote_plus(entry_url), rhash=tg_rhash)})

        else:
            entry.link({'href': entry_url})

        try:
            entry.pubdate(
                dateparser.parse(item.get('creationTime'), settings={'RETURN_AS_TIMEZONE_AWARE': True})
            )
        except:
            pass

    rss_response = Response(feed.rss_str(pretty=True))
    rss_response.headers.set('Content-Type', 'application/rss+xml; charset=utf-8')

    return rss_response


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=80)
