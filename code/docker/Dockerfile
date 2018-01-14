FROM library/ubuntu:xenial-20170119
RUN \
     apt-get update &&\
     apt-get -y install build-essential libtool autotools-dev automake pkg-config libssl-dev libevent-dev bsdmainutils &&\
     apt-get -y install libboost-system-dev libboost-filesystem-dev libboost-chrono-dev libboost-program-options-dev libboost-test-dev libboost-thread-dev &&\
     apt-get -y install software-properties-common &&\
     add-apt-repository ppa:bitcoin/bitcoin &&\
     apt-get -y update &&\
     apt-get -y install libdb4.8-dev libdb4.8++-dev &&\

apt-get -y install git

RUN git clone https://github.com/simonmulser/bitcoin.git
WORKDIR "/bitcoin"
RUN git checkout simcoin

RUN ./autogen.sh
RUN ./configure

RUN make
# multi-threaded
#RUN make -j4

ENV PATH /bitcoin/src:$PATH
RUN mkdir /data

EXPOSE 18332
