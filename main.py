# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 11:23:47 2023

@author: kairo
"""

import matplotlib.pyplot as plt
from cartopy import crs as ccrs, feature as cfeature
import cartopy.io.shapereader as shpreader


shapename = 'admin_1_states_provinces_lakes_shp'
states_shp = shpreader.natural_earth(resolution='50m',
                                     category='cultural', name=shapename)



projPC = ccrs.PlateCarree()
lonW = -130
lonE = -50
latS = 25
latN = 47
cLat = (latN + latS) / 2
cLon = (lonW + lonE) / 2
res = '110m'


# Plano
"""
fig = plt.figure(figsize=(11, 11.5))
ax = plt.subplot(1, 1, 1, projection=projPC)
ax.set_title('Plate Carree')
gl = ax.gridlines(
    draw_labels=True, linewidth=2, color='gray', alpha=0.1, linestyle='--'
)
"""

#Curvo
projStr = ccrs.Stereographic(central_longitude=cLon, central_latitude=cLat)
fig = plt.figure(figsize=(11, 8.5))
ax = plt.subplot(1, 1, 1, projection=projStr)
ax.set_title('Stereographic')
gl = ax.gridlines(
    draw_labels=True, linewidth=2, color='gray', alpha=0.1, linestyle='--'
)

ax.set_extent([lonW, lonE, latS, latN], crs=projPC)
ax.coastlines(resolution=res, color='black')
ax.add_feature(cfeature.STATES, linewidth=0.3, edgecolor='brown')
ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='blue');



