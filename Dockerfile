# Start from a base image with Go and Python
FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.22.3

# --- Install dependencies ---
RUN apt update && apt install -y \
    curl wget unzip git python3 python3-pip build-essential \
    libpcap-dev dnsutils

# --- Install Go ---
RUN curl -LO https://golang.org/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    echo "export PATH=$PATH:/usr/local/go/bin" >> /etc/profile && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:/root/go/bin:$PATH"

# --- Install subdomain tools ---
RUN go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
    go install github.com/tomnomnom/assetfinder@latest

# --- Install cero ---
RUN git clone https://github.com/glebarez/cero && \
    cd cero && go build -o cero . && mv cero /usr/local/bin && cd .. && rm -rf cero

# --- Install shosubgo ---
RUN git clone https://github.com/incogbyte/shosubgo && \
    cd shosubgo && go build -o shosubgo . && mv shosubgo /usr/local/bin && cd .. && rm -rf shosubgo

# --- Install Subjack ---
RUN go install github.com/haccer/subjack@latest

# --- Install BadDNS ---
RUN git clone https://github.com/m4ll0k/Bug-Bounty-Toolz && \
    cp -r Bug-Bounty-Toolz/Subdomain\ Takeover/BadDNS /opt/baddns && \
    chmod +x /opt/baddns/baddns.py && \
    ln -s /opt/baddns/baddns.py /usr/local/bin/baddns && \
    apt install -y python3-dnspython && \
    rm -rf Bug-Bounty-Toolz

# --- Copy project files ---
WORKDIR /app
COPY . /app

# --- Install Python dependencies ---
RUN pip3 install --no-cache-dir -r requirements.txt

# --- Run the app ---
CMD ["python3", "main.py"]
