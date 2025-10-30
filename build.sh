#!/bin/bash

case $1 in
    proxy)
        docker buildx build \
	    --build-arg VARIANT=proxy \
	    --platform amd64,arm64 \
	    -t infra7/cups:2.4.10-proxy \
	    -t infra7/cups:2.4-proxy \
	    -t infra7/cups:latest-proxy \
	    --push . ;;
    full|*)
        docker buildx build \
	    --build-arg VARIANT=full \
	    --platform amd64,arm64 \
	    -t infra7/cups:2.4.10 \
	    -t infra7/cups:2.4 \
	    -t infra7/cups:latest \
	    --push . ;;
esac

exit $?
