FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV GO_VERSION=1.23.11
ENV PATH="/usr/local/go/bin:/root/go/bin:$PATH"

# Install system deps and Go
RUN apt-get update && apt-get install -y \
    curl wget unzip git build-essential libpcap-dev dnsutils \
    python3-dnspython jq ca-certificates libxml2-dev libxslt-dev && \
    curl -OL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    ln -s /usr/local/go/bin/go /usr/bin/go && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

# Install Go tools
RUN go install github.com/haccer/subjack@latest
RUN go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest
RUN go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install github.com/projectdiscovery/httpx/cmd/httpx@latest
RUN go install github.com/lc/gau/v2/cmd/gau@latest
RUN go install github.com/tomnomnom/waybackurls@latest
# Subjack fingerprints
RUN mkdir -p /usr/share/subjack && \
    curl -o /usr/share/subjack/fingerprints.json https://raw.githubusercontent.com/haccer/subjack/master/fingerprints.json

# Install shosubgo
RUN git clone --depth=1 https://github.com/incogbyte/shosubgo.git /opt/shosubgo && \
    cd /opt/shosubgo && go build -o shosubgo main.go && mv shosubgo /usr/bin/ && rm -rf /opt/shosubgo

# Install ParamSpider
RUN git clone --depth=1 https://github.com/devanshbatham/ParamSpider.git /opt/ParamSpider && \
    pip install --no-cache-dir requests urllib3 && \
    chmod +x /opt/ParamSpider/paramspider/main.py

# Install Arjun
# RUN git clone --depth=1 https://github.com/s0md3v/Arjun.git /opt/Arjun && \
#     ln -s /opt/Arjun/arjun /usr/bin/arjun && \
#     chmod +x /opt/Arjun/arjun/__main__.py && \
#     rm -rf /opt/Arjun/.git


# Findomain
RUN wget -q https://github.com/findomain/findomain/releases/download/9.0.3/findomain-linux.zip -O /tmp/findomain.zip && \
    unzip -q /tmp/findomain.zip -d /tmp/ && \
    mv /tmp/findomain /usr/bin/findomain && chmod +x /usr/bin/findomain && rm -rf /tmp/*

# Final app setup
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . /app

CMD ["python3", "main.py"]





