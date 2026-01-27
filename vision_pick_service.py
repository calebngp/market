import os
import threading
import time
import uuid
from collections import deque

def _ms_now() -> int:
    return int(time.time() * 1000)


class VisionPickService:
    def __init__(
        self,
        camera_id: str = "cam_01",
        estante_id: str = "est_01",
        roi_id: str = "roi_01",
        max_events: int = 500,
    ):
        self.camera_id = camera_id
        self.estante_id = estante_id
        self.roi_id = roi_id

        self._lock = threading.Lock()
        self._events = deque(maxlen=max_events)

        self._thread: threading.Thread | None = None
        self._stop_evt = threading.Event()
        self._running = False
        self._last_error: str | None = None
        self._last_heartbeat_ms: int | None = None

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "camera_id": self.camera_id,
                "estante_id": self.estante_id,
                "roi_id": self.roi_id,
                "queued_events": len(self._events),
                "last_error": self._last_error,
                "last_heartbeat_ms": self._last_heartbeat_ms,
            }

    def pop_events(self, limit: int = 50) -> list[dict]:
        if limit <= 0:
            return []
        with self._lock:
            out = []
            for _ in range(min(limit, len(self._events))):
                out.append(self._events.popleft())
            return out

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._stop_evt.clear()
            self._running = True
            self._last_error = None

        t = threading.Thread(target=self._run_loop, name="VisionPickService", daemon=True)
        self._thread = t
        t.start()

    def stop(self, timeout_s: float = 2.0) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False
        self._stop_evt.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout_s)

    def _emit_event(self, payload: dict) -> None:
        with self._lock:
            self._events.append(payload)

    def _run_loop(self) -> None:
        try:
            self._run_loop_impl()
        except Exception as e:  # noqa: BLE001
            with self._lock:
                self._last_error = f"{type(e).__name__}: {e}"
                self._running = False
        finally:
            with self._lock:
                self._running = False

    def _run_loop_impl(self) -> None:
        source = os.environ.get("PICK_CAM_SOURCE", "0")
        fps = float(os.environ.get("PICK_FPS", "30"))
        hb_period_s = float(os.environ.get("PICK_HEARTBEAT_S", "2.0"))

        try:
            import cv2  # type: ignore
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                "Falta OpenCV (cv2). Instalá opencv-python y configurá PICK_CAM_SOURCE."
            ) from e

        cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
        if not cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara/source: {source}")

        dt_target = 1.0 / max(fps, 1.0)
        last_hb = time.time()
        last_fake_pick = time.time()

        try:
            while not self._stop_evt.is_set():
                t0 = time.time()

                ok, frame = cap.read()
                if not ok or frame is None:
                    time.sleep(0.05)
                    continue

                now = time.time()
                if (now - last_hb) >= hb_period_s:
                    with self._lock:
                        self._last_heartbeat_ms = _ms_now()
                    last_hb = now

                demo = os.environ.get("PICK_DEMO", "1") == "1"
                if demo and (now - last_fake_pick) >= 8.0:
                    last_fake_pick = now
                    evt = {
                        "event_type": "PICK",
                        "event_id": str(uuid.uuid4()),
                        "timestamp_ms": _ms_now(),
                        "camera_id": self.camera_id,
                        "estante_id": self.estante_id,
                        "roi_id": self.roi_id,
                        "sku_id": os.environ.get("PICK_DEMO_SKU", "SKU_DEMO"),
                        "track_id": int(os.environ.get("PICK_DEMO_TRACK", "1")),
                        "confidence": 0.5,
                        "confirmation_method": "demo",
                        "evidence": {"fps": fps},
                    }
                    self._emit_event(evt)

                dt = time.time() - t0
                sleep_s = max(0.0, dt_target - dt)
                if sleep_s:
                    time.sleep(sleep_s)
        finally:
            cap.release()
