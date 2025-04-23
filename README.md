# RTM-VTS: Real-Time Map for VTS Situations and Bus Collisions

## Overview

This Django web application provides a real-time map visualization integrating traffic situation data from the Norwegian Public Roads Administration (Statens vegvesen - VTS) DATEX II API with static bus route information.

The core functionalities include:

*   **Fetching VTS Data:** Regularly retrieves current road situation data (road work, accidents, closures, etc.) from the VTS DATEX II API.
*   **Bus Route Management:** Imports static bus route geometries from external sources (e.g., GeoJSON).
*   **Collision Detection:** Calculates potential proximity conflicts (collisions within a tolerance) between VTS situation points/paths and bus route paths.
*   **Real-time Publishing:** Publishes newly detected collisions via MQTT for consumption by external clients or dashboards.
*   **Interactive Map Display:** Visualizes VTS situations and bus routes on an interactive map.
*   **(Potential) API Endpoint:** (If implemented) Provides collision data via a REST API.
*   **(Potential) Drawing Tools:** Allows users to draw custom features on the map (as described in the original README).

## Requirements

### 1. System Dependencies

These must be installed on your system **before** installing Python packages. Installation methods vary by OS:

*   **Python:** Version 3.10+ recommended (check compatibility with Django 5.1).
*   **GDAL (Geospatial Data Abstraction Library):** Essential for GeoDjango.
    *   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install gdal-bin libgdal-dev`
    *   **macOS (Homebrew):** `brew update && brew install gdal`
    *   **Windows:** Use pre-compiled binaries (e.g., [OSGeo4W](https://trac.osgeo.org/osgeo4w/)) or Conda (`conda install -c conda-forge gdal`).
*   **SpatiaLite Library (mod_spatialite):** Required for the SpatiaLite database backend.
    *   **Linux (Debian/Ubuntu):** `sudo apt install libsqlite3-mod-spatialite`
    *   **macOS (Homebrew):** `brew install libspatialite`
    *   **Windows:** Download `mod_spatialite.dll` ([gaia-gis.it](https://www.gaia-gis.it/fossil/libspatialite/)), install via OSGeo4W/Conda, or ensure its location is set via the `SPATIALITE_LIBRARY_PATH` environment variable.
*   **MQTT Broker:** A running MQTT broker is needed for the real-time publishing feature.
    *   **Recommendation:** [Mosquitto](https://mosquitto.org/download/) for local development. Install via package manager (`apt`, `brew`) or download the installer for Windows.
    *   Ensure the broker is running and accessible from where you run the Django application.

### 2. Python Environment & Packages

*   **Virtual Environment:** Strongly recommended.
    ```bash
    # Create environment (use python or python3 as appropriate)
    python -m venv .venv

    # Activate:
    # Linux/macOS (bash/zsh)
    source .venv/bin/activate
    # Windows (cmd.exe)
    # .\.venv\Scripts\activate.bat
    # Windows (PowerShell)
    # .\.venv\Scripts\Activate.ps1
    ```
*   **Python Packages:** Install using the provided `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure your `requirements.txt` file is up-to-date using `pip freeze > requirements.txt` after installing all packages.)*

## Setup and Configuration

### 1. Clone the Repository

```bash
# Using SSH (Recommended if you have keys setup)
git clone git@github.com:TromsFylkestrafikk/rtm-vts.git
# Or using HTTPS
# git clone https://github.com/TromsFylkestrafikk/rtm-vts.git

cd rtm-vts
```