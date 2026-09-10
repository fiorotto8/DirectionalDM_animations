#!/usr/bin/env python3
"""Render, verify, and package the complete CYGNO animation release matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cygno_anim.config import (  # noqa: E402
    ConfigurationError,
    assert_publication_clearance,
    load_branding,
    load_local,
    load_scene_manifest,
)


MEDIA_ROOT = ROOT / "media"
VIDEO_ROOT = MEDIA_ROOT / "videos"
DIST_ROOT = ROOT / "dist"


@dataclass(frozen=True)
class Profile:
    name: str
    width: int
    height: int
    fps: int
    crf: int | None


PREVIEW = Profile("480p30", 854, 480, 30, None)
MASTER = Profile("1080p60", 1920, 1080, 60, 18)


def _tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"Required executable is not available: {name}")
    return executable


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _ffmpeg_wrapper(directory: Path, real_ffmpeg: str, crf: int) -> tuple[Path, Path]:
    """Create an ephemeral first-generation CRF injector for Manim."""

    wrapper = directory / "ffmpeg"
    invocation_log = directory / "x264-invocations.log"
    source = f'''#!/usr/bin/env python3
import os
import sys

real = {real_ffmpeg!r}
log = {str(invocation_log)!r}
args = sys.argv[1:]
if "libx264" in args:
    if "-crf" in args:
        args[args.index("-crf") + 1] = "{crf}"
    else:
        output = args[-1]
        args = [*args[:-1], "-crf", "{crf}", output]
    if "-preset" not in args:
        output = args[-1]
        args = [*args[:-1], "-preset", "slow", output]
    with open(log, "a", encoding="utf-8") as stream:
        stream.write("libx264 crf={crf}\\n")
os.execv(real, [real, *args])
'''
    wrapper.write_text(source, encoding="utf-8")
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return wrapper, invocation_log


def _manifest_scene(scene_id: str) -> dict[str, Any]:
    for scene in load_scene_manifest():
        if scene["id"] == scene_id:
            return scene
    known = ", ".join(item["id"] for item in load_scene_manifest())
    raise ConfigurationError(f"Unknown scene {scene_id!r}; expected one of: {known}")


def _destination(
    scene: dict[str, Any],
    profile: Profile,
    suffix: str = ".mp4",
    *,
    video_root: Path = VIDEO_ROOT,
) -> Path:
    return video_root / scene["id"] / profile.name / f"{scene['output_name']}{suffix}"


def _locate_render(media_dir: Path, output_name: str) -> Path:
    matches = [
        path
        for path in media_dir.rglob(f"{output_name}.mp4")
        if "partial_movie_files" not in path.parts
    ]
    if not matches:
        raise RuntimeError(f"Manim did not produce {output_name}.mp4 below {media_dir}")
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def _faststart(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".installing.mp4")
    temporary.unlink(missing_ok=True)
    _run(
        [
            _tool("ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0",
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(temporary),
        ]
    )
    os.replace(temporary, destination)


def render_mp4(
    scene: dict[str, Any], profile: Profile, work_root: Path, output_root: Path
) -> Path:
    if scene["requires_local_science"]:
        load_local(required=True)

    media_dir = work_root / scene["id"] / profile.name
    media_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "manim",
        "render",
        "--renderer",
        "cairo",
        "--resolution",
        f"{profile.width},{profile.height}",
        "--fps",
        str(profile.fps),
        "--format",
        "mp4",
        "--disable_caching",
        "--progress_bar",
        "none",
        "--media_dir",
        str(media_dir),
        "--output_file",
        scene["output_name"],
        scene["file"],
        scene["class_name"],
    ]

    environment = os.environ.copy()
    invocation_log: Path | None = None
    if profile.crf is not None:
        real_ffmpeg = _tool("ffmpeg")
        wrapper_dir = media_dir / ".ffmpeg-wrapper"
        wrapper_dir.mkdir(parents=True, exist_ok=True)
        _, invocation_log = _ffmpeg_wrapper(wrapper_dir, real_ffmpeg, profile.crf)
        environment["PATH"] = f"{wrapper_dir}{os.pathsep}{environment.get('PATH', '')}"

    _run(command, env=environment)
    if invocation_log is not None:
        invocations = (
            invocation_log.read_text(encoding="utf-8").splitlines()
            if invocation_log.is_file()
            else []
        )
        expected_record = f"libx264 crf={profile.crf}"
        if not invocations or any(item != expected_record for item in invocations):
            raise RuntimeError(
                f"{scene['id']}: Manim did not route every libx264 encode through CRF {profile.crf}"
            )
    rendered = _locate_render(media_dir, scene["output_name"])
    destination = _destination(scene, profile, video_root=output_root)
    _faststart(rendered, destination)
    verify_mp4(destination, profile)
    return destination


def make_gif(
    scene: dict[str, Any], preview: Path, work_root: Path, output_root: Path
) -> Path:
    temporary = work_root / scene["id"] / "gif" / f"{scene['output_name']}.gif"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            _tool("ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(preview),
            "-filter_complex",
            "[0:v]fps=30,scale=854:480:flags=lanczos,split[g0][g1];"
            "[g0]palettegen=max_colors=160:stats_mode=diff[p];"
            "[g1][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle",
            "-loop",
            "0",
            str(temporary),
        ]
    )
    destination = _destination(scene, PREVIEW, ".gif", video_root=output_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    installing = destination.with_suffix(".installing.gif")
    shutil.copy2(temporary, installing)
    os.replace(installing, destination)
    verify_gif(destination)
    return destination


def _probe(path: Path) -> dict[str, Any]:
    process = subprocess.run(
        [
            _tool("ffprobe"),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(process.stdout)


def _video_stream(probe: dict[str, Any]) -> dict[str, Any]:
    videos = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"]
    if len(videos) != 1:
        raise RuntimeError(f"Expected one video stream, found {len(videos)}")
    return videos[0]


def _full_decode(path: Path) -> None:
    _run(
        [
            _tool("ffmpeg"),
            "-v",
            "error",
            "-xerror",
            "-err_detect",
            "explode",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-f",
            "null",
            "-",
        ]
    )


def _fraction(value: str) -> Fraction:
    return Fraction(value)


def _contains_bytes(path: Path, needle: bytes) -> bool:
    """Search a large artifact without loading it all into memory."""

    overlap = max(0, len(needle) - 1)
    tail = b""
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            payload = tail + block
            if needle in payload:
                return True
            tail = payload[-overlap:] if overlap else b""
    return False


def _top_level_mp4_atoms(path: Path) -> list[bytes]:
    """Return top-level ISO BMFF atom names without reading media payloads."""

    atoms: list[bytes] = []
    file_size = path.stat().st_size
    offset = 0
    with path.open("rb") as stream:
        while offset + 8 <= file_size:
            stream.seek(offset)
            header = stream.read(8)
            atom_size = int.from_bytes(header[:4], "big")
            atom_name = header[4:8]
            header_size = 8
            if atom_size == 1:
                extended = stream.read(8)
                if len(extended) != 8:
                    raise RuntimeError(f"{path}: truncated extended MP4 atom")
                atom_size = int.from_bytes(extended, "big")
                header_size = 16
            elif atom_size == 0:
                atom_size = file_size - offset
            if atom_size < header_size or offset + atom_size > file_size:
                raise RuntimeError(f"{path}: invalid top-level MP4 atom")
            atoms.append(atom_name)
            offset += atom_size
    if offset != file_size:
        raise RuntimeError(f"{path}: trailing or truncated MP4 data")
    return atoms


def _decoded_frame_count(path: Path) -> int:
    process = subprocess.run(
        [
            _tool("ffprobe"),
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    try:
        count = int(process.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"{path}: decoded frame count is unavailable") from exc
    if count <= 0:
        raise RuntimeError(f"{path}: decoded frame count is not positive")
    return count


def _gif_loop_count(path: Path) -> int | None:
    """Parse the GIF application extension and return its loop count."""

    def read_exact(stream, size: int) -> bytes:
        payload = stream.read(size)
        if len(payload) != size:
            raise RuntimeError(f"{path}: truncated GIF structure")
        return payload

    def read_sub_blocks(stream) -> list[bytes]:
        blocks: list[bytes] = []
        while True:
            size = read_exact(stream, 1)[0]
            if size == 0:
                return blocks
            blocks.append(read_exact(stream, size))

    with path.open("rb") as stream:
        if read_exact(stream, 6) not in {b"GIF87a", b"GIF89a"}:
            raise RuntimeError(f"{path}: invalid GIF header")
        descriptor = read_exact(stream, 7)
        packed = descriptor[4]
        if packed & 0x80:
            read_exact(stream, 3 * (2 ** ((packed & 0x07) + 1)))

        while True:
            introducer = stream.read(1)
            if not introducer:
                raise RuntimeError(f"{path}: GIF trailer is absent")
            if introducer == b"\x3b":
                return None
            if introducer == b"\x21":
                extension_label = read_exact(stream, 1)
                if extension_label == b"\xff":
                    application = read_exact(stream, read_exact(stream, 1)[0])
                    blocks = read_sub_blocks(stream)
                    if application in {b"NETSCAPE2.0", b"ANIMEXTS1.0"}:
                        if not blocks or len(blocks[0]) < 3 or blocks[0][0] != 1:
                            raise RuntimeError(f"{path}: malformed GIF loop extension")
                        return int.from_bytes(blocks[0][1:3], "little")
                else:
                    read_sub_blocks(stream)
            elif introducer == b"\x2c":
                image_descriptor = read_exact(stream, 9)
                image_packed = image_descriptor[8]
                if image_packed & 0x80:
                    read_exact(stream, 3 * (2 ** ((image_packed & 0x07) + 1)))
                read_exact(stream, 1)
                read_sub_blocks(stream)
            else:
                raise RuntimeError(
                    f"{path}: unexpected GIF block introducer 0x{introducer.hex()}"
                )


def verify_mp4(path: Path, profile: Profile) -> float:
    if not path.is_file():
        raise RuntimeError(f"Missing output: {path}")
    probe = _probe(path)
    stream = _video_stream(probe)
    expected = {
        "codec_name": "h264",
        "pix_fmt": "yuv420p",
        "width": profile.width,
        "height": profile.height,
    }
    for key, value in expected.items():
        if stream.get(key) != value:
            raise RuntimeError(f"{path}: expected {key}={value}, got {stream.get(key)}")
    if _fraction(stream.get("r_frame_rate", "0/1")) != profile.fps:
        raise RuntimeError(f"{path}: expected {profile.fps} fps")
    if _fraction(stream.get("avg_frame_rate", "0/1")) != profile.fps:
        raise RuntimeError(f"{path}: average frame rate is not {profile.fps} fps")
    if any(item.get("codec_type") == "audio" for item in probe.get("streams", [])):
        raise RuntimeError(f"{path}: audio streams are not permitted")
    atoms = _top_level_mp4_atoms(path)
    if b"moov" not in atoms or b"mdat" not in atoms or atoms.index(b"moov") > atoms.index(b"mdat"):
        raise RuntimeError(f"{path}: MP4 is not fast-start optimized")
    if profile.crf is not None and not _contains_bytes(
        path, f"crf={profile.crf}.0".encode()
    ):
        raise RuntimeError(f"{path}: CRF {profile.crf} encoder marker is absent")
    duration = float(probe["format"]["duration"])
    decoded_frames = _decoded_frame_count(path)
    if abs(decoded_frames / duration - profile.fps) > 0.01:
        raise RuntimeError(
            f"{path}: decoded frame timing is inconsistent with {profile.fps} fps"
        )
    _full_decode(path)
    return duration


def verify_gif(path: Path) -> float:
    if not path.is_file():
        raise RuntimeError(f"Missing output: {path}")
    probe = _probe(path)
    stream = _video_stream(probe)
    if stream.get("codec_name") != "gif" or stream.get("width") != 854 or stream.get("height") != 480:
        raise RuntimeError(f"{path}: expected an 854x480 GIF")
    duration = float(probe["format"]["duration"])
    decoded_fps = _decoded_frame_count(path) / duration
    if not 29.5 <= decoded_fps <= 30.5:
        raise RuntimeError(
            f"{path}: decoded timing is {decoded_fps:.3f} fps, expected about 30 fps"
        )
    loop_count = _gif_loop_count(path)
    if loop_count != 0:
        raise RuntimeError(
            f"{path}: expected infinite GIF loop count 0, got {loop_count!r}"
        )
    _full_decode(path)
    return duration


def _newest_input(scene: dict[str, Any]) -> float:
    branding = load_branding()
    paths = [
        ROOT / scene["file"],
        *(ROOT / "cygno_anim").glob("*.py"),
        ROOT / "config" / "branding.yaml",
        ROOT / "config" / "science.yaml",
        ROOT / "config" / "scenes.yaml",
        ROOT / "scripts" / "render.py",
        ROOT / "requirements.txt",
        ROOT / branding["logo_path"],
        ROOT / branding["website_qr_path"],
        ROOT / branding["instagram_qr_path"],
    ]
    if scene["requires_local_science"]:
        local_override = os.environ.get("CYGNO_LOCAL_CONFIG")
        paths.append(
            Path(local_override).expanduser().resolve()
            if local_override
            else ROOT / "config" / "local.yaml"
        )
    return max(path.stat().st_mtime for path in paths if path.is_file())


def verify_instagram_artwork(frame, source: Path) -> None:
    """Check original Instagram nametag fidelity; it is not a standard QR.

    Instagram's stylized finder symbols require its own scanner. Match the
    central artwork in the decoded video instead of claiming a standard-QR
    decode for this asset.
    """
    import cv2
    template = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if template is None:
        raise RuntimeError(f"Missing Instagram artwork: {source}")
    code_width = float(load_branding()["outro"]["qr_width"])
    expected_width = frame.shape[1] * (code_width * 2350/1880) / (128/9)
    region = frame[:, int(frame.shape[1]*.50):]
    best = -1.0
    for width in range(round(expected_width)-3, round(expected_width)+4):
        scaled = cv2.resize(template, (width, round(width*template.shape[0]/template.shape[1])),
                            interpolation=cv2.INTER_AREA)
        height = scaled.shape[0]
        central = scaled[int(height*.10):int(height*.90), int(width*.10):int(width*.90)]
        score = cv2.matchTemplate(region, central, cv2.TM_CCOEFF_NORMED).max()
        best = max(best, float(score))
    if best < .88:
        raise RuntimeError(f"Original Instagram artwork is missing or altered (match {best:.3f})")


def verify_qr(scene: dict[str, Any], preview: Path, duration: float) -> None:
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "QR verification requires the pinned runtime dependencies"
        ) from exc

    branding = load_branding()
    expected = branding["website_url"]
    outro_duration = float(branding["outro"]["duration"])
    if duration < outro_duration:
        raise RuntimeError(f"{scene['id']}: video is shorter than the configured outro")
    with tempfile.TemporaryDirectory(prefix="cygno-qr-") as directory:
        offsets_from_end = (outro_duration - 0.8, outro_duration / 2.0, 0.4)
        for index, offset in enumerate(offsets_from_end):
            frame = Path(directory) / f"outro-{index}.png"
            timestamp = max(0.0, duration - offset)
            _run(
                [
                    _tool("ffmpeg"),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    f"{timestamp:.3f}",
                    "-i",
                    str(preview),
                    "-frames:v",
                    "1",
                    str(frame),
                ]
            )
            image = cv2.imread(str(frame))
            # Isolate the website code from the original Instagram nametag.
            width = image.shape[1]
            website_region = image[int(image.shape[0]*.30):, int(width*.10):int(width*.49)]
            decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(website_region)
            if not decoded:
                enlarged = cv2.resize(website_region, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(enlarged)
            from urllib.parse import urlsplit
            def target(url):
                parts = urlsplit(url)
                return parts.scheme, parts.netloc, parts.path.rstrip("/")
            # The supplied website QR includes a fragment; it still targets the
            # configured page. Preserve that original artwork and payload.
            if target(decoded) == target(expected):
                decoded = expected
            verify_instagram_artwork(image, ROOT / branding["instagram_qr_path"])
            if decoded != expected:
                raise RuntimeError(
                    f"{scene['id']}: QR at {timestamp:.3f}s decoded as {decoded!r}, expected {expected!r}"
                )


def verify_scene(
    scene: dict[str, Any],
    *,
    video_root: Path = VIDEO_ROOT,
    check_freshness: bool = True,
    check_qr: bool = True,
) -> None:
    preview = _destination(scene, PREVIEW, video_root=video_root)
    gif = _destination(scene, PREVIEW, ".gif", video_root=video_root)
    master = _destination(scene, MASTER, video_root=video_root)
    preview_duration = verify_mp4(preview, PREVIEW)
    gif_duration = verify_gif(gif)
    master_duration = verify_mp4(master, MASTER)
    tolerance = max(0.5, preview_duration * 0.005)
    if abs(preview_duration - gif_duration) > tolerance:
        raise RuntimeError(f"{scene['id']}: preview/GIF durations differ")
    if abs(preview_duration - master_duration) > tolerance:
        raise RuntimeError(f"{scene['id']}: preview/master durations differ")
    from scripts.provenance import verify as verify_provenance
    if check_freshness and not verify_provenance(scene, video_root):
        newest = _newest_input(scene)
        for output in (preview, gif, master):
            if output.stat().st_mtime < newest:
                raise RuntimeError(f"{output} is stale relative to source/configuration")
    if check_qr:
        verify_qr(scene, preview, preview_duration)


def render_scene(scene: dict[str, Any], work_root: Path, output_root: Path) -> None:
    preview = render_mp4(scene, PREVIEW, work_root, output_root)
    make_gif(scene, preview, work_root, output_root)
    render_mp4(scene, MASTER, work_root, output_root)
    verify_scene(scene, video_root=output_root, check_freshness=False)


def _expected_outputs(
    *,
    video_root: Path = VIDEO_ROOT,
    scenes: list[dict[str, Any]] | None = None,
) -> set[Path]:
    result: set[Path] = set()
    for scene in scenes if scenes is not None else load_scene_manifest():
        result.add(_destination(scene, PREVIEW, video_root=video_root))
        result.add(_destination(scene, PREVIEW, ".gif", video_root=video_root))
        result.add(_destination(scene, MASTER, video_root=video_root))
    return result


def _verify_output_shape(
    video_root: Path = VIDEO_ROOT,
    *,
    scenes: list[dict[str, Any]] | None = None,
) -> None:
    expected = {path.resolve() for path in _expected_outputs(video_root=video_root, scenes=scenes)}
    actual = {path.resolve() for path in video_root.rglob("*") if path.is_file()}
    if actual != expected:
        missing = sorted(str(path) for path in expected - actual)
        unexpected = sorted(str(path) for path in actual - expected)
        raise RuntimeError(
            "Output matrix mismatch; "
            f"missing={missing or 'none'}, unexpected={unexpected or 'none'}"
        )


def _remove_tree(path: Path, *, within: Path) -> None:
    """Remove one resolved child tree after validating its containment."""

    if not path.exists():
        return
    target = path.resolve()
    parent = within.resolve()
    if target == parent or parent not in target.parents:
        raise RuntimeError(f"Refusing to remove unsafe path: {target}")
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def _replace_directory(source: Path, destination: Path, *, within: Path) -> None:
    """Install a verified directory with rollback if the rename fails."""

    if not source.is_dir():
        raise RuntimeError(f"Staged directory is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = destination.with_name(f".{destination.name}.previous")
    _remove_tree(backup, within=within)
    had_destination = destination.exists()
    if had_destination:
        os.replace(destination, backup)
    try:
        os.replace(source, destination)
    except Exception:
        if had_destination and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    _remove_tree(backup, within=within)


def _clear_generated_side_outputs() -> None:
    """Remove only known horizontal caches; preserve other output families."""

    if not MEDIA_ROOT.exists():
        return
    for path in MEDIA_ROOT.iterdir():
        if path.name in {"images", "texts", "Tex"}:
            _remove_tree(path, within=MEDIA_ROOT)


def _new_render_staging() -> Path:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=".render-", dir=MEDIA_ROOT))


def render_all() -> None:
    scenes = load_scene_manifest()
    staging = _new_render_staging()
    work_root = staging / "work"
    output_root = staging / "videos"
    try:
        for scene in scenes:
            print(f"\n=== Rendering {scene['id']} ===", flush=True)
            render_scene(scene, work_root, output_root)
        _verify_output_shape(output_root, scenes=scenes)
        _replace_directory(output_root, VIDEO_ROOT, within=MEDIA_ROOT)
        from scripts.provenance import record
        for scene in scenes:
            record(scene, VIDEO_ROOT)
    finally:
        _remove_tree(staging, within=MEDIA_ROOT)
    _clear_generated_side_outputs()
    verify_all()


def verify_all() -> None:
    scenes = load_scene_manifest()
    _verify_output_shape(VIDEO_ROOT, scenes=scenes)
    for scene in scenes:
        print(f"Verifying {scene['id']}...", flush=True)
        verify_scene(scene)
    print("All 15 local artifacts passed verification.")


def package_release(tag: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", tag) or tag in {".", ".."}:
        raise ConfigurationError(
            "Release tag must be a simple 1-64 character name using letters, digits, '.', '_', or '-'"
        )
    assert_publication_clearance()
    verify_all()
    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    destination = DIST_ROOT / tag
    staging = Path(tempfile.mkdtemp(prefix=".package-", dir=DIST_ROOT))

    packaged: list[Path] = []
    try:
        for scene in load_scene_manifest():
            for suffix in (".mp4", ".gif"):
                source = _destination(scene, PREVIEW, suffix)
                target = staging / f"{scene['id']}{suffix}"
                shutil.copy2(source, target)
                packaged.append(target)

        checksum_path = staging / "SHA256SUMS"
        checksum_path.write_text(
            "".join(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
                for path in sorted(packaged)
            ),
            encoding="utf-8",
        )
        expected_names = {
            *(f"{scene['id']}{suffix}" for scene in load_scene_manifest() for suffix in (".mp4", ".gif")),
            "SHA256SUMS",
        }
        actual_names = {path.name for path in staging.iterdir() if path.is_file()}
        if len(packaged) != 10 or actual_names != expected_names:
            raise RuntimeError(
                "Release package must contain exactly ten media files plus SHA256SUMS"
            )
        _replace_directory(staging, destination, within=DIST_ROOT)
    finally:
        _remove_tree(staging, within=DIST_ROOT)
    print(f"Prepared GitHub Release assets in {destination}")
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("all", help="render and verify all five production scenes")
    scene_parser = subcommands.add_parser("scene", help="render one production scene")
    scene_parser.add_argument("scene_id")
    verify_parser = subcommands.add_parser("verify", help="verify an output family")
    verify_parser.add_argument("--target", choices=("horizontal", "vertical", "stories", "all"), default="horizontal")
    vertical_parser = subcommands.add_parser("vertical", help="render portrait animations and Stories")
    vertical_sub = vertical_parser.add_subparsers(dest="vertical_action", required=True)
    vertical_sub.add_parser("all")
    for action in ("scene", "stories", "story"):
        selection = vertical_sub.add_parser(action)
        selection.add_argument("identifier")
    package_parser = subcommands.add_parser("package", help="prepare low-resolution release assets")
    package_parser.add_argument("--tag", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "vertical":
            from scripts.vertical import render_selection
            render_selection(args.vertical_action, getattr(args, "identifier", None))
        elif args.command == "all":
            render_all()
        elif args.command == "scene":
            staging = _new_render_staging()
            work_root = staging / "work"
            output_root = staging / "videos"
            try:
                scene = _manifest_scene(args.scene_id)
                render_scene(scene, work_root, output_root)
                _verify_output_shape(output_root, scenes=[scene])
                _replace_directory(
                    output_root / scene["id"],
                    VIDEO_ROOT / scene["id"],
                    within=VIDEO_ROOT,
                )
            finally:
                _remove_tree(staging, within=MEDIA_ROOT)
            from scripts.provenance import record
            record(scene, VIDEO_ROOT)
            _clear_generated_side_outputs()
            verify_scene(scene)
        elif args.command == "verify":
            if args.target in ("horizontal", "all"):
                verify_all()
            from scripts.vertical import verify_family
            for family in ("vertical", "stories"):
                if args.target in (family, "all"):
                    verify_family(family)
        else:
            package_release(args.tag)
    except (ConfigurationError, FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
