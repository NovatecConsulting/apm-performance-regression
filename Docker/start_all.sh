#!/bin/bash

sudo chmod -R 777 jenkins
docker-compose up -d

sleep 10s
sudo cp inspectit/businessContext.xml inspectit_cmr/ci/businessContext.xml
sudo cp inspectit/default.xml inspectit_cmr/config/default.xml
docker restart inspectit_cmr
xdg-open http://localhost:3000
xdg-open http://localhost:8090
open http://localhost:3000
open http://localhost:8090