"""Sound playback helpers with simple cross-platform fallbacks."""

from __future__ import annotations

import os
import shutil
import subprocess


class SoundPlayer:
    """Play local files or stream URLs using the first available backend."""

    def __init__(self) -> None:
        self.players = ["ffplay", "mpg123", "cvlc", "mpv"]
        self.radio_processes: list[subprocess.Popen] = []

    def play(self, source: str | None, volume: int = 100, radio: bool = False, loop: bool = False) -> None:
        if radio:
            if source:
                self._play_radio(source, volume)
            else:
                self._fallback_beep()
            return

        if not source or not os.path.exists(source):
            self._fallback_beep()
            return

        if os.name == "nt" and source.lower().endswith(".wav"):
            try:
                import winsound

                flags = winsound.SND_ASYNC | winsound.SND_FILENAME
                if loop:
                    flags |= winsound.SND_LOOP
                winsound.PlaySound(source, flags)
                return
            except Exception:
                pass

        for backend in self.players:
            if shutil.which(backend):
                cmd = self._build_file_cmd(backend, source, volume, loop)
                if not cmd:
                    continue
                try:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except Exception:
                    continue

        if os.name == "nt":
            try:
                os.startfile(source)  # type: ignore[attr-defined]
                return
            except Exception:
                pass

        self._fallback_beep()

    def _build_file_cmd(self, backend: str, source: str, volume: int, loop: bool) -> list[str] | None:
        if backend == "ffplay":
            return [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loop",
                "0" if loop else "1",
                "-volume",
                str(volume),
                source,
            ]
        if backend == "mpg123":
            return ["mpg123", "-q", "-f", str(volume * 10), "--loop", "-1" if loop else "1", source]
        if backend == "cvlc":
            return ["cvlc", "--play-and-exit", "--no-loop", "--volume", str(int(volume * 2.56)), source, "vlc://quit"]
        if backend == "mpv":
            return ["mpv", "--no-terminal", "--volume", str(volume), "--loop-file", "inf" if loop else "no", source]
        return None

    def _play_radio(self, url: str, volume: int) -> None:
        if shutil.which("cvlc"):
            cmd = ["cvlc", url, "--volume", str(int(volume * 2.56)), "--intf", "dummy"]
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.radio_processes.append(proc)
                return
            except Exception:
                pass
        self._fallback_beep()

    def stop_radio(self) -> None:
        if os.name == "nt":
            try:
                import winsound

                winsound.PlaySound(None, 0)
            except Exception:
                pass
        for proc in self.radio_processes:
            try:
                proc.terminate()
            except Exception:
                pass
        self.radio_processes.clear()

    def _fallback_beep(self) -> None:
        if os.name == "nt":
            try:
                import winsound

                winsound.MessageBeep()
                return
            except Exception:
                pass
        print("\a", end="", flush=True)


player = SoundPlayer()


def metronome_tick() -> None:
    """Play a short tick sound using the host's simplest available option."""

    if os.name == "nt":
        try:
            import winsound

            winsound.Beep(1200, 120)
            return
        except Exception:
            pass

    linux_tick = "/usr/share/sounds/alsa/Front_Center.wav"
    if os.path.exists(linux_tick) and shutil.which("aplay"):
        try:
            subprocess.run(["aplay", linux_tick], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return
        except Exception:
            pass

    print("\a", end="", flush=True)
