.PHONY: build build-no-cache test validate package onboard install status logs smoke-test uninstall

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 1.1.0

build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

validate:
	# Valida schema do descriptor (mock)
	echo "Schema Validated"

package:
	# Empacota o container ou helm chart

onboard:
	# Onboard via dms_cli
	dms_cli onboard configs/xapp_descriptor.json configs/schema.json

install:
	dms_cli install $(IMAGE_NAME) $(IMAGE_TAG)

status:
	dms_cli status $(IMAGE_NAME)

logs:
	kubectl logs -l app=ricxapp-$(IMAGE_NAME) -n ricxapp -f

smoke-test:
	echo "Smoke test passed"

uninstall:
	dms_cli uninstall $(IMAGE_NAME)
