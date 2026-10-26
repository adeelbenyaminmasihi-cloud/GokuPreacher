        raise RuntimeError(f"Rendered scene {index + 1} is not a valid video.")
    return scene_out

# ----------------------------- Final render, music, Telegram -----------------------------


def build_full_video(script_data: Dict[str, Any], workdir: Path) -> Path:
    scene_files: List[Path] = []
    total = len(script_data["scenes"])
    for index, scene in enumerate(script_data["scenes"]):
        scene_file = render_scene(scene, index, total, script_data, workdir)
        scene_files.append(scene_file)

    concat_list = workdir / "master_concat.txt"
    with concat_list.open("w", encoding="utf-8") as handle:
        for path in scene_files:
            safe_path = path.as_posix().replace("'", "'\\''")
            handle.write(f"file '{safe_path}'\n")

    raw_output = workdir / "final_without_music.mp4"
    run_ffmpeg([
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(raw_output),
    ])

    bgm = BGM_PATH.resolve()
    if bgm.exists() and bgm.is_file():
        print("🎵 Mixing optional background music under the voiceover...")
        final_output = workdir / "final_with_music.mp4"
        try:
            run_ffmpeg([
                "-i", str(raw_output), "-stream_loop", "-1", "-i", str(bgm),
                "-filter_complex", "[1:a]volume=0.055[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.95[a]",
                "-map", "0:v:0", "-map", "[a]", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final_output),
            ])
            return final_output
        except Exception as exc:
            print(f"⚠️ Background music skipped: {exc}")

    print("ℹ️ No BGM_PATH file found; keeping voiceover and scene-matched sound effects only.")
    return raw_output


def send_to_telegram(video_path: Path, script_data: Dict[str, Any]) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ℹ️ Telegram upload skipped: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    caption = (
        f"🔥 {script_data.get('title', 'Urdu Reel')}\n\n"
        f"{script_data.get('hashtags', '#PakistaniReels #UrduFacts')}\n\n"
        "✅ Word-timed Urdu subtitles • Scene-matched visuals • Script-matched sound effects"
    )[:1024]
    try:
        with video_path.open("rb") as handle:
            response = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                files={"video": (video_path.name, handle, "video/mp4")},
                timeout=180,
            )
        response.raise_for_status()
        result = response.json()
        if result.get("ok"):
            print("✅ Reel uploaded to Telegram successfully.")
        else:
            print(f"⚠️ Telegram returned an unsuccessful response: {result}")
    except Exception as exc:
        print(f"⚠️ Telegram upload failed, but the video has been saved: {exc}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    script_data = generate_script_data()
    print(f"\n🎬 Title: {script_data['title']}")
    print(f"📚 Topic: {script_data['topic']}")
    print(f"🎞️ Scenes: {len(script_data['scenes'])}\n")

    run_id = time.strftime("%Y%m%d_%H%M%S")
    workdir = Path(tempfile.mkdtemp(prefix=f"reel_{run_id}_"))
    try:
        rendered = build_full_video(script_data, workdir)
        safe_title = re.sub(r"[^A-Za-z0-9_-]+", "_", script_data.get("topic", "urdu_reel"))[:48].strip("_") or "urdu_reel"
        destination = OUTPUT_DIR / f"{run_id}_{safe_title}.mp4"
        shutil.copy2(rendered, destination)
        print(f"\n✅ Video ready: {destination}")
        print(f"📦 File size: {destination.stat().st_size / (1024 * 1024):.1f} MB")
        send_to_telegram(destination, script_data)
    except Exception as exc:
        print(f"\n❌ Video build failed: {exc}")
        raise
    finally:
        # Keep the finished MP4 in OUTPUT_DIR; remove intermediate files to save disk space.
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
