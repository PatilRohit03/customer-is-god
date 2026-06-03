from typing import List, Dict


class DeepSortAdapter:
    """Adapter for deep_sort_realtime to present a uniform tracker interface.

    Usage:
        adapter = DeepSortAdapter(max_age=30)
        tracks = adapter.update(detections, frame)

    Where detections is list of {'bbox': [x1,y1,x2,y2], 'confidence': float}
    Returns list of objects with attributes: track_id (int), bbox (list)
    """

    def __init__(self, max_age: int = 30, n_init: int = 3):
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort
        except Exception as e:
            raise RuntimeError('deep_sort_realtime is not installed or failed to import: ' + str(e))

        self._ds = DeepSort(max_age=max_age, n_init=n_init)

    def update(self, detections: List[Dict], frame=None):
        """Update tracker with detections. Returns list of simple track objects."""
        # deep_sort_realtime expects detections as list of [x1,y1,x2,y2,score]
        ds_input = []
        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            score = float(d.get('confidence', 0.0))
            ds_input.append([x1, y1, x2, y2, score])

        tracks = self._ds.update_tracks(ds_input, frame=frame)
        out = []
        for tr in tracks:
            if not tr.is_confirmed():
                continue
            obj = SimpleTrack(tr.track_id, tr.to_ltrb())
            out.append(obj)
        return out


class SimpleTrack:
    def __init__(self, track_id: int, ltrb: List[float]):
        # deep_sort_realtime `to_ltrb()` returns [left, top, right, bottom]
        left, top, right, bottom = ltrb
        self.track_id = track_id
        self.bbox = [left, top, right, bottom]
*** End Patch