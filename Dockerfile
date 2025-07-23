FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.23.11
ENV PATH="/usr/local/go/bin:/root/go/bin:$PATH"

# Install dependencies
RUN apt update && apt install -y \
    curl wget unzip git python3 python3-pip build-essential \
    libpcap-dev dnsutils python3-dnspython jq

# Install Go 1.23.0
RUN curl -OL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/bin/go && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

# Install Subdomain Enumeration Tools
RUN go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install github.com/tomnomnom/assetfinder@latest && \
    go install github.com/owasp-amass/amass/v4/...@latest && \
    ln -s /root/go/bin/subfinder /usr/bin/subfinder && \
    ln -s /root/go/bin/assetfinder /usr/bin/assetfinder && \
    ln -s /root/go/bin/amass /usr/bin/amass

# Install findomain binary
RUN wget https://github.com/findomain/findomain/releases/download/9.0.4/findomain-linux-amd64 -O /usr/bin/findomain && \
    chmod +x /usr/bin/findomain

# Copy Python requirements
COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

# Copy rest of project
COPY . /app

CMD ["python3", "main.py"]
