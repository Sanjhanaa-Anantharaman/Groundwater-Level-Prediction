
import imdlib as imd
import pandas as pd

from src.config import IMD_DIR, RAIN, STATIONS, START_YEAR


HISTORICAL_END_YEAR = 2025

REALTIME_START_DATE = "2026-01-01"
REALTIME_END_DATE = "2026-06-30"


def extract_station_rainfall(ds, stations, source_priority):
    """Extract rainfall at the nearest IMD grid cell for each station."""

    rain = ds["rain"].where(ds["rain"] != -999)
    rain = rain.where(rain >= 0)

    results = []

    for station in stations.itertuples():
        series = rain.sel(
            lat=float(station.lat),
            lon=float(station.lon),
            method="nearest",
        ).to_series()

        station_df = series.rename("rain").rename_axis("date").reset_index()

        station_df["station_id"] = str(station.station_id)
        station_df["date"] = pd.to_datetime(
            station_df["date"]
        ).dt.normalize()
        station_df["source_priority"] = source_priority

        results.append(
            station_df[["station_id", "date", "rain", "source_priority"]]
        )

    return pd.concat(results, ignore_index=True)


def main():
    IMD_DIR.mkdir(parents=True, exist_ok=True)

    realtime_dir = IMD_DIR / "realtime"
    realtime_dir.mkdir(parents=True, exist_ok=True)

    stations = pd.read_csv(STATIONS, dtype={"station_id": str})

    print("Loading historical rainfall data...")

    historical_ds = imd.open_data(
        "rain",
        START_YEAR,
        HISTORICAL_END_YEAR,
        "yearwise",
        file_dir=str(IMD_DIR),
    ).get_xarray()

    historical_df = extract_station_rainfall(
        historical_ds,
        stations,
        source_priority=0,
    )

    print("Retrieving real-time rainfall data for January–June 2026...")

    realtime_data = imd.get_real_data(
        "rain",
        REALTIME_START_DATE,
        REALTIME_END_DATE,
        file_dir=str(realtime_dir),
    )

    realtime_ds = realtime_data.get_xarray()

    realtime_df = extract_station_rainfall(
        realtime_ds,
        stations,
        source_priority=1,
    )

    combined = pd.concat(
        [historical_df, realtime_df],
        ignore_index=True,
    )

    combined["is_valid"] = combined["rain"].notna()

    combined = combined.sort_values(
        ["station_id", "date", "is_valid", "source_priority"]
    )

    combined = combined.drop_duplicates(
        subset=["station_id", "date"],
        keep="last",
    )

    combined = combined.drop(
        columns=["is_valid", "source_priority"]
    )

    combined = combined.sort_values(
        ["station_id", "date"]
    ).reset_index(drop=True)

    RAIN.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(RAIN, index=False)

    print("\nRainfall pipeline completed.")
    print(f"Saved to: {RAIN}")
    print(f"Total rows: {len(combined)}")
    print(f"Number of stations: {combined['station_id'].nunique()}")
    print(
        f"Date range: {combined['date'].min().date()} "
        f"to {combined['date'].max().date()}"
    )

    print("\nRows and valid rainfall days by station:")
    print(
        combined.groupby("station_id")["rain"]
        .agg(total_days="size", valid_days="count")
    )

    print(
        "\nOverall missing rainfall percentage:",
        round(combined["rain"].isna().mean() * 100, 2),
        "%",
    )

    print("\n2026 coverage by station:")
    data_2026 = combined[
        (combined["date"] >= "2026-01-01")
        & (combined["date"] <= "2026-06-30")
    ]

    print(
        data_2026.groupby("station_id")["rain"]
        .agg(total_days="size", valid_days="count")
    )


if __name__ == "__main__":
    main()
