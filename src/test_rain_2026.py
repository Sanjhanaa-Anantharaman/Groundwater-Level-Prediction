
import imdlib as imd
import pandas as pd

from src.config import IMD_DIR, STATIONS

# Keep real-time data separate from historical .grd files.
REALTIME_DIR = IMD_DIR / "realtime"
REALTIME_DIR.mkdir(parents=True, exist_ok=True)

# Match the period covered by your groundwater data.
START_DATE = "2026-01-01"
END_DATE = "2026-06-30"


def main():
    try:
        print(f"Downloading rainfall from {START_DATE} to {END_DATE}...")

        data = imd.get_real_data(
            "rain",
            START_DATE,
            END_DATE,
            file_dir=str(REALTIME_DIR),
        )

        ds = data.get_xarray()

        # Load station metadata.
        stations = pd.read_csv(
            STATIONS,
            dtype={"station_id": str},
        )

        # Convert IMD's missing-data marker to NaN.
        rain = ds["rain"].where(ds["rain"] != -999)
        rain = rain.where(rain >= 0)

        # ---------------------------------------------
        # 1. Check the retrieved date range
        # ---------------------------------------------
        print("\nRetrieved rainfall date range:")
        print("Start:", pd.Timestamp(ds.time.values[0]).date())
        print("End:  ", pd.Timestamp(ds.time.values[-1]).date())
        print("Number of dates:", len(ds.time))

        # ---------------------------------------------
        # 2. Check rainfall availability at each station
        # ---------------------------------------------
        print("\n2026 Rainfall Availability by Station")
        print("-" * 60)

        station_results = []

        for station in stations.itertuples():
            series = rain.sel(
                lat=float(station.lat),
                lon=float(station.lon),
                method="nearest",
            ).to_series()

            total_days = len(series)
            valid_days = int(series.notna().sum())
            missing_days = total_days - valid_days

            nearest_lat = float(
                rain.lat.sel(
                    lat=float(station.lat),
                    method="nearest",
                )
            )
            nearest_lon = float(
                rain.lon.sel(
                    lon=float(station.lon),
                    method="nearest",
                )
            )

            print(f"\nStation: {station.station_id}")
            print(
                f"Requested coordinates: "
                f"{station.lat}, {station.lon}"
            )
            print(
                f"Nearest grid coordinates: "
                f"{nearest_lat}, {nearest_lon}"
            )
            print(f"Valid days: {valid_days}/{total_days}")
            print(f"Missing days: {missing_days}/{total_days}")

            if valid_days > 0:
                print(f"Minimum rainfall: {series.min():.2f}")
                print(f"Maximum rainfall: {series.max():.2f}")
            else:
                print("WARNING: No valid rainfall data for this station.")

            station_results.append({
                "station_id": station.station_id,
                "total_days": total_days,
                "valid_days": valid_days,
                "missing_days": missing_days,
            })

        # ---------------------------------------------
        # 3. Check missing values across the entire grid
        # ---------------------------------------------
        print("\nOverall IMD Grid Statistics")
        print("-" * 60)

        raw_rain = ds["rain"]

        print("Total grid values:", raw_rain.size)
        print(
            "Missing (-999) values:",
            int((raw_rain == -999).sum().item()),
        )
        print(
            "Missing-data percentage:",
            round(float((raw_rain == -999).mean().item() * 100), 2),
            "%",
        )
        print("Valid rainfall values:", int(rain.count().item()))

        if rain.count().item() > 0:
            print("Minimum valid rainfall:", float(rain.min().item()))
            print("Maximum valid rainfall:", float(rain.max().item()))

        # ---------------------------------------------
        # 4. Save station-level availability report
        # ---------------------------------------------
        report_path = REALTIME_DIR / "rainfall_2026_availability.csv"

        pd.DataFrame(station_results).to_csv(
            report_path,
            index=False,
        )

        print(f"\nAvailability report saved to: {report_path}")
        print("\nReal-time rainfall retrieval completed.")

    except Exception as e:
        print(f"Real-time rainfall retrieval failed: {e}")


if __name__ == "__main__":
    main()
