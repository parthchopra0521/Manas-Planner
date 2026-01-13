from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


def _safe_pixmap(path: Path, *, height: int | None = None) -> QPixmap | None:
    if not path.exists():
        return None
    pix = QPixmap(str(path))
    if pix.isNull():
        return None
    if height is not None:
        pix = pix.scaledToHeight(height, Qt.TransformationMode.SmoothTransformation)
    return pix


class DroneStatusCard(QFrame):
    def __init__(
        self,
        name: str,
        status_text: str = "Status: Offline",
        image_path: Path | None = None,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        altitude_m: float | None = None,
        updated_text: str | None = None,
        # mode_text intentionally removed (no scan/spray functionality)
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("DroneStatusCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._name = name

        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        name_lbl.setObjectName("DroneName")

        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        img_lbl.setObjectName("DroneImage")
        img_lbl.setMinimumHeight(86)

        pix = _safe_pixmap(image_path, height=78) if image_path else None
        if pix is not None:
            img_lbl.setPixmap(pix)
        else:
            img_lbl.setText("[drone]")

        self.status_lbl = QLabel(status_text)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.status_lbl.setObjectName("DroneStatus")
        # Default to offline unless updated by backend.
        self.status_lbl.setProperty("live", False)

        # Info grid (Latitude/Longitude/Altitude/Updated)
        info = QFrame()
        info.setObjectName("InfoGrid")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.lat_card = self._make_kv_card(
            "Latitude", "--" if latitude is None else f"{latitude:.6f}"
        )
        self.lon_card = self._make_kv_card(
            "Longitude", "--" if longitude is None else f"{longitude:.6f}"
        )
        self.alt_card = self._make_kv_card(
            "Altitude", "--" if altitude_m is None else f"{altitude_m:.1f} m"
        )
        self.updated_card = self._make_kv_card("Updated", updated_text or "--")

        row1.addWidget(self.lat_card)
        row1.addWidget(self.lon_card)
        row2.addWidget(self.alt_card)
        row2.addWidget(self.updated_card)

        info_layout.addLayout(row1)
        info_layout.addLayout(row2)

        self.gps_lbl = QLabel("GPS: --")
        self.gps_lbl.setObjectName("GpsStatus")
        self.gps_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.gps_lbl.setProperty("gps", "unknown")

        layout.addWidget(name_lbl)
        layout.addWidget(img_lbl)
        layout.addWidget(self.status_lbl)
        layout.addWidget(info)
        layout.addWidget(self.gps_lbl)

    def _make_kv_card(self, key: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("KvCard")
        v = QVBoxLayout(card)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(2)

        k = QLabel(key)
        k.setObjectName("KvKey")
        val = QLabel(value)
        val.setObjectName("KvValue")
        val.setWordWrap(True)

        v.addWidget(k)
        v.addWidget(val)
        card._value_label = val  # type: ignore[attr-defined]
        return card

    def _set_kv_value(self, card: QFrame, value: str) -> None:
        lbl = getattr(card, "_value_label", None)
        if isinstance(lbl, QLabel):
            lbl.setText(value)

    def set_position(
        self,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        altitude_m: float | None = None,
        updated_text: str | None = None,
    ) -> None:
        if latitude is not None:
            self._set_kv_value(self.lat_card, f"{latitude:.6f}")
        if longitude is not None:
            self._set_kv_value(self.lon_card, f"{longitude:.6f}")
        if altitude_m is not None:
            self._set_kv_value(self.alt_card, f"{altitude_m:.1f} m")
        if updated_text is not None:
            self._set_kv_value(self.updated_card, updated_text)

    def set_gps_active(self, active: bool | None) -> None:
        if active is None:
            self.gps_lbl.setText("GPS: --")
            self.gps_lbl.setProperty("gps", "unknown")
        else:
            self.gps_lbl.setText("GPS: Active" if active else "GPS: Inactive")
            self.gps_lbl.setProperty("gps", "active" if active else "inactive")
        self.gps_lbl.style().unpolish(self.gps_lbl)
        self.gps_lbl.style().polish(self.gps_lbl)
        self.gps_lbl.update()

    def set_live(self, live: bool) -> None:
        # Text + an objectName used by QSS for coloring.
        self.status_lbl.setText("Status: Live" if live else "Status: Offline")
        self.status_lbl.setProperty("live", bool(live))
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)
        self.status_lbl.update()


class MissionPlannerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Manas Planner")
        self.resize(1200, 700)

        root = QWidget()
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = self._build_header()
        body = self._build_body()

        outer.addWidget(header)
        outer.addWidget(body)

        # Track last-known positions to infer "mode" from movement.
        # Shape: { "freyja": (lat, lon, alt_m), "cleo": (lat, lon, alt_m) }
        self._last_positions: dict[str, tuple[float, float, float]] = {}

        # GPS signal state per drone. Coordinates should update only while GPS is active.
        self._gps_active: dict[str, bool] = {"freyja": False, "cleo": False}

        self._apply_styles()

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(70)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(16)

        logo = QLabel()
        logo.setObjectName("Logo")
        logo.setFixedHeight(50)
        # Prefer the repo-provided logo if present; keep backwards-compatible fallbacks.
        logo_pix = (
            _safe_pixmap(ASSETS_DIR / "manas-full-white.png", height=50)
            or _safe_pixmap(ASSETS_DIR / "logo.png", height=50)
        )
        if logo_pix is not None:
            logo.setPixmap(logo_pix)
        else:
            logo.setText("PROJECT\nMANAS")
            logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            logo.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))

        self.global_status = QLabel("Status: Offline")
        self.global_status.setObjectName("GlobalStatus")
        self.global_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.global_status.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        # Default to offline unless updated by backend.
        self.global_status.setProperty("live", False)

        layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addWidget(self.global_status, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        return header

    def _build_body(self) -> QFrame:
        body = QFrame()
        body.setObjectName("Body")

        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Map placeholder
        map_frame = QFrame()
        map_frame.setObjectName("MapArea")
        map_layout = QVBoxLayout(map_frame)
        map_layout.setContentsMargins(16, 16, 16, 16)

        map_lbl = QLabel("Map")
        map_lbl.setObjectName("MapLabel")
        map_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        map_lbl.setFont(QFont("Sans Serif", 48, QFont.Weight.Bold))
        map_layout.addWidget(map_lbl)

        # Right sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(280)

        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(18, 18, 18, 18)
        sb.setSpacing(18)

        freyja_img = (
            ASSETS_DIR / "Freyja.png"
            if (ASSETS_DIR / "Freyja.png").exists()
            else ASSETS_DIR / "drone.png"
        )
        cleo_img = (
            ASSETS_DIR / "Cleo.png"
            if (ASSETS_DIR / "Cleo.png").exists()
            else ASSETS_DIR / "drone.png"
        )

        self.freyja_card = DroneStatusCard("Freyja", "Status: Offline", freyja_img)
        self.cleo_card = DroneStatusCard("Cleo", "Status: Offline", cleo_img)

        sb.addWidget(self.freyja_card)
        sb.addWidget(self.cleo_card)
        sb.addItem(QSpacerItem(20, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        btn_start_mission = QPushButton("Start Mission")
        btn_start_mission.setObjectName("PrimaryButton")

        kill_row = QHBoxLayout()
        kill_row.setSpacing(12)
        btn_kill_left = QPushButton("Kill Freyja")
        btn_kill_left.setObjectName("SmallButton")
        btn_kill_right = QPushButton("Kill Cleo")
        btn_kill_right.setObjectName("SmallButton")

        kill_row.addWidget(btn_kill_left)
        kill_row.addWidget(btn_kill_right)

        btn_start_mission.setMinimumHeight(56)

        sb.addWidget(btn_start_mission)
        sb.addLayout(kill_row)

        layout.addWidget(map_frame, 1)
        layout.addWidget(sidebar, 0)

        return body

    def set_global_live(self, live: bool) -> None:
        self.global_status.setText("Status: Live" if live else "Status: Offline")
        self.global_status.setProperty("live", bool(live))
        self.global_status.style().unpolish(self.global_status)
        self.global_status.style().polish(self.global_status)
        self.global_status.update()

    def set_drone_live(self, drone_name: str, live: bool) -> None:
        name = drone_name.strip().lower()
        if name == "freyja":
            self.freyja_card.set_live(live)
        elif name == "cleo":
            self.cleo_card.set_live(live)

    def update_drone_position(
        self,
        drone_name: str,
        *,
        latitude: float,
        longitude: float,
        altitude_m: float,
        updated_text: str | None = None,
    ) -> None:
        """Update the UI for a drone's coordinates.

                Contract:
                - Updates the Lat/Lon/Alt/Updated tiles for the named drone only when that drone's GPS is active.
        """
        name = drone_name.strip().lower()
        card: DroneStatusCard | None
        if name == "freyja":
            card = self.freyja_card
        elif name == "cleo":
            card = self.cleo_card
        else:
            return

        # Only change the coordinate tiles when GPS is active.
        if self._gps_active.get(name, False):
            card.set_position(
                latitude=latitude,
                longitude=longitude,
                altitude_m=altitude_m,
                updated_text=updated_text,
            )

        prev = self._last_positions.get(name)
        curr = (float(latitude), float(longitude), float(altitude_m))
        moved = prev is None or any(abs(a - b) > 1e-9 for a, b in zip(prev, curr))
        _ = moved  # kept for potential future use (e.g. highlighting a moving drone)
        self._last_positions[name] = curr

    def set_drone_gps_active(self, drone_name: str, active: bool) -> None:
        name = drone_name.strip().lower()
        if name not in ("freyja", "cleo"):
            return
        self._gps_active[name] = bool(active)
        if name == "freyja":
            self.freyja_card.set_gps_active(active)
        elif name == "cleo":
            self.cleo_card.set_gps_active(active)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            /*
              Theme: black surfaces + #f49221 accents
              - Keep contrast high, avoid flat gray blocks
              - Use orange borders to match the reference screenshot
            */
            QMainWindow { background: #070707; }

            #Header {
                background: #070707;
                border-bottom: 2px solid #f49221;
            }
            #GlobalStatus { color: #eaeaea; }
            #GlobalStatus[live="true"] { color: #69e36b; }
            #GlobalStatus[live="false"] { color: #ff5c5c; }
            #Logo { color: #eaeaea; }

            #Body { background: #070707; }

            #MapArea {
                background: #0d0d0d;
                border-right: 2px solid rgba(244, 146, 33, 0.55);
            }
            #MapLabel { color: rgba(244, 146, 33, 0.85); }

            #Sidebar {
                background: #070707;
            }

            /* Drone card: orange outline + dark panel */
            #DroneStatusCard {
                background: #0e0e0e;
                border: 2px solid #f49221;
                border-radius: 14px;
                padding: 12px;
            }

            #DroneName {
                color: #f4f4f4;
                font-size: 20px;
                font-weight: 700;
            }

            #DroneImage { color: #f2f2f2; }

            /* Status badge (pill) */
            #DroneStatus {
                color: #cfcfcf;
                font-size: 14px;
                padding: 6px 10px;
                border-radius: 10px;
                background: #121212;
                border: 1px solid rgba(244, 146, 33, 0.45);
            }

            /* Info grid */
            #InfoGrid { background: transparent; }

            #KvCard {
                background: #121212;
                border-radius: 10px;
                border: 1px solid rgba(244, 146, 33, 0.22);
            }

            #KvKey {
                color: rgba(244, 146, 33, 0.85);
                font-size: 11px;
                font-weight: 700;
            }

            #KvValue {
                color: #e6e6e6;
                font-size: 13px;
                font-weight: 700;
            }

            #DroneMode {
                color: rgba(244, 146, 33, 0.95);
                font-size: 13px;
                font-weight: 800;
                padding-top: 2px;
            }

            #GpsStatus {
                color: #bdbdbd;
                font-size: 12px;
                font-weight: 700;
                padding: 4px 8px;
                border-radius: 10px;
                background: #111111;
                border: 1px solid rgba(244, 146, 33, 0.20);
            }
            #GpsStatus[gps="active"] {
                color: #69e36b;
                background: rgba(105, 227, 107, 0.10);
                border: 1px solid rgba(105, 227, 107, 0.55);
            }
            #GpsStatus[gps="inactive"] {
                color: #ff5c5c;
                background: rgba(255, 92, 92, 0.10);
                border: 1px solid rgba(255, 92, 92, 0.55);
            }

            #DroneStatus[live="true"] {
                color: #69e36b;
                background: rgba(105, 227, 107, 0.10);
                border: 1px solid rgba(105, 227, 107, 0.55);
            }

            #DroneStatus[live="false"] {
                color: #ff5c5c;
                background: rgba(255, 92, 92, 0.10);
                border: 1px solid rgba(255, 92, 92, 0.55);
            }

            QPushButton#PrimaryButton,
            QPushButton#SmallButton {
                background: #f49221;
                color: #0b0b0b;
                border: 1px solid rgba(244, 146, 33, 0.85);
                border-radius: 12px;
                font-weight: 700;
                letter-spacing: 0.2px;
            }

            QPushButton#PrimaryButton {
                font-size: 16px;
                padding: 14px 14px;
            }

            QPushButton#SmallButton {
                font-size: 14px;
                padding: 10px 12px;
                min-height: 40px;
            }

            QPushButton#PrimaryButton:hover,
            QPushButton#SmallButton:hover {
                background: #ffad55;
                border: 1px solid rgba(244, 146, 33, 1.0);
            }

            QPushButton#PrimaryButton:pressed,
            QPushButton#SmallButton:pressed {
                background: #d97813;
                border: 1px solid rgba(244, 146, 33, 0.95);
            }

            QPushButton#PrimaryButton:focus,
            QPushButton#SmallButton:focus {
                outline: none;
                border: 2px solid rgba(244, 146, 33, 0.95);
            }
            """
        )
