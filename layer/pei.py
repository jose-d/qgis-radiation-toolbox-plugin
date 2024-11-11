from qgis.core import QgsFeature, QgsPointXY, QgsGeometry

from . import LayerBase, LayerType
from style.pei import PEIStyle

class PEILayer(LayerBase):
    def __init__(self, fileName, storageFormat):
        """ERS memory-based read-only layer.

        :param fileName: path to input file
        :param storageFormat: storage format for layer (Memory or SQLite)
        """
        super(PEILayer, self).__init__(fileName, storageFormat)

        # layer type
        self.layerType = LayerType.PEI

        # style
        self._style = PEIStyle()

    def _rec2feat(self, record):
        """Create QgsFeature from data record.
        """
        feat = QgsFeature()

        # set geometry
        feat.setGeometry(
            QgsGeometry.fromPointXY(QgsPointXY(*record.point))
        )

        # set attributes
        feat.setAttributes(list(record.values()))

        return feat


    def _setShownFields(self, fields):
        """Set shown fields.

        :param list fields: list of fields
        """
        config = self.attributeTableConfig()
        columns = config.columns()
        for column in columns:
            if column.name.lower() not in fields:
                column.hidden = True
        config.setColumns(columns)
        self.setAttributeTableConfig(config)

    def load(self, reader):
        super(PEILayer, self).load(reader)

        # to be fixed
        # with open(self._attributesCSVFile()) as fd:
        #     fields = list(map(lambda x: x.lower(), fd.read().splitlines()))
        #     self._setShownFields(fields)

    def formatType(self):
        field_names = [field.name().lower() for field in self.fields()]
        return 'MobDose' if 'fastdose' in field_names else 'IRIS'
