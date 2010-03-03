CC = gcc
LD = ld
AR = ar
CFLAGS=-g -pipe -Os -Wall -Wsign-compare -Wcast-align -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Wmissing-declarations -Wmissing-noreturn -finline-functions -Wmissing-format-attribute

BINS = ber-dump
SLIBS = gber.a
LIBS = pygber.so

BER_DUMP_OBJ = ber_dump.o
BER_DUMP_SLIBS = gber.a
BER_DUMP_LIBS =

GBERA_OBJ = ber_decode.o

PYGBER_OBJ = py_gber.o
PYGBER_SLIBS = gber.a

ALL_OBJS = $(BER_DUMP_OBJ) $(GBERA_OBJ) $(PYGBER_OBJ)
ALL_TARGETS = $(BINS) $(SLIBS) $(LIBS)

TARGET = all

.PHONY: all clean dep

all: dep $(BINS) $(SLIBS) $(LIBS)

dep: Make.dep

Make.dep: Makefile *.c *.h
	$(CC) $(CFLAGS) -MM $(patsubst %.o, %.c, $(ALL_OBJS)) > $@

%.o: Makefile %.c
	$(CC) $(CFLAGS) -c -o $@ $(patsubst %.o, %.c, $@)

gber.a: $(GBERA_OBJ)
	$(AR) cr $@ $(GBERA_SLIB) $^

ber-dump: $(BER_DUMP_OBJ) $(BER_DUMP_SLIBS)
	$(CC) $(BER_DUMP_LIBS) $(CFLAGS) -o $@ $(BER_DUMP_SLIBS) $^

pygber.so: $(PYGBER_OBJ) $(PYGBER_SLIBS)
	$(CC) $(CFLAGS) -shared -o $@ $(PYGBER_SLIBS) $^

clean:
	rm -f $(ALL_TARGETS) $(ALL_OBJS) Make.dep

include Make.dep
