#!/bin/bash
# Render RMR routes template

TEMPLATE_FILE="configs/routes.rt.template"
OUTPUT_FILE="configs/routes.rt"

# Default values if not set
export E2TERM_SERVICE=${E2TERM_SERVICE:-"service-ricplt-e2term-rmr-alpha.ricplt:38000"}
export SUBMGR_SERVICE=${SUBMGR_SERVICE:-"service-ricplt-submgr-rmr.ricplt:4560"}
export RDL_SERVICE=${RDL_SERVICE:-"service-ricxapp-iqos-xapp-rdl-rmr.ricxapp:4560"}

# Use envsubst to render
envsubst < $TEMPLATE_FILE > $OUTPUT_FILE
echo "Routes rendered to $OUTPUT_FILE"
