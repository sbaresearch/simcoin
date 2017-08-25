FROM simcoin/base:v1

RUN git clone https://github.com/simonmulser/bitcoin.git
WORKDIR "/bitcoin"
RUN git checkout 79f158b

RUN ./autogen.sh
RUN ./configure --disable-hardening
RUN make

ENV PATH /bitcoin/src:$PATH
RUN mkdir /data
COPY bitcoin.conf /data

EXPOSE 18332
