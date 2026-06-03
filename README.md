# Store Intelligence Dashboard

This project is a real-time dashboard built to track how customers move around a retail store using computer vision. We built this to solve the problem statement of tracking customer journeys and measuring store conversion rates using video feeds and POS (Point of Sale) data.

## How It Matches the Problem Statement
The main goal of the problem statement was to create a system that can measure customer behavior in a physical store just like we do for an online website. 
Our dashboard does exactly this by:
- **Counting unique visitors:** Knowing exactly how many people walk in and out.
- **Tracking dwell time:** Measuring how long people spend in different zones (like the main floor or checkout line).
- **Conversion funnel:** Combining the video tracking with the POS data to see how many people actually bought something versus just looking around.
- **Queue analytics:** Keeping an eye on the billing line to see the wait times and if people abandon the line because it's too long.

## Missing Resources & How We Overcame Them
While building this, we ran into a few data problems:
1. **Missing / Messy Camera Feeds:** For Store 2, we didn't have all the perfect camera angles, and one of the entry videos was just a duplicate from a different date. We overcame this by updating our store configuration file (`layouts.json`) to safely ignore the bad duplicate feeds and only rely on the 3 good cameras (entry, main floor, and billing).
2. **Adblocker Issues:** We noticed our checkout camera was completely blank. It turns out our adblockers were hiding any network requests with the word "billing" or "checkout". We fixed this by renaming our video files to generic names like `area_5.mp4` so the browser wouldn't block them!
3. **Browser Limitations (The "Black Box" Issue):** Browsers only let you open 6 video streams at once. When we tried to view multiple stores or hot-swapped between Store 1 and Store 2, the old background video streams were kept alive by Chrome, maxing out the 6-connection limit and causing the final camera to appear as a black box. **To fix this, simply press F5 (refresh the page)** when switching stores to instantly clear the browser's HTTP cache.
4. **Docker Network DNS Timeouts:** When running `docker compose up --build` for the first time, Docker can occasionally lose internet access (`Failed to establish a new connection...`). This is a known Docker Desktop glitch. If this happens to you, simply restart the Docker Desktop app and re-run the build command—it will successfully resume from where it left off.

## Important Note on Videos (For Evaluators)
Because the video files are huge, **we did not upload them to this GitHub repo**. This project is specifically configured for the two stores provided in the problem resources. 

To run the project correctly, you must place the provided videos into the exact folder structure below. 
**Crucially, you must rename the billing/checkout video to `area_5.mp4`** to prevent browser adblockers from hiding the video stream!

```text
data/
└── resource/
    ├── Store 1/
    │   ├── entry.mp4
    │   ├── zone.mp4
    │   └── area_5.mp4   <-- (This is the billing video)
    └── Store 2/
        ├── entry 2.mp4
        ├── zone.mp4
        └── area_5.mp4   <-- (This is the billing video)
```

## Installation & Setup
Make sure you have Docker installed.

1. Clone this folder.
2. Put the provided video files inside the `data/resource/Store 1` and `data/resource/Store 2` folders as shown above.
3. Open your terminal and run:
   ```bash
   docker compose up --build
   ```
*(Note: You do not need to run a separate script for the detection pipeline! The YOLOv8 computer vision pipeline is fully integrated into the FastAPI backend. It automatically runs against the clips and feeds the event output directly into the API when you start the streams.)*

4. Open your browser and go to the dashboard: 
   👉 **[http://localhost:8000/dashboard](http://localhost:8000/dashboard)**
5. If you want to view the FastAPI Swagger Docs to see the API endpoints, go to:
   👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

## How to Use
- Type in `STORE_1` or `STORE_2` and click **Start Live Tracking**.
- You will see the videos start playing with bounding boxes, and the metrics will update live.
- **Important:** Click **Stop Tracking** before switching to another store to free up the browser's video connections!
- If you want to start a fresh run for your evaluation, click the **Reset Database** button.
