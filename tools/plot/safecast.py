"""
/***************************************************************************
                             A QGIS Safecast Plugin
                             ----------------------
        begin                : 2016-05-25
        git sha              : $Format:%H$
        copyright            : (C) 2016-2018 by OpenGeoLabs s.r.o.
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
import matplotlib
matplotlib.use('QtAgg')

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)

        # variables used throughout the graph
        self.pressed = False

        super(MplCanvas, self).__init__(fig)

        # zoom event
        self.mpl_connect('scroll_event', self.zoom)

        # pan events
        self.mpl_connect('button_press_event', self.onPress)
        self.mpl_connect('button_release_event', self.onRelease)
        self.mpl_connect('motion_notify_event', self.onMotion)

    def update_graph(self, layer, style): # , layer=None, style=None):
        """Update plot for given Safecast layer.

        :param layer: Safecast layer
        """
        if layer is not None:
            self.layer = layer
        # collect plot coordinates
        x, y = self.layer.plotData()

        self.axes.clear()

        plt_kwargs = {'label': self.layer.filename()}
        if style == 1:  # points
            plt_kwargs.update({'linestyle': 'None', 'marker': '+'})
        else:  # lines
            plt_kwargs.update({'linestyle': 'solid', 'linewidth': 0.7})

        self.axes.plot(x, y, **plt_kwargs)
        self.axes.grid(color='green', linestyle='--', linewidth=0.3)
        self.axes.set_xlabel(self.tr("Distance (km)"))
        self.axes.set_ylabel(self.tr("ADER (microSv/h)"))
        self.draw()

    def zoom(self, event):
        """Zoom the image upon scrolling the mouse wheel.

        Scrolling it in the plot zooms the plot. Scrolling above or below the
        plot scrolls the x axis. Scrolling to the left or the right of the plot
        scrolls the y axis. Where it is ambiguous nothing happens."""
        zoom_scale = 1.1

        x = event.x
        y = event.y
        xdata = event.xdata
        ydata = event.ydata

        # convert pixels to axes
        tranP2A = self.axes.transAxes.inverted().transform
        # convert axes to data limits
        tranA2D = self.axes.transLimits.inverted().transform
        # convert the scale (for log plots)
        tranSclA2D = self.axes.transScale.inverted().transform

        if event.button == 'down':
            # deal with zoom in
            scale_factor = zoom_scale
        elif event.button == 'up':
            # deal with zoom out
            scale_factor = 1 / zoom_scale
        else:
            # deal with something that should never happen
            scale_factor = 1

        # get my axes position to know where I am with respect to them
        xa, ya = tranP2A((x, y))

        # fallback values (should always be defined in the following if clauses)
        zoomx = False
        zoomy = False

        if (ya < 0):
            if (xa >= 0 and xa <= 1):
                zoomx = True
                zoomy = False
                xdata = tranSclA2D(tranA2D((0.5, 0.5)))[0]
        elif (ya <= 1):
            if (xa < 0):
                zoomx = False
                zoomy = True
                ydata = tranSclA2D(tranA2D((0.5, 0.5)))[1]
            elif (xa <= 1):
                zoomx = True
                zoomy = True
            else:
                zoomx = False
                zoomy = True
                ydata = tranSclA2D(tranA2D((0.5, 0.5)))[1]
        else:
            if (xa >= 0 and xa <= 1):
                zoomx = True
                zoomy = False
                xdata = tranSclA2D(tranA2D((0.5, 0.5)))[0]

        # set new limits
        if zoomx is True:
            new_xl = xdata - scale_factor * (xdata - self.axes.get_xlim()[0])
            new_xr = xdata + scale_factor * (self.axes.get_xlim()[1] - xdata)
            # set limits
            self.axes.set_xlim([new_xl, new_xr])
        if zoomy is True:
            new_yl = ydata - scale_factor * (ydata - self.axes.get_ylim()[0])
            new_yr = ydata + scale_factor * (self.axes.get_ylim()[1] - ydata)
            # set limits
            self.axes.set_ylim([new_yl, new_yr])

        # replot the graph
        self.draw()

    def onPress(self, event):
        """Save coordinates of the click."""
        if event.inaxes != self.axes:
            return

        self.cur_xlim = self.axes.get_xlim()
        self.cur_ylim = self.axes.get_ylim()

        self.pressed = True
        self.xpress = event.xdata
        self.ypress = event.ydata

    def onRelease(self, event):
        """Draw the graph."""
        self.pressed = False
        self.draw()

    def onMotion(self, event):
        """Pan the graph."""
        if self.pressed is False:
            return
        if event.inaxes != self.axes:
            return

        dx = event.xdata - self.xpress
        dy = event.ydata - self.ypress
        self.cur_xlim -= dx
        self.cur_ylim -= dy

        self.axes.set_xlim(self.cur_xlim)
        self.axes.set_ylim(self.cur_ylim)

        self.draw()
