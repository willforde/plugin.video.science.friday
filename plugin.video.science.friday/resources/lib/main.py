# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, run
from codequick.utils import urljoin_partial, bold
import urlquick

# Localized string Constants
RECENT_VIDEOS = 30001
RECENT_AUDIO = 30002
LIST_AUDIO = 30003
LIST_VIDEO = 30004

BASE_URL = "https://www.sciencefriday.com"
url_constructor = urljoin_partial(BASE_URL)


@Route.register
def root(plugin, content_type="video"):
    """
    :type plugin: Route
    :type content_type: str
    """
    # Set context parameters based on default view setting
    if content_type == "video":
        context_label = plugin.localize(LIST_AUDIO)
        context_type = "segment"
        item_type = "video"
    else:
        context_label = plugin.localize(LIST_VIDEO)
        context_type = "video"
        item_type = "segment"

    # Add Youtube
    yield Listitem.youtube("UCDjGU4DP3b-eGxrsipCvoVQ")

    # Recent Content
    extra_url = url_constructor("/explore/?post_types={}")
    yield Listitem.from_dict(
        content_lister,
        bold(plugin.localize(RECENT_VIDEOS)),
        params={"url": extra_url.format("video")}
    )
    yield Listitem.from_dict(
        content_lister,
        bold(plugin.localize(RECENT_AUDIO)),
        params={"url": extra_url.format("segment")}
    )

    # Fetch HTML Source
    url = url_constructor("/explore/")
    html = urlquick.get(url)

    # Parse for the content
    root_elem = html.parse("form", attrs={"class": "searchandfilter"})
    content_url = url_constructor("/explore/?post_types={post_type}&_sft_topic={topic}")

    # List all topics
    for elem in root_elem.iterfind(".//option[@data-sf-count]"):
        count = int(elem.get("data-sf-count"))
        if not count:
            continue

        item = Listitem()
        item.label = elem.text  # "{} ({})".format(elem.text, count)
        url = content_url.format(topic=elem.attrib["value"], post_type=item_type)
        context_url = content_url.format(topic=elem.attrib["value"], post_type=context_type)

        # Add context item to link to the opposite content type. e.g. audio if video is default
        item.context.container(content_lister, context_label, url=context_url)
        item.set_callback(content_lister, url=url, alt_url=context_url)
        yield item


@Route.register
def content_lister(plugin, url, alt_url=None):
    """
    :type plugin: Route
    :type url: str
    :type alt_url: str
    """

    # Add link to Alternitve Listing
    if alt_url:
        label = bold(plugin.localize(LIST_AUDIO) if "post_types=segment" in alt_url else plugin.localize(LIST_VIDEO))
        item_dict = {"label": label, "callback": content_lister, "params": {"url": alt_url, "_title_": plugin.category}}
        yield Listitem.from_dict(**item_dict)

    # Fetch & parse HTML Source
    ishd = bool(plugin.setting.get_int("video_quality", addon_id="script.module.youtube.dl"))
    root_elem = urlquick.get(url_constructor(url)).parse()

    # Fetch next page
    next_url = root_elem.find(".//a[@rel='next']")
    if next_url is not None:  # pragma: no branch
        url = url_constructor("/explore/?{}".format(next_url.get("href")))
        yield Listitem.next_page(url=url)

    # Parse the elements
    for element in root_elem.iterfind(".//article"):
        klasses = element.get("class")
        if not ("type-video" in klasses or "type-segment" in klasses):
            continue

        tag_a = element.find(".//a[@rel='bookmark']")
        item = Listitem()
        item.label = tag_a.text
        item.stream.hd(ishd)

        # Fetch plot & duration
        tag_p = element.findall(".//p")
        if tag_p and tag_p[0].get("class") == "run-time":
            item.info["duration"] = tag_p[0].text
            item.info["plot"] = tag_p[1].text
        elif tag_p:  # pragma: no branch
            item.info["plot"] = tag_p[0].text

        # Fetch image if exists
        img = element.find(".//img[@data-src]")
        if img is not None:
            item.art["thumb"] = img.get("data-src")

        # Fetch audio/video url
        tag_audio = element.find(".//a[@data-audio]")
        if tag_audio is not None:
            audio_url = tag_audio.get("data-audio")
            item.set_callback(audio_url)
        else:
            item.set_callback(play_video, url=tag_a.get("href"))

        yield item


@Resolver.register
def play_video(plugin, url):
    """
    :type plugin: Resolver
    :type url: unicode
    """
    return plugin.extract_source(url)
