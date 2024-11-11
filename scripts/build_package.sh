#!/bin/bash -e

VENV=/tmp/radiation_toolbox_plugin
python3 -m venv $VENV
source $VENV/bin/activate

script_dir=$(realpath $(dirname $0))
### install released SMODERP2D version
# pip3 install radiation-toolbox-reader
### or from git
(cd ${script_dir}/../../radiation-toolbox-reader ;pip3 install . gdal==3.9.3)

pv=$(python3 -V | cut -d' ' -f 2 | cut -d'.' -f 1,2)
LIB=$VENV/lib/python$pv/site-packages

pb_tool deploy -y -p zip_build/

plugin_name=radiation_toolbox_plugin
plugin_dir=zip_build/$plugin_name
cp -r $LIB/radiation_toolbox_reader $plugin_dir/

# clean-up
find $plugin_dir/radiation_toolbox_reader -name __pycache__ | xargs rm -rf
find $plugin_dir/ -name __pycache__ | xargs rm -rf

# pb_tool zip
(cd zip_build; zip -r $plugin_name.zip $plugin_name) # pb_tool zip will overwrite python package

deactivate
rm -rf $VENV

exit 0
