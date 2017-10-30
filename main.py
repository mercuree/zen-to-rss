
import requests
import requests_cache
from flask import Flask
from flask import request
from flask import Response
from flask import abort
from datetime import datetime
from datetime import timezone
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

    parsed_url = urlparse(zen_url)

    if parsed_url.netloc != 'zen.yandex.ru':
        return 'Domain must be zen.yandex.ru'

    # validate tg_rhash
    if tg_rhash and not re.match(r'^[a-fA-F\d]+$', tg_rhash):
        return 'Invalid tg_rhash. Please, check rhash value from instant view template'

    if not re.match(r'^/media/(id/[\da-f]+|[a-z\d_]+)/?$', parsed_url.path):
        return 'Url is unsupported. Supported formats:<br>' \
               '• https://zen.yandex.ru/media/id/01234567890abcdef0123456 <br>' \
               '• https://zen.yandex.ru/media/nickname'

    resp = requests.get(zen_url, headers={
        'User-Agent': 'TelegramBot (like TwitterBot)'
    })
    doc = fromstring(resp.text)

    try:
        json_data = json.loads(doc.xpath('.//*[@id="init_data"]')[0].text)
    except:
        return abort(404)

    items = json_data.get('publications')
    publisher = json_data.get('publisher')

    feed = FeedGenerator()
    feed.id('http://zen.yandex.ru/')
    feed.title(publisher.get('name'))
    feed.subtitle(publisher.get('description').strip())
    feed.language('ru')
    feed.author({'name': '-', 'email': '-'})
    feed.link(href=zen_url, rel='alternate')
    try:
        image_logo_id = json_data['publisher']['logo'].get('id')
        image_logo = json_data['images'].get(image_logo_id)
        image_logo_url = IMAGE_URL.format(
            namespace=image_logo['namespace'],
            groupId=image_logo['groupId'],
            imageName=image_logo['imageName']
        )
        feed.logo(image_logo_url)
    except:
        pass

    for item in items:

        entry = feed.add_entry()

        entry.title(
            item['content']['preview'].get('title').strip()
        )

        entry.description(
            item['content']['preview'].get('snippet').strip()
        )

        if item['content']['preview'].get('image'):
            item_image = json_data['images'].get(
                item['content']['preview']['image'].get('id')
            )
    
            item_image_url = IMAGE_URL.format(
                namespace=item_image['namespace'],
                groupId=item_image['groupId'],
                imageName=item_image['imageName']
            )
            entry.enclosure(
                url=item_image_url,
                type='image/%s' % item_image['meta']['origFormat'].lower(),
                length='2048'
            )

        # set /media/<nickname> if available, otherwise set /media/id/<uid>
        publisher_identity = publisher['nickname'].get('normalized') if 'nickname' in publisher else "id/" + item.get('publisherId')
        entry_url = ENTRY_URL.format(
            publisherId=publisher_identity,
            titleForUrl=item.get('titleForUrl'),
            id=item.get('id')
        )
        # convert to instant view link if tg hash is provided
        if tg_rhash:
            # write original url into author field
            entry.author({'name': '', 'email': entry_url})
            entry_url = TG_URL.format(url=quote_plus(entry_url), rhash=tg_rhash)

        entry.link({'href': entry_url})

        entry.pubdate(
            datetime.fromtimestamp(item['content'].get('modTime') / 1000, tz=timezone.utc)
        )

    rss_response = Response(feed.rss_str(pretty=True))
    rss_response.headers.set('Content-Type', 'application/rss+xml; charset=utf-8')

    return rss_response


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=80)
