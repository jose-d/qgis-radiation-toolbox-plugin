# Radiation ToolBox Plugin for QGIS 3.x

This plugin allows to easily load data from Safecast radiation monitoring devices (LOG file) like bGeigie Nano into QGIS as a new vector point layer. Experimental support for ERS 2.0 format (European Radiometric and Spectrometry format)(1) and some types of PicoEnvirotec PEI files (2). 


## 2024-03-04 Update - added new language files

- Slovak / Slovenčina (Miroslav Vanek)

## 2024-03-01 Update - added new language files

- Polish / Polski (Anna Mrozik)

## 2023-10-02 Update - complete code refresh, upgraded plot window

- current version 1.0.1, also available from QGIS plugin managing / installation tool
- support for CzechRad LOG data format - initial implementation (conversion coefficient to be updated after device callibration)
- plot window now allows panning and zooming, not dependent on OS or external libraries

## 2023-04-06 Update - added new language files

Currently the RadiationToolbox contains these translations

- Czech / Čeština (Jan Helebrant / Martin Landa)
- English (Jan Helebrant / Martin Landa)
- French / Français (Louis Bertrand)
- German / Deutsch (draft, Jan Helebrant)
- Italian / Italiano (Andrea Serafini)
- Russian / Русский (Jelena Burianová)
- Ukrainian / Українська (Pavlo Tkachenko)

## 2023-02-28 Update - plot fixed in Windows OS

- implemented fix provided by Petr Klosko (Twitter: @pklosko) usable only in Windows OS (in linux the plot works without need to fix anything)
- get the plugin from the fixed branch (Windows only, the fix causes errors in linux):

https://github.com/jose-d/qgis-radiation-toolbox-plugin/tree/Windows_fix


Features:

- easy loading of Safecast LOG files with predefined color style

- Statistics and Plot window for additional details - currently only available for Safecast data, some issues regarding the plot feature in Windows

- editing feature for Safecast files, ability to save edited file in LOG format for compatibility with Safecast API and other tools

- initial experimental support for quick loading ERS files and some types of PEI files (issues related to IRIS airborne gammaspectrometry binary files)

- user interface translated in several languages (English, Czech, Russian, Italian translation to be added soon), no problem to add other languages


Developed by OpenGeoLabs s.r.o for National Radiation Protection Institute (SURO), Prague, Czech Republic (SURO).


(1) https://github.com/juhele/opengeodata/tree/master/ERS_-_European_Radiometric_and_Spectrometry_format

(2) https://github.com/juhele/opengeodata/tree/master/Ground_radiation_monitoring_DEMO_data



