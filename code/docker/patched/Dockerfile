FROM simcoin/base:v1

RUN git clone https://github.com/simonmulser/bitcoin.git
WORKDIR "/bitcoin"
RUN git checkout 14cdc69

RUN ./autogen.sh
RUN ./configure --disable-hardening

RUN make -j

ENV PATH /bitcoin/src:$PATH
RUN mkdir /data
COPY bitcoin.conf /data

EXPOSE 18332
