FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.20.7
ENV PATH="/usr/local/go/bin:/root/go/bin:$PATH"

# Install base packages
RUN apt update && apt install -y \
    curl wget unzip git python3 python3-pip build-essential \
    libpcap-dev dnsutils python3-dnspython jq

# Install Go
RUN curl -OL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/bin/go && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

# Install Subdomain Enumeration Tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/tomnomnom/assetfinder@latest && \
    go install -v github.com/owasp-amass/amass/v4/...@latest && \
    ln -s /root/go/bin/subfinder /usr/bin/subfinder && \
    ln -s /root/go/bin/assetfinder /usr/bin/assetfinder && \
    ln -s /root/go/bin/amass /usr/bin/amass

# Install findomain (precompiled binary)
RUN wget https://github.com/findomain/findomain/releases/latest/download/findomain-linux -O /usr/bin/findomain && \
    chmod +x /usr/bin/findomain

# Copy requirements first
COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

# Copy rest of project
COPY . /app

CMD ["python3", "main.py"]
