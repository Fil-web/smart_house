from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(command))
    return subprocess.run(command, check=check, text=True, capture_output=True)


def require(command: str) -> None:
    if shutil.which(command) is None:
        raise SystemExit(f"Command not found: {command}")


def bluetoothctl(*commands: str, check: bool = True) -> str:
    require("bluetoothctl")
    print("+ bluetoothctl")
    result = subprocess.run(
        ["bluetoothctl"],
        input="\n".join(commands) + "\n",
        check=check,
        text=True,
        capture_output=True,
    )
    output = result.stdout.strip()
    if output:
        print(output)
    error = result.stderr.strip()
    if error:
        print(error)
    return output


def scan(seconds: int) -> None:
    require("timeout")
    require("bluetoothctl")
    print("Put Alice/Yandex Station into Bluetooth pairing mode first.")
    result = subprocess.run(
        ["timeout", str(seconds), "bluetoothctl"],
        input="scan on\n",
        text=True,
        capture_output=True,
        check=False,
    )
    print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    print("\nLook for a device named Yandex, Station, Alice, or the name shown in the Yandex app.")


def pair(address: str) -> None:
    bluetoothctl("power on")
    bluetoothctl("agent on")
    bluetoothctl("default-agent")
    bluetoothctl(f"pair {address}", check=False)
    bluetoothctl(f"trust {address}", check=False)
    bluetoothctl(f"connect {address}", check=False)


def connect(address: str) -> None:
    bluetoothctl("power on")
    bluetoothctl(f"trust {address}", check=False)
    bluetoothctl(f"connect {address}", check=False)


def status() -> None:
    bluetoothctl("show", "devices", check=False)


def make_tone(path: Path, seconds: float = 1.5, frequency: int = 880) -> None:
    sample_rate = 44_100
    amplitude = 18_000
    frames = int(sample_rate * seconds)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for index in range(frames):
            value = int(amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
            wav.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))


def test_sound() -> None:
    players = [
        ["paplay"],
        ["pw-play"],
        ["aplay"],
    ]
    player = next((candidate for candidate in players if shutil.which(candidate[0])), None)
    if player is None:
        raise SystemExit("No audio player found. Install one: sudo apt install -y alsa-utils pulseaudio-utils")

    with tempfile.TemporaryDirectory() as temp_dir:
        tone = Path(temp_dir) / "alice-test-tone.wav"
        make_tone(tone)
        run([*player, str(tone)], check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pair and test a Yandex Alice speaker over Bluetooth.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    scan_parser = subcommands.add_parser("scan", help="Scan Bluetooth devices")
    scan_parser.add_argument("--seconds", type=int, default=20)

    pair_parser = subcommands.add_parser("pair", help="Pair, trust, and connect by MAC address")
    pair_parser.add_argument("address")

    connect_parser = subcommands.add_parser("connect", help="Connect an already paired speaker")
    connect_parser.add_argument("address")

    subcommands.add_parser("status", help="Show adapter and known devices")
    subcommands.add_parser("test", help="Play a short test tone")

    args = parser.parse_args()
    if args.command == "scan":
        scan(args.seconds)
    elif args.command == "pair":
        pair(args.address)
    elif args.command == "connect":
        connect(args.address)
    elif args.command == "status":
        status()
    elif args.command == "test":
        test_sound()


if __name__ == "__main__":
    main()
