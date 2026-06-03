from typing import List


class ByteTrackAdapter:
    """Adapter stub for ByteTrack integration.

    This adapter performs a lazy import of a locally installed ByteTrack implementation.
    It intentionally fails fast with a helpful error if ByteTrack isn't installed so the
    operator can `pip install` the correct package.

    Supported packages (try installing one):
    - bytetrack (community implementations vary)
    - bytetrack-pytorch

    The adapter assumes the installed package exposes a tracker with an `update()`
    method that accepts detections in [x1,y1,x2,y2,score] format and returns track objects
    with `track_id` and `to_ltrb()` or similar. Because concrete APIs differ, this
    adapter is a lightweight shim that will need minor adjustments when a particular
    ByteTrack package is chosen.
    """

    def __init__(self, *args, **kwargs):
        # Try a few known module names
        tried = []
        impl = None
        for mod in ('bytetrack', 'bytetrack_pytorch', 'bytetrack_realtime', 'byte_track'):
            tried.append(mod)
            try:
                impl = __import__(mod)
                break
            except Exception:
                impl = None
        if impl is None:
            raise RuntimeError(
                'ByteTrack implementation not found. Install one of: pip install bytetrack\n'
                f'Tried modules: {tried}\n'
                'See project README for recommended ByteTrack package and installation instructions.'
            )

        # Store reference to implementation module for later use. Actual usage depends on the
        # concrete library; this adapter will attempt to find a plausible class name.
        self._impl = impl
        # Note: users should modify the following lines to match the API of their ByteTrack package.
        TrackerClass = getattr(impl, 'ByteTrack', None) or getattr(impl, 'BYTETrack', None) or getattr(impl, 'BYTETracker', None)
        if TrackerClass is None:
            # Some libs expose a factory or different name; keep impl module for custom wiring
            raise RuntimeError('Found ByteTrack module but could not locate tracker class.\n'
                               'You may need to adjust src/pipeline/bytetrack_adapter.py to match the installed package API.')
        # Instantiate with default args (may need adjustment per package)
        try:
            self._tracker = TrackerClass()
        except Exception as e:
            raise RuntimeError('Failed to instantiate ByteTrack tracker: ' + str(e))

    def update(self, detections: List[dict], frame=None):
        """Convert detections and call the underlying ByteTrack update method.

        Expects `detections` as list of {'bbox': [x1,y1,x2,y2], 'confidence': float}
        Returns list of objects with `track_id` and `bbox` attributes (ltrb format).
        """
        ds_input = []
        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            score = float(d.get('confidence', 0.0))
            ds_input.append([x1, y1, x2, y2, score])

        # Concrete API varies; try common call signatures
        if hasattr(self._tracker, 'update'):
            tracks = self._tracker.update(ds_input, frame)
        else:
            raise RuntimeError('ByteTrack tracker does not expose `update()` with expected signature.')

        out = []
        for tr in tracks:
            # try several attribute patterns
            tid = getattr(tr, 'track_id', None) or getattr(tr, 'track_id_', None) or getattr(tr, 'id', None)
            ltrb = None
            if hasattr(tr, 'to_ltrb'):
                ltrb = tr.to_ltrb()
            elif hasattr(tr, 'tlbr'):
                ltrb = tr.tlbr
            elif hasattr(tr, 'tlbrs'):
                ltrb = tr.tlbrs
            if tid is None or ltrb is None:
                # best-effort: skip incompatible track object
                continue
            obj = SimpleTrack(tid, ltrb)
            out.append(obj)
        return out


class SimpleTrack:
    def __init__(self, track_id: int, ltrb: List[float]):
        left, top, right, bottom = ltrb
        self.track_id = track_id
        self.bbox = [left, top, right, bottom]
