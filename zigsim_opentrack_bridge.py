#!/usr/bin/env python3
"""ZIG SIM -> OpenTrack bridge (standard-library only).

Safe dependencies:
  * ZIG SIM from Apple's App Store
  * Python 3 from python.org or Microsoft Store
  * OpenTrack from github.com/opentrack/opentrack

ZIG SIM sends a quaternion in a UDP/JSON packet.  This bridge recentres the
quaternion, converts it to camera yaw/pitch/roll, and sends the six little-
endian doubles expected by OpenTrack's "UDP over network" input.

Controls while running:
  Enter  - recenter using the next valid packet
  q Enter - quit
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import struct
import sys
import threading
from typing import Any, Iterable


Quaternion = tuple[float, float, float, float]  # x, y, z, w
Vector = tuple[float, float, float]
Matrix = tuple[Vector, Vector, Vector]


def normalize(q: Quaternion) -> Quaternion:
    length = math.sqrt(sum(value * value for value in q))
    if length < 1e-12:
        raise ValueError("zero-length quaternion")
    return tuple(value / length for value in q)  # type: ignore[return-value]


def conjugate(q: Quaternion) -> Quaternion:
    x, y, z, w = q
    return -x, -y, -z, w


def multiply(a: Quaternion, b: Quaternion) -> Quaternion:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def quaternion_to_matrix(q: Quaternion) -> Matrix:
    x, y, z, w = normalize(q)
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def transpose(m: Matrix) -> Matrix:
    return tuple(tuple(m[row][column] for row in range(3)) for column in range(3))  # type: ignore[return-value]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    return tuple(
        tuple(sum(a[row][k] * b[k][column] for k in range(3)) for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def camera_basis(orientation: str) -> Matrix:
    """Return camera right/up/forward axes as columns in iPhone coordinates."""
    axes: dict[str, tuple[Vector, Vector, Vector]] = {
        # Back camera points along -Z in Apple's device coordinate system.
        "portrait": ((1, 0, 0), (0, 1, 0), (0, 0, -1)),
        "portrait-upside-down": ((-1, 0, 0), (0, -1, 0), (0, 0, -1)),
        "landscape-left": ((0, 1, 0), (-1, 0, 0), (0, 0, -1)),
        "landscape-right": ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
    }
    right, up, forward = axes[orientation]
    return (
        (right[0], up[0], forward[0]),
        (right[1], up[1], forward[1]),
        (right[2], up[2], forward[2]),
    )


def matrix_to_ypr(m: Matrix) -> tuple[float, float, float]:
    """Extract yaw(Y), pitch(X), roll(Z) in degrees from Ry * Rx * Rz."""
    pitch = math.asin(max(-1.0, min(1.0, -m[1][2])))
    cp = math.cos(pitch)
    if abs(cp) > 1e-7:
        yaw = math.atan2(m[0][2], m[2][2])
        roll = math.atan2(m[1][0], m[1][1])
    else:
        yaw = math.atan2(-m[2][0], m[0][0])
        roll = 0.0
    return tuple(math.degrees(angle) for angle in (yaw, pitch, roll))  # type: ignore[return-value]


def nested_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nested_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_dicts(child)


def read_quaternion(payload: Any) -> Quaternion | None:
    """Accept current and older ZIG SIM JSON layouts."""
    for obj in nested_dicts(payload):
        for key, value in obj.items():
            if "quaternion" not in str(key).lower():
                continue
            if isinstance(value, dict):
                lowered = {str(k).lower(): v for k, v in value.items()}
                if all(axis in lowered for axis in "xyzw"):
                    return normalize(tuple(float(lowered[axis]) for axis in "xyzw"))  # type: ignore[arg-type]
            if isinstance(value, (list, tuple)) and len(value) >= 4:
                return normalize(tuple(float(value[index]) for index in range(4)))  # type: ignore[arg-type]
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Receive ZIG SIM quaternion JSON and forward it to OpenTrack."
    )
    parser.add_argument("--listen-port", type=int, default=50000,
                        help="UDP port entered in ZIG SIM (default: 50000)")
    parser.add_argument("--opentrack-port", type=int, default=4242,
                        help="OpenTrack UDP input port (default: 4242)")
    parser.add_argument("--orientation", default="landscape-left",
                        choices=("portrait", "portrait-upside-down", "landscape-left", "landscape-right"),
                        help="How the iPhone is held (default: landscape-left)")
    parser.add_argument("--yaw-sign", type=float, default=-1.0, choices=(-1.0, 1.0))
    parser.add_argument("--pitch-sign", type=float, default=-1.0, choices=(-1.0, 1.0))
    parser.add_argument("--roll-sign", type=float, default=1.0, choices=(-1.0, 1.0))
    parser.add_argument("--debug", action="store_true",
                        help="Print decoded angles about five times per second")
    return parser.parse_args()


def console_worker(state: dict[str, bool]) -> None:
    while state["running"]:
        try:
            command = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if command == "q":
            state["running"] = False
            return
        state["recenter"] = True
        print("Recenter requested; hold the phone still in its neutral position.")


def main() -> int:
    args = parse_args()
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receiver.bind(("0.0.0.0", args.listen_port))
    receiver.settimeout(0.25)

    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    destination = ("127.0.0.1", args.opentrack_port)
    basis = camera_basis(args.orientation)
    basis_t = transpose(basis)

    state = {"running": True, "recenter": True}
    threading.Thread(target=console_worker, args=(state,), daemon=True).start()

    reference: Quaternion | None = None
    packets = 0
    valid = 0
    last_debug_second = -1

    print(f"Listening for ZIG SIM JSON on UDP 0.0.0.0:{args.listen_port}")
    print(f"Sending OpenTrack packets to {destination[0]}:{destination[1]}")
    print(f"Phone orientation: {args.orientation}")
    print("Press Enter to recenter; type q and press Enter to quit.")

    try:
        while state["running"]:
            try:
                raw, source = receiver.recvfrom(65535)
            except socket.timeout:
                continue
            packets += 1

            try:
                payload = json.loads(raw.decode("utf-8-sig"))
                current = read_quaternion(payload)
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                current = None

            if current is None:
                if packets == 1 or packets % 100 == 0:
                    print("Packets arrive, but no quaternion was found. "
                          "In ZIG SIM enable QUATERNION and select JSON, not OSC.")
                continue

            valid += 1
            if reference is None or state["recenter"]:
                reference = current
                state["recenter"] = False
                print(f"Centered from {source[0]} after {valid} valid packet(s).")

            # Rotation relative to the calibrated phone pose.
            relative = normalize(multiply(conjugate(reference), current))
            device_matrix = quaternion_to_matrix(relative)
            camera_matrix = matmul(matmul(basis_t, device_matrix), basis)
            yaw, pitch, roll = matrix_to_ypr(camera_matrix)
            yaw *= args.yaw_sign
            pitch *= args.pitch_sign
            roll *= args.roll_sign

            # OpenTrack input order: X, Y, Z (cm), Yaw, Pitch, Roll (degrees).
            packet = struct.pack("<6d", 0.0, 0.0, 0.0, yaw, pitch, roll)
            sender.sendto(packet, destination)

            if args.debug:
                tick = int(valid / 12)
                if tick != last_debug_second:
                    last_debug_second = tick
                    print(f"Yaw {yaw:7.2f}  Pitch {pitch:7.2f}  Roll {roll:7.2f}")
    except KeyboardInterrupt:
        pass
    finally:
        receiver.close()
        sender.close()

    print("Bridge stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
