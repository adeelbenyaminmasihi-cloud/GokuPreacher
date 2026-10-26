            "afade=t=out:st=0.12:d=0.16,volume=0.8",
            0.28,
        ),
        "alert": (
            "aevalsrc=0.22*sin(2*PI*720*t)*(lt(mod(t\\,0.5)\\,0.20))+0.12*sin(2*PI*460*t)*(gte(mod(t\\,0.5)\\,0.20)):s=44100:d=0.62",
            "afade=t=out:st=0.38:d=0.22,volume=0.7",
            0.62,
        ),
        "zap": (
            "anoisesrc=color=white:sample_rate=44100:duration=0.38",
            "highpass=f=1200,lowpass=f=8500,afade=t=in:st=0:d=0.01,afade=t=out:st=0.06:d=0.32,volume=0.32",
            0.38,
        ),
        "engine": (
            "anoisesrc=color=pink:sample_rate=44100:duration=0.65",
            "lowpass=f=180,highpass=f=45,afade=t=in:st=0:d=0.08,afade=t=out:st=0.24:d=0.4,volume=0.7",
            0.65,
        ),
        "ding": (
            "aevalsrc=0.24*sin(2*PI*1046*t)*exp(-5*t)+0.16*sin(2*PI*1568*t)*exp(-7*t):s=44100:d=0.55",
            "afade=t=out:st=0.28:d=0.27,volume=0.62",
            0.55,
        ),
        "boing": (
            "aevalsrc=0.42*sin(2*PI*(250*t-70*t*t))*exp(-4.5*t):s=44100:d=0.65",
            "afade=t=out:st=0.38:d=0.27,volume=0.7",
            0.65,
        ),
        "click": (
            "anoisesrc=color=white:sample_rate=44100:duration=0.12",
            "highpass=f=1800,lowpass=f=7000,afade=t=out:st=0.015:d=0.105,volume=0.28",
            0.12,
        ),
        "scratch": (
            "anoisesrc=color=white:sample_rate=44100:duration=0.42",
            "highpass=f=500,lowpass=f=4200,afade=t=in:st=0:d=0.02,afade=t=out:st=0.09:d=0.3,volume=0.32",
            0.42,
        ),
    }
    if sfx_type not in source_and_filter:
        return None
    source, afilter, duration = source_and_filter[sfx_type]
    try:
        run_ffmpeg([
            "-f", "lavfi", "-i", source,
            "-af", afilter,
            "-t", str(duration), "-ar", "44100", "-ac", "2",
            "-c:a", "pcm_s16le", str(out_path),
        ])
        return out_path if out_path.exists() and out_path.stat().st_size > 1000 else None
    except Exception as exc:
        print(f"   ⚠️ Could not synthesize '{sfx_type}' sound effect: {exc}")
        return None


def infer_sfx(narration: str) -> str:
    text = narration.lower()
    if any(word in text for word in ("پیسے", "روپے", "رقم", "خرید", "پارسل", "بل", "خرچہ", "اکاؤنٹ")):
        return "cash"
    if any(word in text for word in ("فون", "موبائل", "کال", "میسج", "او ٹی پی", "پاس ورڈ")):
        return "alert"
    if any(word in text for word in ("گاڑی", "انجن", "بائیک", "موٹر", "ٹائر")):
        return "engine"
    if any(word in text for word in ("گرمی", "چارج", "سولر", "بجلی", "روشنی")):
        return "zap"
    if any(word in text for word in ("غلط", "افواہ", "چور", "فراڈ", "اسکیم", "اسکیم")):
        return "scratch"
    return random.choice(["whoosh", "pop", "ding", "boing"])


def _sfx_delay(scene: Dict[str, Any], duration: float) -> float:
    point = str(scene.get("sfx_at", "middle")).lower()
    if point == "start":
        return min(0.18, duration * 0.05)
    if point == "end":
        return max(0.0, duration - 0.9)
    return max(0.15, min(duration * 0.52, duration - 0.65))


def mix_scene_voice_and_sfx(
    voice_path: Path,
    sfx_type: str,
    delay_sec: float,
    out_audio: Path,
    workdir: Path,
    scene_index: int,
) -> Path:
    effect = _make_sfx(sfx_type, workdir / f"sfx_{scene_index:02d}.wav")
    if effect is None:
        shutil.copy2(voice_path, out_audio)
        return out_audio
    delay_ms = max(0, int(delay_sec * 1000))
    try:
        run_ffmpeg([
            "-i", str(voice_path), "-i", str(effect),
            "-filter_complex",
            f"[1:a]volume=0.22,adelay={delay_ms}|{delay_ms}[fx];"
            "[0:a][fx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
            "alimiter=limit=0.95[a]",
            "-map", "[a]", "-ar", "44100", "-ac", "2",
            "-c:a", "aac", "-b:a", "160k", str(out_audio),
        ])
        return out_audio
    except Exception as exc:
        print(f"   ⚠️ Sound effect mix failed for scene {scene_index + 1}: {exc}; keeping clean voiceover.")
        shutil.copy2(voice_path, out_audio)
        return out_audio


def render_scene(scene: Dict[str, Any], index: int, total_scenes: int, script_data: Dict[str, Any], workdir: Path) -> Path:
    narration = scene["tts_urdu"]
    print(f"🎙️ Scene {index + 1}/{total_scenes}: {narration[:52]}{'…' if len(narration) > 52 else ''}")
    raw_voice, metadata = synthesize_scene_voice(narration, index, workdir)

    # Light mastering without silence removal, so Edge TTS word timestamps stay aligned.
    mastered_voice = workdir / f"voice_master_{index:02d}.m4a"
    run_ffmpeg([
        "-i", str(raw_voice),
        "-af", "highpass=f=65,acompressor=threshold=-18dB:ratio=2.4:attack=8:release=90:makeup=2dB,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k", str(mastered_voice),
    ])
    duration = get_audio_duration(mastered_voice)
    sub_path = workdir / f"subtitles_{index:02d}.ass"
    create_timed_subtitles(metadata, narration, duration, sub_path)

    queries = scene.get("visual_queries") or [script_data["topic"], script_data["topic"] + " close up"]
    if len(queries) < 2:
        queries = list(queries) + [str(queries[0]) + " detail close up"]
    query_video = str(scene.get("video_query") or queries[0]).strip()
    video_path = fetch_contextual_stock_video(query_video, workdir / f"stock_{index:02d}.mp4")
    if video_path:
        first_media, first_is_video = video_path, True
    else:
        first_media = fetch_exact_scene_photo(str(queries[0]), workdir / f"photo_{index:02d}_a.jpg")
        first_is_video = False
    second_media = fetch_exact_scene_photo(str(queries[1]), workdir / f"photo_{index:02d}_b.jpg")

    # Keep the visual cuts on exact frame boundaries; the combined video is a hair longer
    # than the audio so the last subtitle is never clipped by frame rounding.
    total_frames = max(6, int(math.ceil(duration * FPS)))
    first_frames = max(1, int(round(total_frames * 0.53)))
    second_frames = max(1, total_frames - first_frames)
    if first_frames + second_frames > total_frames:
        second_frames = total_frames - first_frames
    cut_specs = [
        (first_media, first_is_video, first_frames / FPS, "a"),
        (second_media, False, second_frames / FPS, "b"),
    ]
    clip_paths: List[Path] = []
    for media, is_video, cut_duration, suffix in cut_specs:
        brand_overlay = create_brand_overlay(
            script_data.get("category_badge", "FUN KNOWLEDGE"), index, total_scenes,
            workdir / f"brand_{index:02d}_{suffix}.png",
        )
        clip = workdir / f"visual_{index:02d}_{suffix}.mp4"
        prepare_visual_subclip(media, is_video, brand_overlay, cut_duration, clip)
        clip_paths.append(clip)

    visual_list = workdir / f"visual_list_{index:02d}.txt"
    with visual_list.open("w", encoding="utf-8") as handle:
