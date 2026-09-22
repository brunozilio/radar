"""Compatibility entry point for the Radar-only hourly forecast.

The former dual-model runner has been removed. Existing issued outputs remain
immutable; new runs use the same ledger and duplicate protection as the scheduler.
"""
from hydro_hourly_forecast import run

if __name__ == '__main__':
    run()
