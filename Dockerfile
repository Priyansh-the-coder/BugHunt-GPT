FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.20.7
ENV PATH="/usr/local/go/bin:/root/go/bin:$PATH"

RUN apt update && apt install -y \
    curl wget unzip git python3 python3-pip build-essential \
    libpcap-dev dnsutils python3-dnspython

RUN curl -OL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/bin/go && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

# Copy requirements first
COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

# Copy rest of project
COPY . /app

CMD ["python3", "main.py"]
