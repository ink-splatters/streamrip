"""Tests for search results display formatting."""

from streamrip.metadata.search_results import AlbumSummary, TrackSummary


def test_album_summary_with_year():
    """Test that album summary includes year suffix."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released="2023-05-15",
    )
    summary = album.summarize()
    assert "(2023)" in summary
    assert "Test Album" in summary
    assert "Test Artist" in summary


def test_album_summary_with_unknown_year():
    """Test that Unknown year is omitted from display."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released="Unknown",
    )
    summary = album.summarize()
    assert summary == "Test Album by Test Artist"
    assert "Unknown" not in summary


def test_album_summary_with_none_date():
    """Test that None date shows no year."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released=None,
    )
    summary = album.summarize()
    assert summary == "Test Album by Test Artist"


def test_album_summary_format():
    """Test the complete format of album summary."""
    album = AlbumSummary(
        id="67890",
        name="Rumours",
        artist="Fleetwood Mac",
        num_tracks="11",
        date_released="1977-02-04",
    )
    summary = album.summarize()
    assert summary == "Rumours (1977) by Fleetwood Mac"


def test_album_preview_unchanged():
    """Ensure preview format remains unchanged."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released="2023-05-15",
    )
    preview = album.preview()
    assert "Date released:" in preview
    assert "2023-05-15" in preview
    assert "10 Tracks" in preview
    assert "ID: 12345" in preview


def test_album_from_item_qobuz_format():
    """Test parsing Qobuz-style API response."""
    qobuz_item = {
        "id": 19512572,
        "title": "Rumours",
        "version": "",
        "artist": {"name": "Fleetwood Mac"},
        "tracks_count": 11,
        "release_date_original": "1977-02-04",
    }
    album = AlbumSummary.from_item(qobuz_item)
    assert album.id == "19512572"
    assert album.name == "Rumours"
    assert album.artist == "Fleetwood Mac"
    assert album.num_tracks == "11"
    assert album.date_released == "1977-02-04"


def test_album_from_item_deezer_format():
    """Test parsing Deezer-style API response."""
    deezer_item = {
        "id": 123456,
        "title": "Test Album",
        "artist": {"name": "Test Artist"},
        "nb_tracks": 12,
        "release_date": "2022-03-15",
    }
    album = AlbumSummary.from_item(deezer_item)
    assert album.id == "123456"
    assert album.name == "Test Album"
    assert album.artist == "Test Artist"
    assert album.date_released == "2022-03-15"


def test_album_from_item_tidal_format():
    """Test parsing Tidal-style API response."""
    tidal_item = {
        "id": 789012,
        "title": "Another Album",
        "artist": {"name": "Another Artist"},
        "numberOfTracks": 8,
        "releaseDate": "2021-11-20",
    }
    album = AlbumSummary.from_item(tidal_item)
    assert album.id == "789012"
    assert album.name == "Another Album"
    assert album.artist == "Another Artist"
    assert album.num_tracks == "8"
    assert album.date_released == "2021-11-20"


def test_track_summary_unchanged():
    """Ensure track summary format remains unchanged (no year prefix for tracks)."""
    track = TrackSummary(
        id="54321",
        name="Test Track",
        artist="Test Artist",
        date_released="2023-05-15",
    )
    summary = track.summarize()
    assert summary == "Test Track by Test Artist"
    assert "2023" not in summary  # Tracks don't get year prefix


def test_album_preview_with_audio_quality():
    """Test preview displays audio quality when available."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released="2023-05-15",
        bit_depth=24,
        sampling_rate=96000,
    )
    preview = album.preview()
    assert "Audio Quality:" in preview
    assert "96.0 kHz" in preview
    assert "24-bit" in preview


def test_album_preview_with_sampling_rate_only():
    """Test preview displays sampling rate when bit depth unavailable."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released="2023-05-15",
        sampling_rate=44100,
    )
    preview = album.preview()
    assert "Sampling Rate:" in preview
    assert "44.1 kHz" in preview
    assert "bit" not in preview


def test_album_preview_with_bit_depth_only():
    """Test preview displays bit depth when sampling rate unavailable."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released="2023-05-15",
        bit_depth=16,
    )
    preview = album.preview()
    assert "Bit Depth:" in preview
    assert "16-bit" in preview
    assert "kHz" not in preview


def test_album_preview_without_audio_quality():
    """Test preview works when audio quality unavailable."""
    album = AlbumSummary(
        id="12345",
        name="Test Album",
        artist="Test Artist",
        num_tracks="10",
        date_released="2023-05-15",
    )
    preview = album.preview()
    assert "Date released:" in preview
    assert "10 Tracks" in preview
    assert "Audio Quality:" not in preview
    assert "kHz" not in preview
    assert "bit" not in preview


def test_album_from_item_qobuz_with_quality():
    """Test parsing Qobuz-style API response with audio quality."""
    qobuz_item = {
        "id": 19512572,
        "title": "Rumours",
        "version": "2001 Remaster",
        "artist": {"name": "Fleetwood Mac"},
        "tracks_count": 11,
        "release_date_original": "1977-02-04",
        "maximum_bit_depth": 24,
        "maximum_sampling_rate": 96000,
    }
    album = AlbumSummary.from_item(qobuz_item)
    assert album.id == "19512572"
    assert album.name == "Rumours (2001 Remaster)"
    assert album.artist == "Fleetwood Mac"
    assert album.bit_depth == 24
    assert album.sampling_rate == 96000


def test_album_from_item_without_quality():
    """Test parsing API response without audio quality fields."""
    item = {
        "id": 123456,
        "title": "Test Album",
        "artist": {"name": "Test Artist"},
        "tracks_count": 10,
        "release_date": "2023-05-15",
    }
    album = AlbumSummary.from_item(item)
    assert album.id == "123456"
    assert album.bit_depth is None
    assert album.sampling_rate is None


def test_sampling_rate_conversion_to_khz():
    """Test that sampling rates are correctly converted to kHz in preview."""
    # Test with 96 kHz
    album_96k = AlbumSummary(
        id="1",
        name="HiRes Album",
        artist="Artist",
        num_tracks="10",
        date_released="2023",
        bit_depth=24,
        sampling_rate=96000,
    )
    assert "96.0 kHz" in album_96k.preview()

    # Test with 44.1 kHz
    album_44k = AlbumSummary(
        id="2",
        name="CD Quality",
        artist="Artist",
        num_tracks="10",
        date_released="2023",
        bit_depth=16,
        sampling_rate=44100,
    )
    assert "44.1 kHz" in album_44k.preview()

    # Test with already-in-kHz format (edge case)
    album_khz = AlbumSummary(
        id="3",
        name="Edge Case",
        artist="Artist",
        num_tracks="10",
        date_released="2023",
        bit_depth=24,
        sampling_rate=96,  # Already in kHz
    )
    assert "96.0 kHz" in album_khz.preview()
