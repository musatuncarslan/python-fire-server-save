# ----- First stage to build ismrmrd and siemens_to_ismrmrd -----
FROM python:3.10.2-slim AS mrd_converter
ARG  DEBIAN_FRONTEND=noninteractive
ENV  TZ=America/Chicago

# Python Dependencies from the requirements.txt file
WORKDIR /usr/local/lib/
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt


#FROM ubuntu:20.04
#ARG DEBIAN_FRONTEND=noninteractive
FROM python:3.10.2-slim

# Copy /usr/local/lib/ which includes additional python libraries from the previous stage
COPY --from=mrd_converter /usr/local/lib/ /usr/local/lib/

# Copy local code to the appropriate palce inside the image
RUN mkdir -p /opt/code/python-fire-server-base \
	&& mkdir -p /opt/code/python-fire-server-base/doc \
	&& mkdir -p /opt/code/python-fire-server-base/docker \
	&& mkdir -p /opt/code/python-fire-server-base/.vscode .
COPY ./ /opt/code/python-fire-server-base

# Ensure startup scripts are marked as executable, which may be lost if files
# are copied in Windows
RUN find /opt/code/python-fire-server-base -name *.sh -exec chmod +x {} \;

# Set the starting directory so that code can use relative paths
WORKDIR /opt/code/python-fire-server-base

CMD [ "python3", "/opt/code/python-fire-server-base/main.py", "-v", "-H", "0.0.0.0", "-p=9003", "-l", "/opt/code/python-fire-server-base/logs/python-fire-server-base.log", "-s", "/opt/code/python-fire-server-base/save/" ]