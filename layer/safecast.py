"""
/***************************************************************************
                             A QGIS Safecast Plugin
                             ----------------------
        begin                : 2016-05-25
        git sha              : $Format:%H$
        copyright            : (C) 2016-2024 by OpenGeoLabs s.r.o.
        acknowledgement      : Suro, Czech Republic
        email                : martin.landa@opengeolabs.cz
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import sys
import time
from datetime import datetime, timedelta, date
from dateutil import tz

from PyQt5.QtWidgets import QProgressBar

from qgis.core import QgsVectorLayer, QgsField, QgsFeature, \
    QgsGeometry, QgsPointXY, QgsFields, \
    QgsCoordinateReferenceSystem, QgsMessageLog, QgsDistanceArea, edit
from qgis.utils import iface, Qgis

from osgeo import ogr

from . import LayerBase, LayerType
from .exceptions import LoadError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from style.safecast import SafecastStyle

from radiation_toolbox_reader import ComputedAttributes
from radiation_toolbox_reader.safecast import SafecastRecord

class SafecastWriterError(Exception):
    """Safecast writer error class.
    """
    pass

class SafecastLayer(LayerBase):
    fieldOrder = [
        'ogc_fid', 'ader_microsvh', 'time_local', 'speed_kmph',
        'dose_increment', 'time_cumulative', 'dose_cumulative', 'dist_cumulative',
        'device', 'device_id', 'date_time', 'cpm', 'pulses5s',
        'pulses_total', 'validity', 'lat_deg', 'hemisphere',
        'long_deg', 'east_west', 'altitude', 'gps_validity',
        'sat', 'hdop', 'checksum'
    ]

    def __init__(self, fileName, storageFormat):
        """Safecast memory-based read-only layer.

        :param fileName: path to input file
        :param storageFormat: storage format for layer (Memory or SQLite)
        """
        super(SafecastLayer, self).__init__(fileName, storageFormat)

        # layer type
        self.layerType = LayerType.Safecast

        # style
        self._style = SafecastStyle()

    def load(self, reader):
        """Load LOG file using specified reader.

        LoadError is raised on failure.

        :param reader: reader class used for reading input data
        """
        super(SafecastLayer, self).load(reader)

    def _rec2feat(self, record):
        """Process line in LOG file and create a new point feature based on this line.

        :param record: record to be processed
        """
        x, y = record.point

        # drop data according
        if int(record['hdop']) == 9999:
            self._addError('HDOP = 9999')
            return None
        if int(record['sat']) < 3:
            self._addError('SAT < 3')
            return None
        ### Date validity will be performed when whole file loaded
        # - year (record[2])
        # myear = datetime2year(record[2])
        # minyear = 2011
        # maxyear = datetime.now().year
        # if myear < minyear or myear > maxyear:
        #     self._addError('year <> {0}-{1}'.format(
        #         minyear, maxyear
        #     ))
        #     return None

        # check timestamp (hours only, dates are fixed when
        # recalculating attributes) validity
        try:
            datetime.strptime(record['date_time'].split('T', 1)[1], "%H:%M:%SZ")
        except ValueError as e:
            self._addError('invalid timestamp {}'.format(record['date_time']))
            return None

        # - null island
        if abs(x) < sys.float_info.epsilon or \
           abs(y) < sys.float_info.epsilon:
            self._addError('null island')
            return None

        # create new feature
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))

        # set attributes
        feat.setAttributes(list(record.values()))

        return feat

class SafecastLayerHelper(object):
    def __init__(self, layer):
        self._layer = layer
        if isinstance(layer, SafecastLayer):
            self._storageFormat = layer.storageFormat
            self._skipNumAttrbs = 6 if self._storageFormat == 'memory' else 7
            self._fileName = layer._fileName
        else:
            # assuming SQLite
            self._storageFormat = "SQLite"
            # better to be stored in metadata than hardcoded
            self._skipNumAttrbs = 7
            self._fileName = layer.dataProvider().dataSourceUri().split('|')[0]

        # ader statistics
        self._updateStats()

        # ader plot
        self._plot = [[], []]

        # connects
        # self._layer.beforeCommitChanges.connect(self.recalculateAttributes)

    def path(self):
        """Return layer file directory path.

        :return: path as a string
        """
        return os.path.dirname(self._fileName)

    def filename(self):
        """Return layer file name without extension.

        :return: filename as a string
        """
        return os.path.splitext(
            os.path.basename(self._fileName)
        )[0]

    def _gpsChecksum(self, item):
        """Compute checksum of item.

        :param item: item line

        :return: checksum
        """
        chk = ord(item[0])

        for ichk in item[1:]:
            chk ^= ord(ichk)

        return hex(chk)[2:].upper()

    def _getMetadata(self):
        """Get metadata."""
        if isinstance(self._layer, SafecastLayer):
            return self._layer.metadata

        metadata = {}
        try:
            ds = ogr.Open(self._fileName)
            layer = ds.GetLayerByName('safecast_metadata')
            if layer:
                layer_defn = layer.GetLayerDefn()
                layer.ResetReading()
                feat = layer.GetNextFeature()
                for i in range(layer_defn.GetFieldCount()):
                    name = layer_defn.GetFieldDefn(i).GetName()
                    value = feat.GetField(i)
                    metadata[name] = value
            ds = None
        except:
            raise LoadError(
                self.tr("Unable to retrive Safecast metadata for selected layer")
            )

        return metadata
        
    def save(self, filePath):
        """Save layer to a new LOG file.

        Raises SafecastWriterError on failure.

        :param filePath: name for output file
        """
        columns = []
        blacklist = ['checksum']
        for name, meta in self._layer.reader.attributeDefs().items():
            if meta['computed'].value < ComputedAttributes.PerRecordOnly.value and name not in blacklist:
                columns.append(name)
        try:
            with open(filePath, 'w', newline='\r\n') as f:
                f.write('# NEW LOG\n')
                metadata = self._getMetadata()
                f.write('# format={}\n'.format(metadata['columns']['format']))
                f.write('# deadtime={}\n'.format(metadata['columns']['deadtime']))
                features = self._layer.getFeatures()
                for feat in features:
                    attrs = feat.attributeMap()
                    record = ','.join([
                        f'{attrs[name]:.2f}' if isinstance(attrs[name], float) else str(attrs[name])
                        for name in columns
                    ])
                    # join two last columns(hdop+checksum)
                    checksum = self._gpsChecksum(record[1:]) # skip '$'
                    f.write(record + f'*{checksum}\n')
        except IOError as e:
            raise SafecastWriterError(e)

    def _updateStats(self, data=None):
        """Update ader statistics.

        :param ader: ader statistics
        """
        if data:
            self._stats = data
        else:
            self._stats = {
                'count' : 0,
                'radiation': {
                    'max' : None,
                    'avg' : None,
                    'total': None,
                },
                'route': {
                    'speed' : None,
                    'time': None,
                    'distance' : None,
                }
            }

    def statsData(self):
        """Get layer statistics"""
        return self._stats

    def plotData(self):
        return self._plot

    def recalculateAttributes(self):
        """Update attributes on editing.
        """
        # collect attributes to be recomputed
        field_idx = {}
        for name, meta in self._layer.reader.attributeDefs().items():
            if meta['computed'].value > ComputedAttributes.PerRecordOnly.value:
                field_idx[name] = self._layer.dataProvider().fieldNameIndex(name)

        # update reader records based on QGIS features
        records = []
        fields = self._layer.fields()
        features = self._layer.getFeatures()
        for feat in features:
            values = feat.attributes()
            records.append(SafecastRecord((fields[i].name(), values[i]) for i in range(len(values))))

        # recompute attributes
        start = time.perf_counter()
        self._layer.reader.computeAttributes(records)

        updated_attrs = {}
        for idx, feat in enumerate(features):
            updated_attrs[feat.id()] = {idx: records[idx][name] for name, idx in field_idx.items()}

        self._layer.setReadOnly(False)
        self._layer.startEditing()
        # with edit(self._layer) returns AssertationError - why?
        self._layer.dataProvider().changeAttributeValues(updated_attrs)
        self._layer.commitChanges()
        self._layer.setReadOnly(True)

        # force reload attributes
        self._layer.dataProvider().reloadData()

        # update stats & plot data
        self.computeStatsPlot()

        QgsMessageLog.logMessage(
            '{0}: {1} features updated in {2:.2f} sec'.format(
                self._layer.name(), self._layer.featureCount(), time.perf_counter() - start),
            tag="Radiation Toolbox",
            level=Qgis.Info
        )

    def computeStatsPlot(self):
        # update layer internal statistics
        stats = self._layer.reader.stats()
        self._updateStats(stats)

        # update layer internal plot data
        self._plot = [[], []]
        dist_cum = stats['route']['distance']
        for rec in self._layer.reader:
            self._plot[0].append(rec["dist_cumulative"] / 1000) # km
            self._plot[1].append(rec["ader_microsvh"])

        # release reader resources
        self._layer.reader.release()
