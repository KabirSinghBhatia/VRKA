"""Unit tests for deterministic quality ranking and format selection."""

import unittest
from vrka_core.quality_ranker import (
    QualityProfile,
    build_ytdlp_format_spec,
    calculate_format_score,
    rank_formats,
)


class QualityRankingTests(unittest.TestCase):
    def test_high_bitrate_outscores_starved_newer_codec(self):
        """User Rule: Never choose a newer codec merely because it is newer

        when another representation has substantially better source quality.
        """
        # Pristine high-bitrate H.264 stream (1080p @ 8000 kbps, 60fps)
        h264_stream = {
            "format_id": "137",
            "height": 1080,
            "width": 1920,
            "fps": 60,
            "vbr": 8000,
            "vcodec": "avc1.64002a",
        }
        # Starved low-bitrate AV1 stream (1080p @ 1200 kbps, 60fps)
        av1_stream = {
            "format_id": "399",
            "height": 1080,
            "width": 1920,
            "fps": 60,
            "vbr": 1200,
            "vcodec": "av01.0.08m.08",
        }

        profile = QualityProfile(target_quality="1080p (Full HD)", prefer_60fps=True)
        h264_score = calculate_format_score(h264_stream, profile)
        av1_score = calculate_format_score(av1_stream, profile)

        self.assertGreater(
            h264_score,
            av1_score,
            f"Expected high-bitrate stream (score {h264_score}) to outrank starved AV1 (score {av1_score})",
        )

        ranked = rank_formats([av1_stream, h264_stream], profile)
        self.assertEqual(ranked[0]["format_id"], "137")

    def test_comparable_bitrate_gives_subtle_boost_to_efficient_codec(self):
        # VP9 stream @ 3000 kbps vs H.264 @ 3000 kbps
        vp9_stream = {
            "format_id": "248",
            "height": 1080,
            "width": 1920,
            "fps": 30,
            "vbr": 3000,
            "vcodec": "vp9",
        }
        h264_stream = {
            "format_id": "137",
            "height": 1080,
            "width": 1920,
            "fps": 30,
            "vbr": 3000,
            "vcodec": "avc1",
        }

        profile = QualityProfile(target_quality="1080p", prefer_60fps=False)
        vp9_score = calculate_format_score(vp9_stream, profile)
        h264_score = calculate_format_score(h264_stream, profile)
        self.assertGreater(vp9_score, h264_score)

    def test_60fps_preference_boost(self):
        stream_60fps = {"format_id": "299", "height": 1080, "fps": 60, "vbr": 4000, "vcodec": "avc1"}
        stream_30fps = {"format_id": "137", "height": 1080, "fps": 30, "vbr": 4000, "vcodec": "avc1"}

        profile_60 = QualityProfile(prefer_60fps=True)
        score_60 = calculate_format_score(stream_60fps, profile_60)
        score_30 = calculate_format_score(stream_30fps, profile_60)
        self.assertGreater(score_60, score_30)

    def test_format_spec_generation(self):
        spec, sort = build_ytdlp_format_spec("video", "1080p (Full HD)", prefer_60fps=True)
        self.assertIn("height<=1080", spec)
        self.assertIn("fps:60", sort)

        spec_best, _ = build_ytdlp_format_spec("video", "Best Available", prefer_60fps=False)
        self.assertEqual(spec_best, "bv*+ba/b/best")

        spec_audio, sort_audio = build_ytdlp_format_spec("audio", "MP3")
        self.assertEqual(spec_audio, "bestaudio/best")


if __name__ == "__main__":
    unittest.main()
