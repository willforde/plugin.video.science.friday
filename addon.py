"""
Copyright: (c) 2016 William Forde (willforde+kodi@gmail.com)
License: GPLv3, see LICENSE for more details

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

# Package Import
import codequick as plugin

plugin.strings.update(recent_videos=30101, recent_audio=30102, list_audio=30103, list_video=30104)
BASEURL = u"http://www.sciencefriday.com%s"


@plugin.route("/")
def root():
    # Set context parameters based on default view setting
    if plugin.get_setting("defaultview") == 0:
        context_label = plugin.localize("list_audio")
        context_type = "segment"
        item_type = "video"
    else:
        context_label = plugin.localize("list_video")
        context_type = "video"
        item_type = "segment"

    # Fetch HTML Source
    url = u"http://www.sciencefriday.com/explore/"
    html = plugin.requests_session().get(url).text
    icon = plugin.get_info("icon")

    # Parse the content
    stripper = plugin.utils.ETBuilder(u"form", attrs={u"class": u"searchandfilter"}, wanted_tags=[u"form", u"option"])
    root_elem = stripper.run(html)

    # Fetch sfid from root element
    sfid = root_elem.get(u"data-sf-form-id")
    assert sfid, "Unable to find sfid, Cannot proceed without it"

    # List all topics
    for element in root_elem.iterfind(".//option[@data-sf-cr]"):
        item = plugin.ListItem()
        item.label = element.text

        # Set url params
        item.url["topic"] = element.attrib["value"]
        item.url["type"] = item_type
        item.art["thumb"] = icon
        item.url["sfid"] = sfid

        # Add context item to link to the opposite content type. e.g. audio if video is default
        item.context.add(content_lister, context_label, topic=element.attrib["value"], sfid=sfid, type=context_type)

        # Return tuple of (url, listitem, isfolder)
        yield item.get(content_lister)

    # Add Youtube & Recent Content
    yield plugin.ListItem.add_youtube(u"UUDjGU4DP3b-eGxrsipCvoVQ")
    yield plugin.ListItem.add_item(content_lister, plugin.localize("recent_videos"), thumbnail=icon, sfid=sfid, type="video", topic="")
    yield plugin.ListItem.add_item(content_lister, plugin.localize("recent_audio"), thumbnail=icon, sfid=sfid, type="segment", topic="")


@plugin.route("/lister")
def content_lister():
    # Only add listing for alternate type if not executing as a next page
    icon = plugin.get_info("icon")
    if "nextpagecount" not in plugin.params and "topic" in plugin.params:
        link_params = plugin.params.copy()
        link_params["updatelisting"] = "true"
        link_params["type"] = "segment" if link_params["type"] == "video" else "video"

        # Add link to Alternitve Listing
        if plugin.params["type"] == "video":
            yield plugin.ListItem.add_item(content_lister, plugin.localize("list_audio"), thumbnail=icon, **link_params)
        else:
            yield plugin.ListItem.add_item(content_lister, plugin.localize("list_video"), thumbnail=icon, **link_params)

    # Fetch Quality Setting from Youtube Addon
    if plugin.params["type"] == u"video":
        has_hd = plugin.youtube.youtube_hd()
    else:
        has_hd = None

    # Create content url
    plugin.params["nextpagecount"] = plugin.params.get("nextpagecount", "1")
    if "topic" in plugin.params:
        url = u"http://www.sciencefriday.com/wp-admin/admin-ajax.php?action=get_results&paged=%(nextpagecount)s&" \
              u"sfid=%(sfid)s&post_types=%(type)s&_sft_topic=%(topic)s" % plugin.params
    else:
        url = u"http://www.sciencefriday.com/wp-admin/admin-ajax.php?action=get_results&paged=%(nextpagecount)s&" \
              u"sfid=%(sfid)s&post_types=%(type)s" % plugin.params

    # Fetch & parse HTML Source
    html = plugin.requests_session().get(url).text
    stripper = plugin.utils.ETBuilder(wanted_tags=[u"article", u"a", u"p", u"img"], root_tag=u"body")
    root_elem = stripper.run(html)

    # Parse the elements
    for element in root_elem.iterfind(".//article"):
        tag_a = element.find("./a[@rel='bookmark']")
        item = plugin.ListItem()
        item.label = tag_a.text
        item.stream.hd(has_hd)

        # Fetch plot/duration
        tag_p = element.findall("p")
        if tag_p and tag_p[0].get("class") == "run-time":
            item.info["duration"] = tag_p[0].text
            item.info["plot"] = tag_p[1].text
        elif tag_p:
            item.info["plot"] = tag_p[0].text

        # Fetch image if exists
        img = element.find(".//img[@data-src]")
        if img is not None:
            item.art["thumb"] = img.get("data-src")
        else:
            item.art["thumb"] = icon

        # Fetch audio/video url and Return listitem
        tag_audio = element.find("./a[@data-audio]")
        if tag_audio is not None:
            audio_url = tag_audio.get("data-audio")
            yield item.get(audio_url)
        else:
            item.url["url"] = tag_a.get("href")
            yield item.get(play_media)

    # Fetch next page
    next_url = root_elem.find("./a[@rel='next']")
    if next_url is not None:
        yield plugin.ListItem.add_next()


@plugin.resolve("/player")
def play_media():
    # Create url for oembed api
    url = plugin.params["url"]
    html = plugin.requests_session().get(url).content

    # Run SpeedForce to atempt to strip Out any unneeded html tags
    flash = plugin.utils.ETBuilder(u"section", attrs={u"class": u"video-section bg-lightgrey"}, wanted_tags=[u"iframe"])
    root_elem = flash.run(html)

    # Search for youtube iframe
    iframe = root_elem.find("iframe")
    assert iframe is not None, "Unable to find youtube iframe, Cannot proceed without it"
    import urlparse

    # Check for playlist or video
    src = urlparse.urlsplit(iframe.get("src"))
    if src.path == u'/embed/videoseries':
        playlist_id = urlparse.parse_qs(src.query)["list"]
        return play_media.youtube_playlist_url(playlist_id)
    elif src.path.startswith("/embed/"):
        video_id = src.path.rsplit("/", 1)[-1]
        return play_media.youtube_video_url(video_id)

# Initiate Startup
if __name__ == "__main__":
    plugin.run(True)
