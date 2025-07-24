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

# Install base deps
RUN apt-get update && apt-get install -y git curl python3-pip

# Install subjack
RUN go install github.com/haccer/subjack@latest && \
    mkdir -p /usr/share/subjack && \
    curl -o /usr/share/subjack/fingerprints.json https://raw.githubusercontent.com/haccer/subjack/master/fingerprints.json && \
    ln -s /root/go/bin/subjack /usr/bin/subjack

# Install dnsx
RUN go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest && \
    ln -s /root/go/bin/dnsx /usr/bin/dnsx
    
# --- Install Go-based tools ---
RUN go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install github.com/tomnomnom/assetfinder@latest && \
    go install github.com/owasp-amass/amass/v4/...@latest && \
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install github.com/haccer/subjack@latest && \
    ln -sf /root/go/bin/subfinder /usr/bin/subfinder && \
    ln -sf /root/go/bin/assetfinder /usr/bin/assetfinder && \
    ln -sf /root/go/bin/amass /usr/bin/amass && \
    ln -sf /root/go/bin/httpx /usr/bin/httpx && \
    ln -sf /root/go/bin/subjack /usr/bin/subjack


# --- Install cero ---
RUN git clone https://github.com/glebarez/cero.git /opt/cero && \
    cd /opt/cero && go build && \
    mv cero /usr/bin/ && chmod +x /usr/bin/cero

# --- Install shosubgo ---
RUN git clone https://github.com/incogbyte/shosubgo.git /opt/shosubgo && \
    cd /opt/shosubgo && go build -o shosubgo main.go && \
    mv shosubgo /usr/bin/shosubgo && chmod +x /usr/bin/shosubgo
    
# Install gau and waybackurls using go
RUN go install github.com/lc/gau/v2/cmd/gau@latest && \
    go install github.com/tomnomnom/waybackurls@latest && \
    ln -s /root/go/bin/gau /usr/bin/gau && \
    ln -s /root/go/bin/waybackurls /usr/bin/waybackurls

# Install Arjun (no requirements.txt needed)
RUN git clone https://github.com/s0md3v/Arjun.git /opt/Arjun && \
    ln -s /opt/Arjun/arjun /usr/bin/arjun && \
    chmod +x /opt/Arjun/arjun/__main__.py

# Install ParamSpider (Python tool)
RUN git clone https://github.com/devanshbatham/ParamSpider.git /opt/ParamSpider && \
    pip install requests urllib3 && \
    ln -s /opt/ParamSpider/paramspider /usr/bin/paramspider && \
    chmod +x /opt/ParamSpider/paramspider/main.py

# Install Findomain (9.0.3)
RUN wget https://github.com/findomain/findomain/releases/download/9.0.3/findomain-linux.zip -O /tmp/findomain.zip && \
    unzip /tmp/findomain.zip -d /tmp/ && \
    mv /tmp/findomain /usr/bin/findomain && \
    chmod +x /usr/bin/findomain && \
    rm /tmp/findomain.zip


# Copy Python requirements
COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

# Copy rest of project
COPY . /app

CMD ["python3", "main.py"]
