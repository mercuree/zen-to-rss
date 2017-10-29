
import requests
import requests_cache
from flask import Flask
from flask import request
from flask import Response
from flask import abort
from datetime import datetime
from datetime import timezone
from feedgen.feed import FeedGenerator
from lxml.html import fromstring
import json


requests_cache.install_cache(expire_after=300)

app = Flask(__name__)

IMAGE_URL = 'https://avatars.mds.yandex.net/get-{namespace}/{groupId}/{imageName}/orig'

ENTRY_URL = 'https://zen.yandex.ru/media/id/{publisherId}/{titleForUrl}-{id}'


@app.route('/')
def main_page():
    return "Just an empty page :\ "


@app.route('/zenrss', methods=['GET'])
def get_rss():
    zen_url = request.args.get('url')

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
    feed.subtitle(publisher.get('description'))
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
            item['content']['preview'].get('title')
        )

        entry.description(
            item['content']['preview'].get('snippet')
        )

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

        entry_url = ENTRY_URL.format(
            publisherId=item.get('publisherId'),
            titleForUrl=item.get('titleForUrl'),
            id=item.get('id')
        )

        entry.link(
            {'href': entry_url}
        )

        entry.pubdate(
            datetime.fromtimestamp(item['content'].get('modTime') / 1000, tz=timezone.utc)
        )

    rss_response = Response(feed.rss_str(pretty=True))
    rss_response.headers.set('Content-Type', 'application/rss+xml; charset=utf-8')

    return rss_response


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=80)
