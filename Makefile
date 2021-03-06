CC = gcc
LD = ld
AR = ar
CFLAGS=-g -pipe -Os -Wall -Wsign-compare -Wcast-align -Waggregate-return -Wstrict-prototypes -Wmissing-prototypes -Wmissing-declarations -Wmissing-noreturn -finline-functions -Wmissing-format-attribute -Iinclude

BINS = ber-dump ef-dg2
SLIBS = gber.a
LIBS = 

BER_DUMP_OBJ = ber_dump.o
BER_DUMP_SLIBS = gber.a
BER_DUMP_LIBS =

EF_DG2_OBJ = ef_dg2.o bio_group.o
EF_DG2_SLIBS = gber.a
EF_DG2_LIBS =

GBERA_OBJ = ber_decode.o autober.o

ALL_OBJS = $(BER_DUMP_OBJ) $(GBERA_OBJ) $(EF_DG2_OBJ)
ALL_TARGETS = $(BINS) $(SLIBS) $(LIBS)

AUTOGEN_TARGETS = bio_group.c bio_group.h

TARGET = all

.PHONY: all clean dep

all: dep $(BINS) $(SLIBS) $(LIBS)

dep: Make.dep

Make.dep: Makefile *.c include/*.h $(AUTOGEN_TARGETS)
	$(CC) $(CFLAGS) -MM $(patsubst %.o, %.c, $(ALL_OBJS)) > $@

%.o: Makefile %.c
	$(CC) $(CFLAGS) -c -o $@ $(patsubst %.o, %.c, $@)

bio_group.c bio_group.h: examples/ef-dg2.b
	./autober-gen $^

gber.a: $(GBERA_OBJ)
	$(AR) cr $@ $(GBERA_SLIB) $^

ber-dump: $(BER_DUMP_OBJ) $(BER_DUMP_SLIBS)
	$(CC) $(BER_DUMP_LIBS) $(CFLAGS) -o $@ $(BER_DUMP_SLIBS) $^

ef-dg2: $(EF_DG2_OBJ) $(EF_DG2_SLIBS)
	$(CC) $(EF_DG2_LIBS) $(CFLAGS) -o $@ $(EF_DG2_SLIBS) $^

clean:
	rm -f $(ALL_TARGETS) $(ALL_OBJS) $(AUTOGEN_TARGETS) Make.dep

include Make.dep
