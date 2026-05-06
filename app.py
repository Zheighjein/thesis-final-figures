# ============================================
# CHAPTER 4 FIGURE + TABLE GENERATOR
# FINAL VERSION
# ============================================

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================
# CONFIG
# ============================================

DB_PATH = "pbr_merged.db"

OUTPUT_DIR = Path("chapter4_outputs")

FIG_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"

FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.size"] = 11

# ============================================
# DATABASE CONNECTION
# ============================================

conn = sqlite3.connect(DB_PATH)

# ============================================
# LOAD READINGS
# ============================================

readings = pd.read_sql_query("""
SELECT *
FROM readings
""", conn)

# ============================================
# TIMESTAMP HANDLING
# ============================================

readings["datetime"] = pd.to_datetime(
    readings["time"],
    unit="s"
)

start_time = readings["time"].min()

readings["elapsed_hours"] = (
    readings["time"] - start_time
) / 3600

readings["day"] = (
    readings["elapsed_hours"] // 24
).astype(int) + 1

# ============================================
# FILTER DATASETS
# ============================================

pid_df = readings[
    (readings["reactor_id"] == 1) &
    (readings["mode"].isin(["PID"]))
].copy()

onoff_df = readings[
    (readings["reactor_id"] == 2) &
    (readings["mode"].isin(["ONOFF"]))
].copy()

# ============================================
# SAFETY CHECKS
# ============================================

if pid_df.empty:
    raise Exception("PID dataset is empty.")

if onoff_df.empty:
    raise Exception("ONOFF dataset is empty.")

# ============================================
# HELPER FUNCTIONS
# ============================================

def save_plot(filename):
    plt.tight_layout()
    plt.savefig(
        FIG_DIR / filename,
        bbox_inches="tight"
    )
    plt.close()

def count_activations(series):
    return (
        (series.shift(1) == 0) &
        (series == 1)
    ).sum()

# ============================================
# ZOOM WINDOW
# ============================================

zoom_start = 24
zoom_end = 30

# ============================================
# FIGURE 4.7
# FULL 4-DAY pH TIME SERIES — ON/OFF
# ============================================

plt.figure(figsize=(14, 5))

plt.plot(
    onoff_df["elapsed_hours"],
    onoff_df["ph"],
    linewidth=1.2,
    label="pH"
)

max_hour = int(onoff_df["elapsed_hours"].max())

for d in range(0, max_hour + 24, 24):

    plt.axvspan(
        d + 12,
        d + 24,
        alpha=0.10
    )

plt.axhline(
    7.5,
    linestyle="--",
    linewidth=1
)

plt.xlabel("Elapsed Time (Hours)")
plt.ylabel("pH")

plt.title(
    "Figure 4.7 — Full 4-Day pH Time Series (PBR-2 ON/OFF)"
)

plt.grid(alpha=0.3)

save_plot(
    "Figure_4_7_ONOFF_full_timeseries.png"
)

# ============================================
# FIGURE 4.8
# ZOOMED 6-HOUR WINDOW — ON/OFF
# ============================================

zoom_df = onoff_df[
    (onoff_df["elapsed_hours"] >= zoom_start) &
    (onoff_df["elapsed_hours"] <= zoom_end)
]

fig, ax1 = plt.subplots(figsize=(14, 5))

ax1.plot(
    zoom_df["elapsed_hours"],
    zoom_df["ph"],
    linewidth=1.5
)

ax1.set_ylabel("pH")
ax1.set_xlabel("Elapsed Time (Hours)")
ax1.grid(alpha=0.3)

ax2 = ax1.twinx()

ax2.step(
    zoom_df["elapsed_hours"],
    zoom_df["co2"],
    where="post",
    linewidth=1
)

ax2.set_ylabel("CO₂ State")

plt.title(
    "Figure 4.8 — Zoomed 6-Hour Excerpt (PBR-2 ON/OFF)"
)

save_plot(
    "Figure_4_8_ONOFF_zoomed.png"
)

# ============================================
# FIGURE 4.9
# DAILY MEAN pH BAR CHART — ON/OFF
# ============================================

daily_onoff = (
    onoff_df
    .groupby(["day", "light_state"])["ph"]
    .mean()
    .reset_index()
)

pivot_onoff = daily_onoff.pivot(
    index="day",
    columns="light_state",
    values="ph"
)

pivot_onoff = pivot_onoff.rename(columns={
    0: "Dark Period",
    1: "Light Period"
})

pivot_onoff.plot(
    kind="bar",
    figsize=(10, 5)
)

plt.ylabel("Mean pH")
plt.xlabel("Experimental Day")

plt.title(
    "Figure 4.9 — Daily Mean pH (PBR-2 ON/OFF)"
)

plt.grid(axis="y", alpha=0.3)

save_plot(
    "Figure_4_9_ONOFF_daily_mean.png"
)

# ============================================
# TABLE 4.5
# DAILY pH STATISTICS — ON/OFF
# ============================================

stats_onoff = (
    onoff_df
    .groupby(["day", "light_state"])
    .agg(
        mean_ph=("ph", "mean"),
        std_ph=("ph", "std"),
        min_ph=("ph", "min"),
        max_ph=("ph", "max")
    )
    .reset_index()
)

stats_onoff["ph_range"] = (
    stats_onoff["max_ph"] -
    stats_onoff["min_ph"]
)

activations = (
    onoff_df
    .groupby(["day", "light_state"])["co2"]
    .apply(count_activations)
    .reset_index(name="solenoid_activations")
)

stats_onoff = stats_onoff.merge(
    activations,
    on=["day", "light_state"]
)

stats_onoff["light_state"] = (
    stats_onoff["light_state"]
    .map({
        0: "Dark",
        1: "Light"
    })
)

stats_onoff.to_csv(
    TABLE_DIR / "Table_4_5_ONOFF_statistics.csv",
    index=False
)

# ============================================
# FIGURE 4.10
# FULL 4-DAY pH TIME SERIES — PID
# ============================================

plt.figure(figsize=(14, 5))

plt.plot(
    pid_df["elapsed_hours"],
    pid_df["ph"],
    linewidth=1.2
)

max_hour = int(pid_df["elapsed_hours"].max())

for d in range(0, max_hour + 24, 24):

    plt.axvspan(
        d + 12,
        d + 24,
        alpha=0.10
    )

plt.axhline(
    7.5,
    linestyle="--",
    linewidth=1
)

plt.xlabel("Elapsed Time (Hours)")
plt.ylabel("pH")

plt.title(
    "Figure 4.10 — Full 4-Day pH Time Series (PBR-1 PID)"
)

plt.grid(alpha=0.3)

save_plot(
    "Figure_4_10_PID_full_timeseries.png"
)

# ============================================
# FIGURE 4.11
# ZOOMED 6-HOUR WINDOW — PID
# ============================================

zoom_pid = pid_df[
    (pid_df["elapsed_hours"] >= zoom_start) &
    (pid_df["elapsed_hours"] <= zoom_end)
]

fig, ax1 = plt.subplots(figsize=(14, 5))

ax1.plot(
    zoom_pid["elapsed_hours"],
    zoom_pid["ph"],
    linewidth=1.5
)

ax1.set_ylabel("pH")
ax1.set_xlabel("Elapsed Time (Hours)")
ax1.grid(alpha=0.3)

ax2 = ax1.twinx()

ax2.step(
    zoom_pid["elapsed_hours"],
    zoom_pid["co2"],
    where="post",
    linewidth=1
)

ax2.set_ylabel("CO₂ State")

plt.title(
    "Figure 4.11 — Zoomed 6-Hour Excerpt (PBR-1 PID)"
)

save_plot(
    "Figure_4_11_PID_zoomed.png"
)

# ============================================
# FIGURE 4.12
# DAILY MEAN pH BAR CHART — PID
# ============================================

daily_pid = (
    pid_df
    .groupby(["day", "light_state"])["ph"]
    .mean()
    .reset_index()
)

pivot_pid = daily_pid.pivot(
    index="day",
    columns="light_state",
    values="ph"
)

pivot_pid = pivot_pid.rename(columns={
    0: "Dark Period",
    1: "Light Period"
})

pivot_pid.plot(
    kind="bar",
    figsize=(10, 5)
)

plt.ylabel("Mean pH")
plt.xlabel("Experimental Day")

plt.title(
    "Figure 4.12 — Daily Mean pH (PBR-1 PID)"
)

plt.grid(axis="y", alpha=0.3)

save_plot(
    "Figure_4_12_PID_daily_mean.png"
)

# ============================================
# TABLE 4.6
# DAILY pH STATISTICS — PID
# ============================================

stats_pid = (
    pid_df
    .groupby(["day", "light_state"])
    .agg(
        mean_ph=("ph", "mean"),
        std_ph=("ph", "std"),
        min_ph=("ph", "min"),
        max_ph=("ph", "max")
    )
    .reset_index()
)

stats_pid["ph_range"] = (
    stats_pid["max_ph"] -
    stats_pid["min_ph"]
)

activations_pid = (
    pid_df
    .groupby(["day", "light_state"])["co2"]
    .apply(count_activations)
    .reset_index(name="solenoid_activations")
)

stats_pid = stats_pid.merge(
    activations_pid,
    on=["day", "light_state"]
)

stats_pid["light_state"] = (
    stats_pid["light_state"]
    .map({
        0: "Dark",
        1: "Light"
    })
)

stats_pid.to_csv(
    TABLE_DIR / "Table_4_6_PID_statistics.csv",
    index=False
)

# ============================================
# LOAD PERFORMANCE DATA
# ============================================

perf = pd.read_sql_query("""
SELECT *
FROM performance_log
""", conn)

perf["datetime"] = pd.to_datetime(
    perf["timestamp"],
    unit="s"
)

perf_pid = perf[
    perf["reactor_id"] == 1
].iloc[::10]

perf_onoff = perf[
    perf["reactor_id"] == 2
].iloc[::10]

# ============================================
# FIGURE 4.13
# CUMULATIVE IAE
# ============================================

plt.figure(figsize=(12, 5))

plt.plot(
    perf_pid["datetime"],
    perf_pid["iae"],
    linewidth=1.5,
    label="PBR-1 PID"
)

plt.plot(
    perf_onoff["datetime"],
    perf_onoff["iae"],
    linewidth=1.5,
    label="PBR-2 ON/OFF"
)

plt.ylabel("Cumulative IAE")
plt.xlabel("Time")

plt.title(
    "Figure 4.13 — Cumulative IAE Over Time"
)

plt.legend()
plt.grid(alpha=0.3)

save_plot(
    "Figure_4_13_Cumulative_IAE.png"
)

# ============================================
# LOAD SUMMARY TABLE
# ============================================

summary = pd.read_sql_query("""
SELECT *
FROM summary
""", conn)

summary = (
    summary
    .sort_values("timestamp")
    .groupby("reactor_id")
    .tail(1)
)

# ============================================
# FIGURE 4.14
# IAE COMPARISON
# ============================================

if not summary.empty:

    pid_iae = summary[
        summary["reactor_id"] == 1
    ]["final_iae"].values[0]

    onoff_iae = summary[
        summary["reactor_id"] == 2
    ]["final_iae"].values[0]

    plt.figure(figsize=(6, 5))

    plt.bar(
        ["PID", "ON/OFF"],
        [pid_iae, onoff_iae]
    )

    plt.ylabel("Final IAE")

    plt.title(
        "Figure 4.14 — Final IAE Comparison"
    )

    plt.grid(axis="y", alpha=0.3)

    save_plot(
        "Figure_4_14_IAE_Comparison.png"
    )

# ============================================
# FIGURE 4.15
# ISE COMPARISON
# ============================================

if not summary.empty:

    pid_ise = summary[
        summary["reactor_id"] == 1
    ]["final_ise"].values[0]

    onoff_ise = summary[
        summary["reactor_id"] == 2
    ]["final_ise"].values[0]

    plt.figure(figsize=(6, 5))

    plt.bar(
        ["PID", "ON/OFF"],
        [pid_ise, onoff_ise]
    )

    plt.ylabel("Final ISE")

    plt.title(
        "Figure 4.15 — Final ISE Comparison"
    )

    plt.grid(axis="y", alpha=0.3)

    save_plot(
        "Figure_4_15_ISE_Comparison.png"
    )

# ============================================
# FIGURE 4.16
# ITAE COMPARISON
# ============================================

if not summary.empty:

    pid_itae = summary[
        summary["reactor_id"] == 1
    ]["final_itae"].values[0]

    onoff_itae = summary[
        summary["reactor_id"] == 2
    ]["final_itae"].values[0]

    plt.figure(figsize=(6, 5))

    plt.bar(
        ["PID", "ON/OFF"],
        [pid_itae, onoff_itae]
    )

    plt.ylabel("Final ITAE")

    plt.title(
        "Figure 4.16 — Final ITAE Comparison"
    )

    plt.grid(axis="y", alpha=0.3)

    save_plot(
        "Figure_4_16_ITAE_Comparison.png"
    )

# ============================================
# TABLE 4.7
# FINAL ERROR METRICS
# ============================================

if not summary.empty:

    table_47 = summary[
        [
            "reactor_id",
            "mode",
            "final_iae",
            "final_ise",
            "final_itae"
        ]
    ]

    table_47.to_csv(
        TABLE_DIR / "Table_4_7_Final_Error_Metrics.csv",
        index=False
    )

# ============================================
# CLOSE DATABASE
# ============================================

conn.close()

# ============================================
# FINISHED
# ============================================

print("\n====================================")
print("CHAPTER 4 OUTPUTS GENERATED")
print("====================================")
print(f"Figures saved to: {FIG_DIR}")
print(f"Tables saved to : {TABLE_DIR}")
print("====================================")