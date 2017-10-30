
## Description
This tool converts zen blogs (like https://zen.yandex.ru/media/lifehacker/) to rss feed.

## Usage
Url format: `https://yourdomain.com/zenrss?url=<zen blog url>`

Example:

`https://your-app.herokuapp.com/zenrss?url=https://zen.yandex.ru/media/lifehacker`

or

`https://your-app.herokuapp.com/zenrss?url=https://zen.yandex.ru/media/id/59a3a1ad50c9e514e42d259a/`
  
### Telegram links
This library also optionally supports telegram links conversion. It allows links to be converted to [instant view format](https://instantview.telegram.org/#publishing-templates) using additional `tg_rhash` parameter.
Example:

`https://your-app.herokuapp.com/zenrss?url=https://zen.yandex.ru/media/id/59a3a1ad50c9e514e42d259a/&tg_rhash=657d57c6a152e8`

where `tg_rhash` - unique instant view template identifier

## Deployment
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/mercuree/zen-to-rss)
