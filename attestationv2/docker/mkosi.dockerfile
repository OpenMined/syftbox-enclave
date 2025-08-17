FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime
    

# Install deps for key handling and mkosi itself
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg systemd-ukify

# Setup mkosi
RUN echo 'deb http://download.opensuse.org/repositories/system:/systemd/Ubuntu_24.04/ /' | tee /etc/apt/sources.list.d/system:systemd.list && \
    curl -fsSL https://download.opensuse.org/repositories/system:systemd/Ubuntu_24.04/Release.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/system_systemd.gpg > /dev/null && \
    apt install mkosi -y

# Nice-to-have default working dir you can bind-mount your project into
WORKDIR /work

# Default to a shell if no command is passed
CMD ["/bin/bash"]
