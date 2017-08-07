FROM simcoin-base:latest

RUN git clone https://github.com/simonmulser/bitcoin.git
WORKDIR "/bitcoin"
RUN git checkout c87a0ae

RUN ./autogen.sh
RUN ./configure
RUN make

ENV PATH /bitcoin/src:$PATH
RUN mkdir /data
COPY bitcoin.conf /data

EXPOSE 18332
