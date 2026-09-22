"""Archived forecast-rain features; never fall back to future observed rain.

The source is fixed-lead previous-day forecast data. Historical publication
availability requires a separate contract and is not certified by this loader.
"""
import numpy as np
from hydro_hourly_forecast import epoch
from hydro_hourly_models import GROUPS

WINDOWS=(3,6,9,12)
FIELD='precipitation_previous_day1'


def forecast_lookup(location):
    if location.get('utc_offset_seconds')!=-10800 or location.get('hourly_units',{}).get(FIELD)!='mm':
        raise ValueError('Unexpected historical forecast units/timezone')
    hourly=location['hourly'];times=hourly['time'];values=hourly.get(FIELD)
    if values is None or len(times)!=len(values):raise ValueError('Missing or misaligned forecast rainfall')
    result={}
    for text,value in zip(times,values):
        at=epoch(text)
        if at in result:raise ValueError('Duplicate forecast valid time')
        v=float(value) if value is not None else np.nan
        if np.isfinite(v) and v<0:raise ValueError('Negative precipitation')
        result[at]=v
    return result


def complete_future_totals(lookup,origins,window):
    if window not in WINDOWS:raise ValueError('Unsupported rainfall window')
    # Each valid-hour amount covers its preceding hour; origin itself is excluded.
    values=np.array([[lookup.get(t+k*3600,np.nan) for k in range(1,window+1)] for t in origins],float)
    totals=values.sum(axis=1)
    totals[~np.isfinite(values).all(axis=1)]=np.nan
    return totals


def future_rain_features(weather,origins):
    if len(weather)!=3 or any(len(locations)!=len(GROUPS) for locations in weather):
        raise ValueError('Expected three models and five frozen locations')
    parsed=[[forecast_lookup(location) for location in locations] for locations in weather]
    cols=[];counts=[];names=[]
    for j,group in enumerate(GROUPS):
        for window in WINDOWS:
            totals=np.array([complete_future_totals(model[j],origins,window) for model in parsed])
            count=np.isfinite(totals).sum(axis=0)
            mean=np.divide(np.nansum(totals,axis=0),count,out=np.full(len(origins),np.nan),where=count>0)
            cols.append(mean/100);counts.append(count);names.append(f'{group}:forecast_P{window}/100mm')
    return np.column_stack(cols),np.column_stack(counts),names
