FROM debian:stable-slim AS updated-base

ARG VARIANT=${VARIANT:-full}
COPY ${VARIANT}/build.env /tmp/
COPY --chmod=0755 scripts/* /sbin/
COPY files/ /files/

RUN set -eu; \
    apt-get update; \
    apt-get dist-upgrade -y --autoremove; \
    apt-get autoremove -y \
        --purge \
        -o APT::AutoRemove::RecommendsImportant=false; \
    apt-get -y clean; \
    rm -rf /var/lib/apt/lists/*


FROM scratch
COPY --from=updated-base / /

# Environment variables
ENV TZ="Etc/UTC"
ENV CUPSADMIN="admin"
ENV CUPSPASSWORD="__cUPsPassw0rd__"

LABEL org.opencontainers.image.source="https://github.com/infra7ti/docker-cups"
LABEL org.opencontainers.image.description="Common Unix Print Server (CUPS)"
LABEL org.opencontainers.image.author="Infra7 Serviços em TI"
LABEL org.opencontainers.image.url="https://github.com/infra7ti/docker-cups/blob/main/README.md"
LABEL org.opencontainers.image.licenses=MIT

# Needed for source shell functions into this Dockerfile
SHELL ["/bin/bash", "-c"]

RUN set -eu; \
    source /tmp/build.env; \
    apt-get update; \
    apt-mark showmanual > /tmp/installed-manual.list; \
    \
    # install packages \
    echo "${PACKAGES}" | xargs \
        apt-get install -y \
            --no-install-recommends \
            --no-install-suggests; \
    \
    # Compile and install foo2zjs (debian package is buggy) \
    [ "${VARIANT}" == "full" ] && __compile_foo2zjs; \
    # Override CUPS templates to use bootstrap Web UI \
    __override_templates; \
    # Baked-in config file changes \
    __configure_cups; \
    # Backup cups config in case used does not add their own \
    __backup_cups; \
    # Cleanup build dependencies and temporary files \
    comm -13 /tmp/installed-manual.list <(apt-mark showmanual) \
        | xargs -r apt-get purge -y --auto-remove; \
    apt-get autoremove -y \
        --purge \
        -o APT::AutoRemove::RecommendsImportant=false; \
    apt-get -y clean; \
    rm -rf /tmp/build.env /tmp/files /tmp/installed-manual.list

EXPOSE 631
EXPOSE 5353/udp

VOLUME [ "/etc/cups" ]

ENTRYPOINT ["/sbin/entrypoint"]
CMD ["/usr/sbin/cupsd","-f"]
