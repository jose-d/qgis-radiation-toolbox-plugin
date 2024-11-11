import os
import sys

from qgis.core import QgsFeature, QgsPointXY, QgsGeometry
 
from . import LayerBase, LayerType
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from style.ers import ERSStyle

class ERSLayer(LayerBase):
    def __init__(self, fileName, storageFormat):
        """ERS memory-based read-only layer.

        :param fileName: path to input file
        :param storageFormat: storage format for layer (Memory or SQLite)
        """
        super(ERSLayer, self).__init__(fileName, storageFormat)

        # layer type
        self.layerType = LayerType.ERS

        # style
        self._style = ERSStyle()

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
