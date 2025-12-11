FROM flink:1.18.1-java11

# Install Python 3.10 and pip
# The base image is Debian-based (bullseye usually for 1.18)
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

# Install Producer dependencies
RUN pip3 install kafka-python websocket-client streamlit pandas requests

# Install PyFlink (Optional but good for local dev/submitter if not using the bundled one)
# Note: The provided Flink image has PyFlink libs in /opt/flink/opt/python usually, 
# but installing via pip ensures the python environment has it for the submitter script if it imports it.
# However, 'flink run' uses the bundled flink dist. 
# We'll just stick to the producer deps for now to keep it light, unless processor.py needs them.

WORKDIR /opt/flink
