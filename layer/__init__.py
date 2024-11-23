import os
import sys
import time
import inspect
import csv
import copy
from enum import Enum
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor

from qgis.utils import iface, Qgis
from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsMessageLog, QgsField, QgsGraduatedSymbolRenderer, QgsSymbol

from osgeo import ogr

from .exceptions import LoadError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from style import Style, StyleError

from radiation_toolbox_reader.exceptions import ReaderExportError

class LayerType(Enum):
    Safecast = 0
    ERS = 1
    PEI = 2

class LayerBase(QgsVectorLayer):
    """QGIS layer base class (read-only memory based).

        :param fileName: path to input file
        :param storageFormat: storage format for layer (Memory or SQLite)
    """
    def __init__(self, fileName, storageFormat):
        self._fileName = fileName
        self._layerName = os.path.splitext(os.path.basename(self._fileName))[0]
        self.storageFormat = storageFormat
        
        # create point layer (WGS-84, EPSG:4326)
        super(LayerBase, self).__init__('Point?crs=epsg:4326', self._layerName, "memory")

        # metadata
        self.setAttribution('Radiation Toolbox Plugin')
        self.setAttributionUrl('https://opengeolabs.gitlab.io/radiation-toolbox/qgis-radiation-toolbox-plugin/')

        self._aliases = [] # list of attribute aliases
        self._provider = self.dataProvider()

        # import errors
        self._errs = {}

        # layer is empty, no data loaded
        self.reader = None

        # layer type not defined
        self.layerType = None

        # style
        self._style = Style()
        self._renderer = None

    @property
    def metadata(self):
        """Return layer metadata derived from reader.
        """
        return self.reader.metadata

    def load(self, reader):
        """Load input data by specified reader.

        :param reader: reader class used for reading input data
        """
        if self.reader:
            return # data already loaded

        # data loaded (avoid multiple imports)
        self.reader = reader

        # create progress bar widget
        progressMessageBar = iface.messageBar().createMessage(
            self.tr("Loading data...")
        )
        progress = QtWidgets.QProgressBar()
        progress.setMaximum(100)
        progressMessageBar.layout().addWidget(progress)
        iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)

        # load items as new point features (inform user about progress)
        i = 0
        count = reader.count()
        start = time.perf_counter()
        prev = None # previous feature

        self._aliases = self._setAttrbsDefs(reader)

        self.startEditing()
        for item in reader:
            i += 1

            feat = self._rec2feat(item)
            if not feat:
                # error appeared
                continue
            feat.setId(i)
            self.addFeature(feat)

            if i % 100 == 0:
                percent = i * 100 // count
                progress.setValue(percent)

        # add features (attributes recalculated if requested)
        self.commitChanges()

        if self.storageFormat != "memory":
            self._writeToOgrDataSource()
            self.reload()

        # finish import
        endtime = time.perf_counter() - start
        progress.setValue(100)
        iface.messageBar().clearWidgets()

        if self._errs:
            # report errors if any
            iface.messageBar().pushMessage(
                self.tr("Info"),
                self.tr("{} invalid measurement(s) skipped (see message log for details)").format(
                    sum(self._errs.values())
                ),
                level=Qgis.Info,
                duration=5
            )

            for attr in list(self._errs.keys()):
                QgsMessageLog.logMessage(
                    "{}: {} measurement(s) skipped (invalid {})".format(
                        self._fileName, self._errs[attr], attr
                    ),
                    tag="Radiation Toolbox"
                )
        
        # inform user about successful import
        iface.messageBar().pushMessage(
            self.tr("Data loaded"),
            self.tr("{} features loaded (in {:.2f} sec).").format(self.featureCount(), endtime),
            level=Qgis.Success,
            duration=3
        )

        # switch to read-only mode
        self.setReadOnly(True)

    def _writeToOgrDataSource(self):
        filePath = Path(self._fileName).with_suffix('.' + self.storageFormat.lower())
        try:
            self.reader.export(filePath, self.storageFormat, overwrite=True)
        except ReaderExportError as e:
            raise LoadError(
                self.tr("Unable to create SQLite datasource: {}").format(e)
            )

        # set datasource to new OGR datasource
        self.setDataSource(str(filePath), self._layerName, 'ogr')
        self._provider = self.dataProvider()

    def _addError(self, etype):
        """Add error message.

        :param etype: error type (HDOP, SAT, ...)
        """
        if etype not in self._errs:
            self._errs[etype] = 0
        self._errs[etype] += 1

    def _rec2feat(self, record):
        """Create QgsFeature from data item.
        """
        raise NotImplementedError()

    def _setAttrbsDefs(self, reader):
        """Set attributes definition from CSV file if available.

        :param reader: Reader object

        :returns: list of aliases
        """
        def dtype2qtype(dtype):
            return {
                int: "Int",
                float: "Double",
                str: "String"
            }[dtype]
        
        attrbs = []
        aliases = []
        for name, meta in reader.attributeDefs().items():
            attrbs.append(QgsField(
                name, eval("QVariant.{}".format(dtype2qtype(meta['type'])))
            ))
            if meta.get('alias'):
                aliases.append(meta['alias'].replace('_', ' '))

        if aliases and self.storageFormat != "memory":
            aliases.insert(0, "FID")

        # set attributes
        self._provider.addAttributes(attrbs)
        self.updateFields()

        return aliases

    def setAliases(self):
        """Set aliases
        """
        for i in range(0, len(self._aliases)):
            self.setFieldAlias(i, self._aliases[i])

    def setStyle(self, idx):
        """Set layer style.

        :param int idx: style (combobox) index
        """
        try:
            style = self._style[idx]
        except (IndexError, KeyError):
            return None
        if 'file' in style:
            # QML style
            stylePath = style['file']
            if not os.path.isfile(stylePath):
                raise StyleError(
                    self.tr("Style '{}' not found").format(stylePath
            ))
            self.loadNamedStyle(stylePath)
        elif 'colorramp' in style:
            if not self._renderer:
                # symbol (store transparent)
                symbol = QgsSymbol.defaultSymbol(self.geometryType())
                symbol.symbolLayer(0).setStrokeColor(
                    QColor("transparent")
                )

                # renderer
                self._renderer = QgsGraduatedSymbolRenderer()
                self._renderer.setSourceSymbol(symbol)
                self._renderer.setClassAttribute(style['attribute'])
                self._renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
                self._renderer.updateClasses(
                    self, QgsGraduatedSymbolRenderer.EqualInterval,
                    style['classes']
                )
                self.setRenderer(self._renderer)

            self._renderer.updateColorRamp(
                style['colorramp']
            )
        else:
            raise StyleError(
                self.tr("Undefined style")
            )

    def style(self):
        """Get style.

        :return: style class
        """
        return self._style
