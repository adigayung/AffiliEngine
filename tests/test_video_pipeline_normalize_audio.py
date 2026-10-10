"""
Test untuk fitur "Normalize Audio" pada Video Pipeline.

Kontrak yang diuji:
  1. Template (/video_pipeline/):
       - checkbox `id="normalizeAudio"` ada, default CHECKED (ON),
       - posisinya di antara "Tambahkan Music" dan "Edit Audio dB",
       - nilainya ikut dikirim saat submit (`form.append("normalize_audio", ...)`).
  2. Router (routers/video_pipeline/index.py):
       - `normalize_audio` dibaca dari form, default True bila tidak ada/kosong,
       - diteruskan ke `PipelineRunner.start()`.
  3. PipelineRunner:
       - `start()` menyimpan flag dan meneruskannya ke `create_video()`.
  4. Processor (includes/video_pipeline/processor.py):
       - `create_video()` / `_process_single_folder()` menerima `normalize_audio`,
       - normalisasi dijalankan SESUDAH decode dan SEBELUM edit audio dB &
         add sound, output normalisasi dipakai sebagai input langkah berikutnya,
       - gagal normalisasi tidak menggagalkan pipeline (lanjut tanpa normalisasi).
  5. Wrapper library (includes/video_pipeline/audio_normalize.py):
       - `normalize_video_file()` dapat dipanggil programatik (tidak pernah
         memanggil sys.exit), mengembalikan path output atau None,
       - kegagalan FFmpeg menjadi `AudioNormalizeError` (CLI tetap exit 1).

Environment test ini tidak punya cv2/flask, jadi modul dependency berat
di-stub terlebih dahulu (pola sama seperti test lain di repo ini).

Jalankan:
    python -m unittest tests.test_video_pipeline_normalize_audio -v
"""

import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT_DIR, "templates", "video_pipeline", "index.html")


# ------------------------------------------------------------------
# STUB dependency berat (cv2 / flask / seleniumbase) yang tidak
# tersedia di environment test. Harus dipasang SEBELUM import modul.
# ------------------------------------------------------------------

def _stub_module(name, **attrs):
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


_stub_module(
    "includes.video_pipeline.decode_video",
    decode_single_video=lambda *a, **k: None,
)
_stub_module(
    "includes.video_pipeline.add_sound",
    add_sound=lambda *a, **k: None,
)
_stub_module(
    "includes.video_pipeline.zoom_video",
    zoom_video=lambda *a, **k: None,
)
_stub_module(
    "includes.video_pipeline.upscale_video",
    upscale_video=lambda *a, **k: None,
)


class _FakeForm(dict):
    """Minimal dict-like FormData."""

    def get(self, key, default=None):
        return dict.get(self, key, default)


class _FakeRequest:
    def __init__(self, form=None):
        self.form = _FakeForm(form or {})


class _FakeBlueprint:
    def __init__(self, *args, **kwargs):
        pass

    def route(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator


try:  # gunakan flask asli bila tersedia; jangan pernah menimpanya
    import flask as _flask  # noqa: F401
    _FLASK_STUBBED = False
except ImportError:
    _FLASK_STUBBED = True
    _stub_module(
        "flask",
        Blueprint=_FakeBlueprint,
        render_template=lambda *a, **k: "",
        request=_FakeRequest({}),
        jsonify=lambda payload=None, *a, **k: payload,
    )

_STUBBED_MODULES = [
    "includes.video_pipeline.decode_video",
    "includes.video_pipeline.add_sound",
    "includes.video_pipeline.zoom_video",
    "includes.video_pipeline.upscale_video",
]

# Modul ASLI di bawah test.
import includes.video_pipeline.audio_normalize as audio_normalize  # noqa: E402
import includes.video_pipeline.processor as processor  # noqa: E402
import routers.video_pipeline.index as pipeline_router  # noqa: E402

# Stub hanya dipakai untuk mengimpor modul di atas. Bersihkan dari
# sys.modules agar tidak mengganggu test lain (mis. test yang butuh flask
# /cv2 asli).
if _FLASK_STUBBED:
    sys.modules.pop("flask", None)
for _name in _STUBBED_MODULES:
    sys.modules.pop(_name, None)


# ==================================================================
# 1. Template
# ==================================================================

class TestTemplateContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_checkbox_exists(self):
        self.assertIn('id="normalizeAudio"', self.html)
        self.assertIn("Normalize Audio", self.html)

    def test_checkbox_is_checked_by_default(self):
        idx = self.html.index('id="normalizeAudio"')
        block = self.html[idx:self.html.index('<span class="form-check-label">', idx)]
        self.assertIn('type="checkbox"', block)
        self.assertIn("checked", block)

    def test_position_between_add_music_and_edit_audio_db(self):
        add_music = self.html.index('id="addMusic"')
        normalize = self.html.index('id="normalizeAudio"')
        edit_db = self.html.index('id="editAudioDb"')
        self.assertLess(add_music, normalize)
        self.assertLess(normalize, edit_db)

    def test_value_is_submitted_with_the_form(self):
        self.assertIn('form.append("normalize_audio"', self.html)
        idx = self.html.index('form.append("normalize_audio"')
        line = self.html[idx:self.html.index("\n", idx)]
        self.assertIn("normalizeAudio.checked", line)

    def test_field_is_disabled_while_running(self):
        self.assertIn("normalizeAudio.disabled = true;", self.html)
        self.assertIn("normalizeAudio.disabled = false;", self.html)


# ==================================================================
# 2 + 3. Router & PipelineRunner
# ==================================================================

class TestRouterContract(unittest.TestCase):
    def setUp(self):
        self.tmp_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_root, True)
        self._request_patch = mock.patch.object(
            pipeline_router, "request", _FakeRequest({})
        )
        self.fake_request = self._request_patch.start()
        self.addCleanup(self._request_patch.stop)

    def _post_start(self, form):
        self.fake_request.form = _FakeForm(form)
        with mock.patch.object(
            pipeline_router, "jsonify", lambda payload=None, *a, **k: payload
        ), mock.patch.object(
            pipeline_router.pipeline_runner, "start", return_value=True
        ) as start_mock:
            response = pipeline_router.start()
        return response, start_mock

    def test_default_is_on_when_field_missing(self):
        response, start_mock = self._post_start({"root_path": self.tmp_root})
        self.assertIsInstance(response, dict)
        self.assertTrue(response["success"])
        self.assertTrue(start_mock.call_args.kwargs["normalize_audio"])

    def test_default_is_on_when_field_blank(self):
        _, start_mock = self._post_start(
            {"root_path": self.tmp_root, "normalize_audio": "   "}
        )
        self.assertTrue(start_mock.call_args.kwargs["normalize_audio"])

    def test_checked_value_is_forwarded(self):
        _, start_mock = self._post_start(
            {"root_path": self.tmp_root, "normalize_audio": "1"}
        )
        self.assertTrue(start_mock.call_args.kwargs["normalize_audio"])

    def test_unchecked_value_is_forwarded(self):
        _, start_mock = self._post_start(
            {"root_path": self.tmp_root, "normalize_audio": "0"}
        )
        self.assertFalse(start_mock.call_args.kwargs["normalize_audio"])

    def test_to_bool_pattern_unchanged(self):
        self.assertTrue(pipeline_router._to_bool(None, True))
        self.assertTrue(pipeline_router._to_bool("on", False))
        self.assertFalse(pipeline_router._to_bool("0", True))


class TestPipelineRunnerContract(unittest.TestCase):
    def test_start_passes_normalize_audio_to_thread(self):
        runner = pipeline_router.PipelineRunner()
        runner._run_pipeline = mock.Mock()
        runner.start(
            "C:\\root",
            preserve_audio=True,
            add_music=True,
            normalize_audio=False,
            edit_audio_db=True,
            audio_db=2.0,
        )
        runner.thread.join(timeout=5)
        args = runner._run_pipeline.call_args.args
        self.assertEqual(args[0], "C:\\root")
        self.assertIs(args[1], True)   # preserve_audio
        self.assertIs(args[2], True)   # add_music
        self.assertIs(args[3], False)  # normalize_audio
        self.assertIs(args[4], True)   # edit_audio_db
        self.assertEqual(args[5], 2.0)  # audio_db

    def test_start_defaults_normalize_audio_on(self):
        runner = pipeline_router.PipelineRunner()
        runner._run_pipeline = mock.Mock()
        runner.start("C:\\root")
        runner.thread.join(timeout=5)
        self.assertIs(runner._run_pipeline.call_args.args[3], True)

    def test_run_pipeline_forwards_flag_to_create_video(self):
        runner = pipeline_router.PipelineRunner()
        with mock.patch.object(
            pipeline_router, "create_video",
            return_value={"succeeded": 1, "failed": 0},
        ) as create_mock:
            runner._run_pipeline("C:\\root", False, True, True, False, 0.0)

        kwargs = create_mock.call_args.kwargs
        self.assertTrue(kwargs["normalize_audio"])
        self.assertEqual(create_mock.call_args.args[0], "C:\\root")


# ==================================================================
# 4. Processor
# ==================================================================

class TestProcessorPipeline(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)

        self.job_dir = os.path.join(self.root, "job1")
        self.asset_dir = os.path.join(self.job_dir, "aseets")
        os.makedirs(self.asset_dir)

        self.video_path = os.path.join(self.asset_dir, "a.mp4")
        self._write(self.video_path)

        self.sound_json = os.path.join(self.asset_dir, "sound.json")
        self._write(
            self.sound_json,
            json.dumps({"music_list": [os.path.join(self.root, "music.mp3")]}),
        )

        self.schedule_json = os.path.join(self.job_dir, "schedule.json")
        self._write(self.schedule_json, json.dumps({"files": {"video": "final.mp4"}}))

        self.folder_info = {
            "video_path": self.video_path,
            "sound_json_path": self.sound_json,
            "asset_dir": self.asset_dir,
            "job_dir": self.job_dir,
        }

        self.calls = []
        self.logs = []

    @staticmethod
    def _write(path, content=""):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _log(self, message):
        self.logs.append(message)

    def _patch_pipeline(self, normalize_result="auto"):
        """Patch semua step pipeline dan catat urutan pemanggilannya."""

        def fake_decode(video_path, preserve_audio=False):
            self.calls.append("decode")
            out = os.path.join(self.asset_dir, "output.mp4")
            self._write(out)
            return out

        def fake_normalize_video_file(input_path, output_path=None, **kwargs):
            self.calls.append("normalize")
            self.normalize_args = (input_path, output_path, kwargs)
            if normalize_result == "fail":
                return None
            out = output_path or (os.path.splitext(input_path)[0] + "_normalized.mp4")
            self._write(out, "normalized")
            self.normalized_output = out
            return out

        def fake_adjust_db(input_video, audio_db, log_callback=None):
            self.calls.append("edit_audio_db")
            if audio_db == 0:
                return input_video
            out = input_video.with_stem(input_video.stem + "_db")
            self._write(str(out))
            self.adjusted_output = str(out)
            return out

        def fake_add_sound(video_input, music_file, preserve_audio=False):
            self.calls.append("add_sound")
            self.add_sound_input = video_input
            out = os.path.join(self.asset_dir, "sound_output.mp4")
            self._write(out)
            return out

        def fake_zoom(video_input, scale=1.05):
            self.calls.append("zoom")
            self.zoom_input = video_input
            out = os.path.join(self.asset_dir, "zoom_output.mp4")
            self._write(out)
            return out

        def fake_upscale(video_input):
            self.calls.append("upscale")
            self.upscale_input = video_input
            out = os.path.join(self.asset_dir, "upscale_output.mp4")
            self._write(out)
            return out

        patches = [
            mock.patch.object(processor, "decode_single_video", fake_decode),
            mock.patch.object(processor, "normalize_video_file", fake_normalize_video_file),
            mock.patch.object(processor, "_has_audio_stream", lambda p: True),
            mock.patch.object(processor, "_adjust_audio_db", fake_adjust_db),
            mock.patch.object(processor, "add_sound", fake_add_sound),
            mock.patch.object(processor, "zoom_video", fake_zoom),
            mock.patch.object(processor, "upscale_video", fake_upscale),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _run(self, **kwargs):
        params = {
            "preserve_audio": True,
            "add_music": True,
            "normalize_audio": True,
            "edit_audio_db": False,
            "audio_db": 0.0,
        }
        params.update(kwargs)
        return processor._process_single_folder(
            self.folder_info, 0, self._log, **params
        )

    def test_normalize_runs_after_decode_before_db_and_sound(self):
        self._patch_pipeline()
        ok = self._run(normalize_audio=True, edit_audio_db=True, audio_db=3.0)

        self.assertTrue(ok)
        self.assertEqual(
            self.calls,
            ["decode", "normalize", "edit_audio_db", "add_sound", "zoom", "upscale"],
        )

    def test_normalized_output_feeds_next_step(self):
        self._patch_pipeline()
        self._run(normalize_audio=True, edit_audio_db=False)

        input_path, output_path, _kwargs = self.normalize_args
        self.assertTrue(input_path.endswith("output.mp4"))
        self.assertTrue(output_path.endswith("output_normalized.mp4"))
        # add_sound harus menerima hasil normalisasi (bukan hasil decode)
        self.assertEqual(self.add_sound_input, self.normalized_output)

    def test_normalize_can_be_disabled(self):
        self._patch_pipeline()
        ok = self._run(normalize_audio=False)

        self.assertTrue(ok)
        self.assertNotIn("normalize", self.calls)
        self.assertEqual(self.add_sound_input, os.path.join(self.asset_dir, "output.mp4"))

    def test_normalize_failure_does_not_fail_pipeline(self):
        self._patch_pipeline(normalize_result="fail")
        ok = self._run(normalize_audio=True)

        self.assertTrue(ok)
        self.assertIn("normalize", self.calls)
        # Lanjut memakai file hasil decode.
        self.assertEqual(self.add_sound_input, os.path.join(self.asset_dir, "output.mp4"))
        self.assertTrue(any("Normalize audio gagal" in m for m in self.logs))

    def test_normalized_temp_file_is_cleaned_up(self):
        self._patch_pipeline()
        self._run(normalize_audio=True)

        self.assertFalse(os.path.exists(self.normalized_output))
        self.assertTrue(os.path.exists(os.path.join(self.job_dir, "final.mp4")))

    def test_create_video_forwards_normalize_audio(self):
        patched_folder = self.folder_info
        with mock.patch.object(processor, "_scan_folders", return_value=[patched_folder]), \
                mock.patch.object(processor, "_process_single_folder", return_value=True) as proc_mock:
            processor.create_video(self.root, normalize_audio=True)

        self.assertTrue(proc_mock.call_args.kwargs["normalize_audio"])

    def test_create_video_normalize_audio_off(self):
        with mock.patch.object(processor, "_scan_folders", return_value=[self.folder_info]), \
                mock.patch.object(processor, "_process_single_folder", return_value=True) as proc_mock:
            processor.create_video(self.root, normalize_audio=False)

        self.assertFalse(proc_mock.call_args.kwargs["normalize_audio"])


# ==================================================================
# 5. Wrapper library audio_normalize
# ==================================================================

class TestNormalizeVideoFileWrapper(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.input_path = os.path.join(self.tmp, "a.mp4")
        with open(self.input_path, "w", encoding="utf-8") as f:
            f.write("dummy")
        self.logs = []

    def _log(self, message):
        self.logs.append(message)

    def test_missing_input_returns_none(self):
        result = audio_normalize.normalize_video_file(
            os.path.join(self.tmp, "tidak-ada.mp4"), log_callback=self._log
        )
        self.assertIsNone(result)
        self.assertTrue(any("tidak ditemukan" in m for m in self.logs))

    def test_missing_ffmpeg_returns_none(self):
        with mock.patch.object(audio_normalize.shutil, "which", return_value=None):
            result = audio_normalize.normalize_video_file(
                self.input_path, log_callback=self._log
            )
        self.assertIsNone(result)

    def test_no_audio_stream_returns_none(self):
        with mock.patch.object(audio_normalize, "has_audio", return_value=False):
            result = audio_normalize.normalize_video_file(
                self.input_path, log_callback=self._log
            )
        self.assertIsNone(result)
        self.assertTrue(any("tidak ada stream audio" in m for m in self.logs))

    def test_success_returns_output_path(self):
        expected = os.path.join(self.tmp, "a_normalized.mp4")

        def fake_normalize(input_path, output_path, **kwargs):
            self.assertEqual(input_path, self.input_path)
            self.assertEqual(output_path, expected)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("normalized")
            return -20.0, 6.0, True

        with mock.patch.object(audio_normalize, "has_audio", return_value=True), \
                mock.patch.object(audio_normalize, "normalize", side_effect=fake_normalize):
            result = audio_normalize.normalize_video_file(
                self.input_path, log_callback=self._log
            )

        self.assertEqual(result, expected)
        self.assertTrue(any("[OK] Normalize audio" in m for m in self.logs))

    def test_explicit_output_path_is_used(self):
        expected = os.path.join(self.tmp, "custom.mp4")

        def fake_normalize(input_path, output_path, **kwargs):
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("x")
            return -18.0, 4.0, False

        with mock.patch.object(audio_normalize, "has_audio", return_value=True), \
                mock.patch.object(audio_normalize, "normalize", side_effect=fake_normalize):
            result = audio_normalize.normalize_video_file(
                self.input_path, output_path=expected, log_callback=self._log
            )

        self.assertEqual(result, expected)

    def test_error_is_swallowed_and_returns_none(self):
        with mock.patch.object(audio_normalize, "has_audio", return_value=True), \
                mock.patch.object(
                    audio_normalize, "normalize",
                    side_effect=audio_normalize.AudioNormalizeError("boom"),
                ):
            result = audio_normalize.normalize_video_file(
                self.input_path, log_callback=self._log
            )

        self.assertIsNone(result)
        self.assertTrue(any("gagal" in m for m in self.logs))

    def test_normalize_raises_instead_of_sys_exit(self):
        """Kegagalan FFmpeg -> AudioNormalizeError (bukan sys.exit)."""
        failing = mock.Mock(returncode=1, stdout="", stderr="ffmpeg error detail")
        with mock.patch.object(audio_normalize.subprocess, "run", return_value=failing):
            with self.assertRaises(audio_normalize.AudioNormalizeError):
                audio_normalize.normalize(
                    self.input_path,
                    os.path.join(self.tmp, "out.mp4"),
                    target_i=-14.0,
                    target_tp=-1.0,
                    target_lra=11.0,
                    nr_amount=3,
                )

    def test_cli_converts_error_to_exit_1(self):
        with mock.patch.object(sys, "argv", ["audio_normalize.py", self.input_path]), \
                mock.patch.object(audio_normalize, "check_ffmpeg"), \
                mock.patch.object(audio_normalize, "check_enhance_deps"), \
                mock.patch.object(audio_normalize, "has_audio", return_value=True), \
                mock.patch.object(
                    audio_normalize, "normalize",
                    side_effect=audio_normalize.AudioNormalizeError("boom"),
                ):
            with self.assertRaises(SystemExit) as ctx:
                audio_normalize.main()

        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
