FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update
# install CMash scripts
RUN apt-get update &&\
	apt-get upgrade &&\
	apt-get install git &&\
	apt-get install gcc &&\
	apt-get install g++ &&\
    cd /opt &&\
    git clone https://github.com/dkoslicki/CMash.git &&\
    cd CMash &&\
    pip install -r requirements.txt


# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
