# Start from a base image with Go and Python
FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.22.3

# --- Install dependencies ---
RUN apt update && apt install -y \
    curl wget unzip git python3 python3-pip build-essential \
    libpcap-dev dnsutils

# Install latest Go
RUN curl -OL https://go.dev/dl/go1.20.7.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.20.7.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/bin/go && \
    go version

ENV PATH="/usr/local/go/bin:/root/go/bin:$PATH"

# --- Install subdomain tools ---
RUN go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
RUN go install github.com/projectdiscovery/httpx/cmd/httpx@latest && \
RUN go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
RUN go install github.com/tomnomnom/assetfinder@latest

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

# Clone ParamSpider
RUN git clone https://github.com/devanshbatham/ParamSpider.git /ParamSpider

# Set PYTHONPATH and working directory for ParamSpider
ENV PYTHONPATH=/ParamSpider
ENV PARAMSPIDER_PATH=/ParamSpider

# Install Gau (Go tool)
RUN wget https://github.com/lc/gau/releases/download/v2.2.1/gau_2.2.1_linux_amd64.tar.gz && \
    tar -xzf gau_2.2.1_linux_amd64.tar.gz && \
    mv gau /usr/local/bin/ && \
    rm -rf gau_2.2.1_linux_amd64.tar.gz LICENSE README.md

# Install Waybackurls (Go tool)
RUN go install github.com/tomnomnom/waybackurls@latest && \
    cp /root/go/bin/waybackurls /usr/local/bin/

# Install Arjun (Python tool)
RUN git clone https://github.com/s0md3v/Arjun.git /Arjun && \
    cd /Arjun && \
    pip install -r requirements.txt

# Copy Go binaries to /usr/local/bin
RUN cp /root/go/bin/* /usr/local/bin/

# --- Copy project files ---
WORKDIR /app
COPY . /app

# --- Install Python dependencies ---
RUN pip3 install --no-cache-dir -r requirements.txt

# --- Run the app ---
CMD ["python3", "main.py"]
