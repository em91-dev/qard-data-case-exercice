#!/bin/bash

cd $(dirname ${0})

DOCKER_COMMAND="$*"
if [ "$DOCKER_COMMAND" = "" ] ; then
    DOCKER_COMMAND="/bin/bash -c "source activate sparkenv && python /src/app.py"
fi

docker run -it --rm \
      -v $PWD/qard-data-case:/qard-data-case \
      -v $PWD/db:/db \
      -v $PWD/src:/src \
      -v $PWD/out:/out \
      --name spark_ocr spark \
      $DOCKER_COMMAND
