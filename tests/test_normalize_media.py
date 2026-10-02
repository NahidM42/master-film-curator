from pathlib import Path

import pytest

from master_film_curator.matching.normalize import normalize_title, parse_filename, parse_path
from master_film_curator.media.ffprobe import probe, require_ffprobe
from master_film_curator.media.quality import resolution_class
from master_film_curator.media.series_parser import parse_series


@pytest.mark.parametrize(
    "name,title,year",
    [
        ("A.Separation.2011.1080p.BluRay.x265.AAC-PSA.mkv", "a separation", 2011),
        ("Persona.1966.WEB-DL.H264.en.srt", "persona", 1966),
        ("Dogville_2003_720p_YIFY.mp4", "dogville", 2003),
        ("1917.2019.2160p.mkv", "1917", 2019),
        ("2001.A.Space.Odyssey.1968.BDRip.mkv", "2001 a space odyssey", 1968),
        ("Ｆｉｌｍ.2020.HEVC.mkv", "film", 2020),
        ("Persona (1966) — Ingmar Bergman.mkv", "persona", 1966),
    ],
)
def test_parse(name, title, year):
    assert parse_filename(name) == {"title": title, "year": year}


def test_unicode():
    assert normalize_title(" Amélie—test!  ") == normalize_title("Ame\u0301lie test")


@pytest.mark.parametrize(
    "name,s,e",
    [
        ("Show.S01E01.mkv", 1, 1),
        ("Show.S1E1.mkv", 1, 1),
        ("Show.1x01.mkv", 1, 1),
        ("Season 02/E03.mkv", 2, 3),
    ],
)
def test_series(name, s, e):
    r = parse_series(Path("/root/Show (2019)") / name)
    assert (r["season"], r["episode"], r["series_uncertain"]) == (s, e, False)


def test_series_safety():
    assert parse_series(Path("Show.S01E01E02.mkv"))["series_uncertain"]
    assert parse_series(Path("Season 03/Show.S02E01.mkv"))["series_uncertain"]
    assert parse_series(Path("Season 01/unknown.mkv"))["series_uncertain"]
    assert parse_path(Path("/root/Show (2019)/Season 01/S01E02.mkv"))["title"] == "show"


@pytest.mark.parametrize(
    "w,h,quality",
    [
        (1920, 1080, "1080-class"),
        (1920, 800, "1080-class"),
        (1280, 720, "720-class"),
        (3840, 2160, "2160 / 4K"),
        (2560, 1440, "1440-class"),
        (720, 480, "SD"),
        (7680, 4320, "Higher"),
        (None, None, "Unknown"),
    ],
)
def test_quality(w, h, quality):
    assert resolution_class(w, h) == quality


def test_probe_missing():
    with pytest.raises(RuntimeError, match="sudo apt"):
        require_ffprobe("/does/not/exist/ffprobe")


def test_probe_ignores_cover(monkeypatch):
    import json
    from types import SimpleNamespace

    monkeypatch.setattr("master_film_curator.media.ffprobe.require_ffprobe", lambda _: "ffprobe")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: SimpleNamespace(
            stdout=json.dumps(
                {
                    "streams": [
                        {
                            "codec_type": "video",
                            "width": 4000,
                            "height": 4000,
                            "disposition": {"attached_pic": 1},
                        },
                        {"codec_type": "video", "width": 1920, "height": 800, "codec_name": "h264"},
                    ],
                    "format": {"duration": "10.5", "bit_rate": "1000"},
                }
            )
        ),
    )
    r = probe(Path("x.mkv"))
    assert (r["width"], r["duration"], r["bitrate"]) == (1920, 10.5, 1000)


def test_episode_number_in_season_folder_and_language_tag():
    assert parse_path(Path("/root/Show (2019)/Season 01/E03.mkv"))["title"] == "show"
    assert parse_filename("Persona.en.1080p.mkv")["title"] == "persona"
