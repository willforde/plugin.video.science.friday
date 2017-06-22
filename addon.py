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
from codequick import register_route, register_resolver, run, Listitem
import urlquick

# Localized string Constants
RECENT_VIDEOS = 30101
RECENT_AUDIO = 30102
LIST_AUDIO = 30103
LIST_VIDEO = 30104

# Base url of resource
BASEURL = u"http://www.sciencefriday.com%s"


@register_route
def root(plugin):
    """:type plugin: :class:`codequick.Route`"""
    # Set context parameters based on default view setting
    if plugin.setting["defaultview"] == "0":
        context_label = plugin.localize(LIST_AUDIO)
        context_type = u"segment"
        item_type = u"video"
    else:
        context_label = plugin.localize(LIST_VIDEO)
        context_type = u"video"
        item_type = u"segment"

    # Fetch HTML Source
    url = BASEURL % u"/explore/"
    html = urlquick.get(url)
    icon = plugin.icon

    # Parse for the content
    root_elem = html.parse(u"form", attrs={u"class": u"searchandfilter"})
    sfid = root_elem.get(u"data-sf-form-id")

    # List all topics
    for elem in root_elem.iterfind(".//option[@data-sf-cr]"):
        item = Listitem()
        item.set_label(elem.text)
        item.art["thumb"] = icon

        # Add context item to link to the opposite content type. e.g. audio if video is default
        item.context.container(context_label, content_lister, topic=elem.attrib["value"], sfid=sfid, ctype=context_type)
        item.set_callback(content_lister, topic=elem.attrib["value"], ctype=item_type, sfid=sfid)
        yield item

    # Add Youtube & Recent Content
    yield Listitem.youtube(u"UUDjGU4DP3b-eGxrsipCvoVQ")

    # Add Recent Videos link
    item_dict = {"label": plugin.localize(RECENT_VIDEOS), "formatting": u"[B]%s[/B]", "callback": content_lister,
                 "params": {"sfid": sfid, "ctype": u"video"}, "art": {"thumb": icon}}
    yield Listitem.from_dict(item_dict)

    # Add Recent Audio link
    item_dict = {"label": plugin.localize(RECENT_AUDIO), "formatting": u"[B]%s[/B]", "callback": content_lister,
                 "params": {"sfid": sfid, "ctype": u"segment"}, "art": {"thumb": icon}}
    yield Listitem.from_dict(item_dict)


@register_route
def content_lister(plugin, sfid, ctype, topic=None, from_next=False):
    """
    :type plugin: :class:`codequick.Route`
    :type sfid: unicode
    :type ctype: unicode
    :type topic: unicode
    :type from_next: bool
    """
    # Add link to Alternitve Listing
    if from_next is False and topic:
        params = {"sfid": sfid, "ctype": u"segment" if ctype == u"video" else u"video", "topic": topic}
        label = plugin.localize(LIST_AUDIO) if ctype == u"video" else plugin.localize(LIST_VIDEO)
        item_dict = {"label": label, "callback": content_lister, "params": params, "art": {"thumb": plugin.icon}}
        yield Listitem.from_dict(item_dict)

    # Create content url
    next_page = plugin.params.get("_nextpagecount_", "1")
    if topic:
        url = u"http://www.sciencefriday.com/wp-admin/admin-ajax.php?action=get_results&paged=%(next)s&" \
              u"sfid=%(sfid)s&post_types=%(ctype)s&_sft_topic=%(topic)s" % \
              {"sfid": sfid, "ctype": ctype, "topic": topic, "next": next_page}
    else:
        url = u"http://www.sciencefriday.com/wp-admin/admin-ajax.php?action=get_results&paged=%(next)s&" \
              u"sfid=%(sfid)s&post_types=%(ctype)s" % \
              {"sfid": sfid, "ctype": ctype, "next": next_page}

    # Fetch & parse HTML Source
    root_elem = urlquick.get(url).parse()
    icon = plugin.icon

    # Fetch next page
    next_url = root_elem.find("./a[@rel='next']")
    if next_url is not None:
        yield Listitem.next_page()

    # Parse the elements
    for element in root_elem.iterfind(".//article"):
        tag_a = element.find("./a[@rel='bookmark']")
        item = Listitem()
        item.label = tag_a.text
        # item.stream.hd(has_hd)

        # Fetch plot & duration
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

        # Fetch audio/video url
        tag_audio = element.find("./a[@data-audio]")
        if tag_audio is not None:
            audio_url = tag_audio.get("data-audio")
            item.set_callback(audio_url)
        else:
            item.params["url"] = tag_a.get("href")
            item.set_callback(play_media)

        yield item


@register_resolver
def play_media(plugin, url):
    """
    :type plugin: :class:`codequick.Resolver`
    :type url: unicode
    """
    # Run SpeedForce to atempt to strip Out any unneeded html tags
    root_elem = urlquick.get(url).parse(u"section", attrs={u"class": u"video-section bg-lightgrey"})

    # Search for youtube iframe
    iframe = root_elem.find("iframe")
    return plugin.extract_source(iframe.get("src"))


# Initiate Startup
if __name__ == "__main__":
    run()
