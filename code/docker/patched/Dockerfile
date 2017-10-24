FROM simcoin/base:v1

RUN git clone https://github.com/simonmulser/bitcoin.git
WORKDIR "/bitcoin"
RUN git checkout simcoin

RUN ./autogen.sh
RUN ./configure

RUN make -j

ENV PATH /bitcoin/src:$PATH
RUN mkdir /data
COPY bitcoin.conf /data

EXPOSE 18332
