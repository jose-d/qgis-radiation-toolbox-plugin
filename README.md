# Radiation ToolBox Plugin for QGIS 4.x

This plugin allows to easily load data from Safecast radiation monitoring devices (LOG file) like bGeigie Nano into QGIS as a new vector point layer. Experimental support for ERS 2.0 format (European Radiometric and Spectrometry format)(1) and some types of PicoEnvirotec PEI files (2). 

This repository is an unofficial QGIS 4 / Qt 6 compatibility fork. It is not an official OpenGeoLabs or SURO release. Upstream authorship and project history are preserved below; issues and releases for this fork are managed in this GitHub repository.

## 2026-07-03 Update - QGIS 4 / Qt 6 packaging

- Ported plugin imports from PyQt5-style APIs to QGIS version-independent `qgis.PyQt` imports for QGIS 4 / Qt 6 compatibility.
- Plugin packaging is produced with `make package` as `radiation_toolbox_plugin.zip`.
- Qt resources are built as a binary `resources.rcc` file using Qt 6 `rcc`; `resources.py` only registers that file through `qgis.PyQt.QtCore.QResource`.
- The package vendors the pinned `radiation_toolbox_reader` dependency, so the zip can be installed directly from QGIS Plugin Manager using "Install from ZIP".
- GitHub Actions build the zip on pushes, pull requests, tags, and manual release runs.

### Build locally

Install the build tools:

```bash
sudo apt-get install make python3-pip python3-sphinx qt6-base-dev-tools qt6-l10n-tools unzip zip
```

Build the installable plugin zip:

```bash
make package
```

The output is `radiation_toolbox_plugin.zip`. The build uses Qt 6 tools by default: `/usr/lib/qt6/libexec/rcc` for resources and `/usr/lib/qt6/bin/lrelease` for translations when available. Override them with `make RCC=/path/to/rcc LRELEASE=/path/to/lrelease package` if your distribution installs Qt tools elsewhere.

The packaged plugin version is generated from the Git tag when the build runs on a tag, with a leading `v` stripped for QGIS metadata. For example, `v2.1.0-qgis4` becomes `version=2.1.0-qgis4` in the zip. For manual local builds, use `make package VERSION=v2.1.0-qgis4` to force the same behavior.


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
