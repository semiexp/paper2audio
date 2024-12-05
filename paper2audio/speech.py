from voicevox_core import AccelerationMode, VoicevoxCore


def synthesize(
    text: str,
    speaker_id: int = 3,  # ずんだもんノーマル
) -> bytes:
    core = VoicevoxCore(
        acceleration_mode=AccelerationMode.AUTO,
        open_jtalk_dict_dir="./open_jtalk_dic_utf_8-1.11",
    )
    core.load_model(speaker_id)

    audio_query = core.audio_query(text, speaker_id)
    wav = core.synthesis(audio_query, speaker_id)

    return wav


def main() -> None:
    wav = synthesize("これはテストなのだ。")
    with open("output.wav", "wb") as f:
        f.write(wav)


if __name__ == "__main__":
    main()
