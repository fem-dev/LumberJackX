CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -O2
TARGET = lumberjackx
SRC = src/main.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

clean:
	rm -f $(TARGET) $(TARGET).exe

.PHONY: all clean
