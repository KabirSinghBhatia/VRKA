"""Tests for yt-dlp failure classification and desktop browser fallback triggering."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from vrka_core.failure_classifier import (
    ClassificationResult,
    FailureCategory,
    RecoveryAction,
    classify_failure,
    has_transfer_started,
    is_browser_recoverable,
)
from vrka_core.browser_fallback import BrowserFallbackError
from vrka_core.candidates import DownloadState
from vrka_core.watchdog import (
    AutomaticFallbackExecutor,
    DirectPathEligibleForFallback,
    ProcessInactivity,
    ActivityPhase,
)
from vrka_downloader import (
    DownloadCanceled,
    VRKADownloader,
    YTDLPCommandError,
    classify_download_error,
    direct_failure_is_browser_recoverable,
    format_download_error,
)


class FailureClassifierTests(unittest.TestCase):
    """Verify structured failure classification for BROWSER_RECOVERABLE and NON_BROWSER_RECOVERABLE."""

    # ------------------------------------------------------------------
    # Group A: Browser Fallback MUST trigger
    # ------------------------------------------------------------------

    def test_android_reference_flashvars_triggers_fallback(self):
        """Android reference case: '[generic] Unable to extract flashvars'."""
        output = 'ERROR: [generic] Unable to extract flashvars; please report this issue on https://github.com/yt-dlp/yt-dlp/issues'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.FLASHVARS)
        self.assertTrue(res.is_recoverable)
        self.assertTrue(is_browser_recoverable(output))

    def test_flashvars_not_found_triggers_fallback(self):
        output = 'ERROR: [generic] None: Flashvars not found'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.FLASHVARS)
        self.assertTrue(is_browser_recoverable(output))

    def test_kvs_player_extraction_failure_triggers_fallback(self):
        output = 'ERROR: [kvs] Failed to parse player configuration'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.KVS_PLAYER)
        self.assertTrue(is_browser_recoverable(output))

    def test_kvs_kt_player_flashvars_triggers_fallback(self):
        output = 'ERROR: [kt_player] Unable to extract video_url from flashvars'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertIn(res.category, (FailureCategory.KVS_PLAYER, FailureCategory.FLASHVARS))
        self.assertTrue(is_browser_recoverable(output))

    def test_json_parsing_in_player_context_triggers_fallback(self):
        output = (
            'ERROR: [generic] Failed to parse JSON (caused by '
            'JSONDecodeError("Expecting value: line 1 column 1 (char 0)")) in player data'
        )
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.PLAYER_EXTRACTION)
        self.assertTrue(is_browser_recoverable(output))

    def test_client_side_js_player_failure_triggers_fallback(self):
        output = 'ERROR: [generic] Could not find JS player or player config on page'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.CLIENT_SIDE_PLAYER)
        self.assertTrue(is_browser_recoverable(output))

    def test_named_player_videojs_error_triggers_fallback(self):
        output = 'ERROR: videojs player config extraction failed: unable to find video source'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.CLIENT_SIDE_PLAYER)
        self.assertTrue(is_browser_recoverable(output))

    def test_embedded_iframe_player_failure_triggers_fallback(self):
        output = 'ERROR: [generic] Could not find embedded player iframe'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.EMBEDDED_PLAYER)
        self.assertTrue(is_browser_recoverable(output))

    def test_generic_parser_stream_extraction_failure_triggers_fallback(self):
        output = 'ERROR: [generic] Unable to extract video url; no formats found'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.GENERIC_PARSER)
        self.assertTrue(is_browser_recoverable(output))

    def test_generic_extractor_page_fetched_unsupported_triggers_fallback(self):
        output = (
            '[generic] Extracting URL: https://example.com/video/123\n'
            '[generic] Downloading webpage\n'
            'ERROR: [generic] Unsupported URL: https://example.com/video/123'
        )
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.PAGE_UNSUPPORTED)
        self.assertTrue(is_browser_recoverable(output))

    def test_cloudflare_challenge_triggers_fallback(self):
        output = 'ERROR: The site returned a Cloudflare verification page (Just a moment... cf-chl-)'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.CLOUDFLARE)
        self.assertTrue(is_browser_recoverable(output))

    def test_cookie_bot_wall_triggers_fallback(self):
        output = 'ERROR: [youtube] Sign in to confirm you’re not a bot'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.COOKIE_WALL)
        self.assertTrue(is_browser_recoverable(output))

    def test_webpage_http_403_triggers_fallback(self):
        output = 'ERROR: Unable to download webpage: HTTP Error 403: Forbidden'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.HTTP_BLOCK)
        self.assertTrue(is_browser_recoverable(output))

    def test_expired_media_address_triggers_fallback(self):
        output = 'ERROR: The media address has expired (URL has expired)'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.EXPIRED)
        self.assertTrue(is_browser_recoverable(output))

    # ------------------------------------------------------------------
    # Group B: Browser Fallback MUST NOT trigger
    # ------------------------------------------------------------------

    def test_dns_failure_is_terminal(self):
        output = 'ERROR: <urlopen error [Errno 11001] getaddrinfo failed>'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.DNS)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_connection_refused_is_terminal(self):
        output = 'ERROR: <urlopen error [Errno 111] Connection refused>'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.CONNECTION)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_tls_certificate_failure_is_terminal(self):
        output = 'ERROR: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.TLS)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_cancellation_is_terminal(self):
        output = 'Download was cancelled by user'
        res = classify_failure(output, is_cancelled=True)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.CANCELLATION)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output, is_cancelled=True))

    def test_ffmpeg_merger_failure_is_terminal(self):
        output = '[Merger] Merging formats into "video.mp4"\nERROR: ffmpeg exited with code 1: conversion failed!'
        res = classify_failure(output, stage="Merging")
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.FFMPEG)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output, stage="Merging"))

    def test_disk_full_is_terminal(self):
        output = 'ERROR: [Errno 28] No space left on device'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.LOCAL_STORAGE)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_permission_denied_is_terminal(self):
        output = 'ERROR: [Errno 13] Permission denied: "C:\\Downloads\\video.mp4"'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.PERMISSION)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_missing_runtime_executable_is_terminal(self):
        output = 'ERROR: ffmpeg not found. Please ensure FFmpeg is installed.'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.MISSING_RUNTIME)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_drm_protected_is_terminal(self):
        output = 'ERROR: This video is DRM protected and cannot be downloaded'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.DRM)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_authentic_private_video_is_terminal(self):
        output = 'ERROR: Private video. Sign in if you\'ve been granted access to this video'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.AUTHENTICATION)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_bare_unsupported_url_without_page_fetch_is_terminal(self):
        output = 'ERROR: [generic] Unsupported URL: foo://invalid-scheme/test'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.UNSUPPORTED)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output))

    def test_post_transfer_failure_is_terminal(self):
        output = '__VRKA_TITLE__ Test Video\n[download] Destination: video.mp4\n[download] 50.0% of 100MiB\nERROR: HTTP Error 403: Forbidden'
        res = classify_failure(output, transferred=True)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.POST_TRANSFER)
        self.assertFalse(res.is_recoverable)
        self.assertFalse(is_browser_recoverable(output, transferred=True))

    def test_bare_kvs_mention_without_player_context_is_not_recoverable(self):
        """Correction 1: Bare occurrence of 'kvs' without extraction/player context."""
        output = 'ERROR: Server returned error on kvs_sync query'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertFalse(res.is_recoverable)

    def test_bare_jsondecodeerror_without_player_context_is_not_recoverable(self):
        """Correction 3: Bare JSONDecodeError without player/config context."""
        output = 'JSONDecodeError: Expecting value: line 1 column 1 (char 0)'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertFalse(res.is_recoverable)

    def test_http_403_post_transfer_is_terminal(self):
        """Correction 2: HTTP 403 after transfer started must remain terminal."""
        output = '[download] Destination: video.mp4\nERROR: The download stream was cut off: HTTP Error 403: Forbidden'
        res = classify_failure(output)
        self.assertEqual(res.action, RecoveryAction.NON_BROWSER_RECOVERABLE)
        self.assertEqual(res.category, FailureCategory.POST_TRANSFER)
        self.assertFalse(res.is_recoverable)

    # ------------------------------------------------------------------
    # Group C: Downloader Integration & Anti-Recursion Guarantees
    # ------------------------------------------------------------------

    def test_ytdlp_command_error_delegates_to_classifier(self):
        exc = YTDLPCommandError('flashvars failure', category='flashvars', output='[generic] Unable to extract flashvars')
        self.assertTrue(direct_failure_is_browser_recoverable(exc))

    def test_ytdlp_command_error_dns_is_not_recoverable(self):
        exc = YTDLPCommandError('dns error', category='dns', output='getaddrinfo failed')
        self.assertFalse(direct_failure_is_browser_recoverable(exc))

    def test_automatic_fallback_executor_triggers_on_eligible_failure(self):
        record = MagicMock()
        record.spec.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        direct_called = False
        browser_called = False

        def direct(_rec, _ctx):
            nonlocal direct_called
            direct_called = True
            raise DirectPathEligibleForFallback("Flashvars error", category="flashvars", reason="Webpage uses flashvars")

        def browser(_rec, _ctx):
            nonlocal browser_called
            browser_called = True

        executor = AutomaticFallbackExecutor(direct, browser)
        executor(record, context)

        self.assertTrue(direct_called)
        self.assertTrue(browser_called)
        context.log.assert_called()

    def test_automatic_fallback_executor_does_not_trigger_recursively(self):
        """Anti-recursion: fallback must execute at most once per task."""
        record = MagicMock()
        record.spec.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        browser_call_count = 0

        def direct(_rec, _ctx):
            raise DirectPathEligibleForFallback("Flashvars error", category="flashvars")

        def browser(_rec, _ctx):
            nonlocal browser_call_count
            browser_call_count += 1

        executor = AutomaticFallbackExecutor(direct, browser)
        # First execution triggers fallback
        executor(record, context)
        self.assertEqual(browser_call_count, 1)

        # Second execution on the same executor cannot re-trigger fallback
        with self.assertRaises(DirectPathEligibleForFallback):
            executor(record, context)
        self.assertEqual(browser_call_count, 1)

    def test_automatic_fallback_executor_inactive_transfer_is_not_eligible(self):
        record = MagicMock()
        record.spec.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        def direct(_rec, _ctx):
            raise ProcessInactivity(ActivityPhase.TRANSFER, 120.0, eligible_for_fallback=False)

        def browser(_rec, _ctx):
            self.fail("Browser fallback should not be invoked for transfer inactivity")

        executor = AutomaticFallbackExecutor(direct, browser)
        with self.assertRaises(ProcessInactivity):
            executor(record, context)


class EndToEndRoutingTests(unittest.TestCase):
    """Verify complete end-to-end routing from direct extraction failure to browser fallback."""

    def test_e2e_flashvars_routes_to_browser_fallback(self):
        """Complete routing: flashvars failure -> BROWSER_RECOVERABLE -> DirectPathEligibleForFallback -> AutomaticFallbackExecutor -> browser fallback."""
        task = MagicMock()
        task.mode = "video"
        task.options = {"browser_fallback_enabled": True}
        context = MagicMock()
        context.cancel_event.is_set.return_value = False

        downloader = MagicMock()
        flashvars_error = YTDLPCommandError(
            "Player config error",
            category="flashvars",
            output="ERROR: [generic] Unable to extract flashvars; please report this issue",
            reason="Webpage uses flashvars player configuration requiring browser rendering",
        )
        downloader._run_standard_task.side_effect = flashvars_error

        # Bind the real _run_core_direct_attempt method
        downloader._run_core_direct_attempt = VRKADownloader._run_core_direct_attempt.__get__(downloader)

        direct_called = False
        browser_called = False

        def direct(_record, active_context):
            nonlocal direct_called
            direct_called = True
            return downloader._run_core_direct_attempt(task, "/tmp/out", active_context)

        def browser(_record, _context):
            nonlocal browser_called
            browser_called = True

        record = MagicMock()
        record.spec.options = task.options
        record.spec.mode = task.mode

        def _browser_fallback_wrapped(active_record, active_context):
            task.options["_browser_fallback_attempted"] = True
            return browser(active_record, active_context)

        executor = AutomaticFallbackExecutor(
            direct,
            _browser_fallback_wrapped,
            enabled=lambda current: (
                current.spec.mode != "custom"
                and bool(current.spec.options.get("browser_fallback_enabled", True))
                and not bool(task.options.get("_browser_fallback_attempted", False))
            ),
        )

        executor(record, context)

        self.assertTrue(direct_called)
        self.assertTrue(browser_called)
        self.assertTrue(task.options.get("_browser_fallback_attempted"))

        # State transitions to fallback must be emitted
        context.transition.assert_any_call(
            DownloadState.DIRECT_FAILED_ELIGIBLE_FOR_FALLBACK,
            message="Direct extraction failed; Browser Fallback eligible",
        )
        context.transition.assert_any_call(
            DownloadState.BROWSER_STARTING,
            message="Browser Fallback started for the same task",
        )

    def test_e2e_tls_failure_does_not_route_to_browser_fallback(self):
        """TLS failure is terminal: no browser fallback."""
        task = MagicMock()
        task.mode = "video"
        task.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        downloader = MagicMock()
        downloader._run_standard_task.side_effect = YTDLPCommandError(
            "TLS failed",
            category="tls",
            output="ERROR: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed",
        )
        downloader._run_core_direct_attempt = VRKADownloader._run_core_direct_attempt.__get__(downloader)

        browser_called = False

        def direct(_record, active_context):
            return downloader._run_core_direct_attempt(task, "/tmp/out", active_context)

        def browser(_record, _context):
            nonlocal browser_called
            browser_called = True

        record = MagicMock()
        record.spec.options = task.options
        record.spec.mode = task.mode

        executor = AutomaticFallbackExecutor(direct, browser)

        with self.assertRaises(YTDLPCommandError) as cm:
            executor(record, context)

        self.assertEqual(cm.exception.category, "tls")
        self.assertFalse(browser_called)

    def test_e2e_post_transfer_http_403_does_not_route_to_browser_fallback(self):
        """Post-transfer HTTP 403 is terminal: no browser fallback."""
        task = MagicMock()
        task.mode = "video"
        task.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        downloader = MagicMock()
        downloader._run_standard_task.side_effect = YTDLPCommandError(
            "Transfer interrupted",
            category="post_transfer",
            output="[download] Destination: video.mp4\nERROR: HTTP Error 403: Forbidden",
        )
        downloader._run_core_direct_attempt = VRKADownloader._run_core_direct_attempt.__get__(downloader)

        browser_called = False

        def direct(_record, active_context):
            return downloader._run_core_direct_attempt(task, "/tmp/out", active_context)

        def browser(_record, _context):
            nonlocal browser_called
            browser_called = True

        record = MagicMock()
        record.spec.options = task.options
        record.spec.mode = task.mode

        executor = AutomaticFallbackExecutor(direct, browser)

        with self.assertRaises(YTDLPCommandError) as cm:
            executor(record, context)

        self.assertEqual(cm.exception.category, "post_transfer")
        self.assertFalse(browser_called)

    def test_e2e_cancellation_does_not_route_to_browser_fallback(self):
        """Cancellation stops processing immediately: no browser fallback."""
        task = MagicMock()
        task.mode = "video"
        task.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        downloader = MagicMock()
        downloader._run_standard_task.side_effect = DownloadCanceled("Cancelled")
        downloader._run_core_direct_attempt = VRKADownloader._run_core_direct_attempt.__get__(downloader)

        browser_called = False

        def direct(_record, active_context):
            return downloader._run_core_direct_attempt(task, "/tmp/out", active_context)

        def browser(_record, _context):
            nonlocal browser_called
            browser_called = True

        record = MagicMock()
        record.spec.options = task.options
        record.spec.mode = task.mode

        executor = AutomaticFallbackExecutor(direct, browser)

        with self.assertRaises(DownloadCanceled):
            executor(record, context)

        self.assertFalse(browser_called)

    def test_e2e_successful_direct_extraction_does_not_route_to_browser_fallback(self):
        """Successful direct extraction completes without fallback."""
        task = MagicMock()
        task.mode = "video"
        task.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        downloader = MagicMock()
        downloader._run_standard_task.return_value = None
        downloader._run_core_direct_attempt = VRKADownloader._run_core_direct_attempt.__get__(downloader)

        browser_called = False

        def direct(_record, active_context):
            return downloader._run_core_direct_attempt(task, "/tmp/out", active_context)

        def browser(_record, _context):
            nonlocal browser_called
            browser_called = True

        record = MagicMock()
        record.spec.options = task.options
        record.spec.mode = task.mode

        executor = AutomaticFallbackExecutor(direct, browser)
        executor(record, context)

        self.assertFalse(browser_called)

    def test_e2e_browser_fallback_failure_terminates_without_retry(self):
        """Browser fallback failure terminates in FAILED state; no second fallback attempt occurs."""
        task = MagicMock()
        task.mode = "video"
        task.options = {"browser_fallback_enabled": True}
        context = MagicMock()

        downloader = MagicMock()
        downloader._run_standard_task.side_effect = YTDLPCommandError(
            "Player error",
            category="flashvars",
            output="ERROR: [generic] Unable to extract flashvars",
        )
        downloader._run_core_direct_attempt = VRKADownloader._run_core_direct_attempt.__get__(downloader)

        fallback_count = 0

        def direct(_record, active_context):
            return downloader._run_core_direct_attempt(task, "/tmp/out", active_context)

        def browser(_record, _context):
            nonlocal fallback_count
            fallback_count += 1
            raise BrowserFallbackError("No playable media was observed in the protected browser")

        record = MagicMock()
        record.spec.options = task.options
        record.spec.mode = task.mode

        def _browser_fallback_wrapped(active_record, active_context):
            task.options["_browser_fallback_attempted"] = True
            return browser(active_record, active_context)

        executor = AutomaticFallbackExecutor(
            direct,
            _browser_fallback_wrapped,
            enabled=lambda current: (
                current.spec.mode != "custom"
                and bool(current.spec.options.get("browser_fallback_enabled", True))
                and not bool(task.options.get("_browser_fallback_attempted", False))
            ),
        )

        with self.assertRaises(BrowserFallbackError) as cm:
            executor(record, context)

        self.assertIn("No playable media was observed", str(cm.exception))
        self.assertEqual(fallback_count, 1)
        self.assertTrue(task.options.get("_browser_fallback_attempted"))

        # A second invocation of the executor on the same task cannot re-trigger fallback
        with self.assertRaises(DirectPathEligibleForFallback):
            executor(record, context)
        self.assertEqual(fallback_count, 1)


if __name__ == '__main__':
    unittest.main()

