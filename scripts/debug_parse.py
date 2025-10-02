from anidl.parser import parse_feeds

S='''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Test Anime - Episode 01</title>
      <description>Size: 200 MB - Seeders: 20</description>
      <author>subsplease</author>
      <link>magnet:?xt=urn:btih:FAKE</link>
      <pubDate>Wed, 17 Sep 2025 12:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>'''

res = parse_feeds([{"url":"http://test","raw":S}])
print('len=', len(res))
print(res)
