# -*- coding: utf-8 -*-
import requests
from collections import defaultdict


class HslUrls(object):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.baseurl = "http://api.reittiopas.fi/hsl/prod/?request="

    def nearby_stops(self, longitude, latitude):
        url = "%sstops_area&epsg_in=4326&center_coordinate=%s,%s&user=%s&pass=%s" % (
            self.baseurl, latitude, longitude, self.user, self.password)
        return url

    def stop_info(self, stop_code):
        url = "%sstop&epsg_out=4326&code=%s&user=%s&pass=%s" % (self.baseurl, stop_code, self.user, self.password)
        return url

    def lines_info(self, lines):
        lines_str = "|".join(lines)
        url = "%slines&epsg_out=4326&query=%s&user=%s&pass=%s" % (self.baseurl, lines_str, self.user, self.password)
        return url


def hsl_time_to_time(x):
    return "%02d.%02d" % (x / 100 % 24, x % 100)


class HslRequests(object):
    def __init__(self, user, password):
        self.urls = HslUrls(user, password)
        self.last_error = None

    def stop_summary(self, stop_code):
        (stop_info, l) = self._stop_info_lines_info(stop_code)
        s = stop_info[0]
        if l:
            lines = dict([(x["code"], "%s %s" % (x["code_short"], x["line_end"])) for x in l])
        else:
            return "Koodilla %s ei löydy pysäkkiä." % stop_code

        stop_line = s["code_short"] + " " + s["name_fi"] + " " + s["address_fi"]

        if s["departures"]:
            departure_line = "\n".join(
                ["%s %s" % (hsl_time_to_time(x["time"]), lines[x["code"]]) for x in s["departures"]])
        else:
            departure_line = ""

        return "\n".join([stop_line, departure_line])

    def _stop_info_lines_info(self, stop_code):
        try:
            stop_info = self._stop_info_json(stop_code)
        except:
            stop_info = "Error"
        if stop_info == "Error":
            return "Error", None
        lines_info = self._lines_info(self._stop_buses(stop_info))
        return (stop_info, lines_info)

    def _stop_info_json(self, stop_code):
        url = self.urls.stop_info(stop_code)
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            return "Error"
        return r.json()

    def _stop_buses(self, json):
        l = json[0]["lines"]
        return [x.split(":")[0] for x in l]

    def _lines_info(self, lines):
        url = self.urls.lines_info(lines)
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            return "Error"
        return r.json()

    def stop_lines_summary(self, stop_code):
        """Return bus code, name, address, and lines going from this stop"""
        (stop_info, l) = self._stop_info_lines_info(stop_code)
        s = stop_info[0]

        if l:
            linecodes = dict([(x["code"], x["code_short"]) for x in l])
        else:
            return "Koodilla %s ei löydy pysäkkiä." % stop_code

        d = dict(map(lambda x: x.split(":"), s["lines"]))

        stop_line = s["code_short"] + " " + s["name_fi"] + " " + s["address_fi"]
        ends_lines = [(d[k].split(",")[0], linecodes[k]) for k in d.keys()]

        d = defaultdict(list)

        for last, code in ends_lines:
            d[last].append(code)

        sumsum = ", ".join(["%s %s" % (", ".join(sorted(d[k])), k) for k in sorted(d.keys())])

        return "\n".join([stop_line, sumsum])

    def _location_stops(self, longitude, latitude):
        url = self.urls.nearby_stops(longitude, latitude)
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            return "Error"
        return r.json()

    def stops_for_location(self, longitude, latitude):
        s = self._location_stops(longitude, latitude)

        if s == "Error":
            return "Ei pysäkkejä tässä sijainnissa"

        return "\n".join(["%s %s %s" % (x["codeShort"], x["name"], x["address"]) for x in s])
