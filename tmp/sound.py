"""Sound playback helpers with simple cross-platform fallbacks."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading

from core.logger import activity_log


class SoundPlayer:
    """Play local files or stream URLs using the first available backend."""

    def __init__(self) -> None:
        self.players = ["ffplay", "mpg123", "cvlc", "mpv"]
        self.file_processes: list[subprocess.Popen] = []
        self.radio_processes: list[subprocess.Popen] = []
        self._fallback_stop = threading.Event()
        self._fallback_thread: threading.Thread | None = None

    def play(self, source: str | None, volume: int = 100, radio: bool = False, loop: bool = False) -> None:
        if radio:
            if source:
                self._play_radio(source, volume)
            else:
                self._fallback_ring(loop)
            return

        if not source or not os.path.exists(source):
            self._fallback_ring(loop)
            return

        if os.name == "nt" and source.lower().endswith(".wav"):
            try:
                import winsound

                flags = winsound.SND_ASYNC | winsound.SND_FILENAME
                if loop:
                    flags |= winsound.SND_LOOP
                winsound.PlaySound(source, flags)
                return
            except Exception as exc:
                activity_log.log("winsound_failed", "", str(exc))

        for backend in self.players:
            if shutil.which(backend):
                cmd = self._build_file_cmd(backend, source, volume, loop)
                if not cmd:
                    continue
                try:
                    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.file_processes.append(proc)
                    return
                except Exception as exc:
                    activity_log.log("player_start_failed", backend, str(exc))
                    continue

        if os.name == "nt":
            try:
                os.startfile(source)  # type: ignore[attr-defined]
                return
            except Exception as exc:
                activity_log.log("os_startfile_failed", "", str(exc))

        self._fallback_ring(loop)

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
            loop_arg = "--loop" if loop else "--no-loop"
            return ["cvlc", "--play-and-exit", loop_arg, "--volume", str(int(volume * 2.56)), source, "vlc://quit"]
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
            except Exception as exc:
                activity_log.log("radio_play_failed", url, str(exc))
        self._fallback_beep()

    def stop_radio(self) -> None:
        self.stop()

    def stop(self) -> None:
        self._fallback_stop.set()
        self._fallback_thread = None
        if os.name == "nt":
            try:
                import winsound
                winsound.PlaySound(None, 0)
            except Exception as exc:
                activity_log.log("winsound_stop_failed", "", str(exc))
        for proc in self.file_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception as exc:
                activity_log.log("terminate_file_failed", "", str(exc))
        self.file_processes.clear()
        for proc in self.radio_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception as exc:
                activity_log.log("terminate_radio_failed", "", str(exc))
        self.radio_processes.clear()

    def _fallback_ring(self, loop: bool = False) -> None:
        if not loop:
            self._fallback_beep()
            return

        self._fallback_stop.set()
        self._fallback_stop = threading.Event()

        def _ring() -> None:
            while not self._fallback_stop.is_set():
                self._fallback_beep()
                self._fallback_stop.wait(1.0)

        self._fallback_thread = threading.Thread(target=_ring, daemon=True)
        self._fallback_thread.start()

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
    