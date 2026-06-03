STORE_LAYOUTS = {
    'STORE_1': {
        'store_id': 'STORE_1',
        'name': 'Store 1',
        'camera_types': {
            'CAM 1 - zone.mp4': 'zone',
            'CAM 2 - zone.mp4': 'zone',
            'CAM 3 - entry.mp4': 'entry',
            'area_5.mp4': 'billing',
        },
        'zones': {
            'ENTRY': {'camera': 'CAM 3 - entry.mp4'},
            'MAIN_FLOOR': {'camera': ['CAM 1 - zone.mp4', 'CAM 2 - zone.mp4']},
            'BILLING': {
                'camera': 'area_5.mp4',
                'staff_zone': [0, 0, 320, 640], # [x1, y1, x2, y2]
                'queue_zone': [300, 200, 640, 640]
            },
        },
    },
    'STORE_2': {
        'store_id': 'STORE_2',
        'name': 'Store 2',
        'camera_types': {
            'entry 2.mp4': 'entry',
            'zone.mp4': 'zone',
            'area_5.mp4': 'billing',
        },
        'zones': {
            'ENTRY': {'camera': 'entry 2.mp4'},
            'MAIN_FLOOR': {'camera': 'zone.mp4'},
            'BILLING': {
                'camera': 'area_5.mp4',
                'staff_zone': [300, 0, 450, 640],
                'queue_zone': [0, 200, 640, 640]
            },
        },
    },
}
