DIR_Config   = ./lib/Config
DIR_EPD   = ./lib/e-Paper
DIR_GUI   = ./lib/GUI
DIR_FONTS = ./lib/Fonts
DIR_BIN = ./bin

OBJ_C = $(wildcard ${DIR_Config}/*.c  ${DIR_EPD}/*.c ${DIR_FONTS}/*.c ${DIR_GUI}/*.c main.c)
OBJ_O = $(patsubst %.c,${DIR_BIN}/%.o,$(notdir ${OBJ_C}))

TARGET = eps13in3eutility
CC = gcc

USELIB = USE_BCM2835_LIB
LIB = -lbcm2835 -lm 

MSG = -g -O0 -Wall
DEBUG = -D DEBUG 
CFLAGS += $(MSG) $(DEBUG) -D USE_BCM2835_LIB

$(shell mkdir -p $(DIR_BIN))

${TARGET}:${OBJ_O}
	$(CC) $(CFLAGS) $(OBJ_O) -o $@ $(LIB) -I $(DIR_GUI)

${DIR_BIN}/%.o:$(DIR_Config)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@  

${DIR_BIN}/%.o:$(DIR_GUI)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@ -I $(DIR_Config) -I $(DIR_EPD) -I $(DIR_FONTS)

${DIR_BIN}/%.o:$(DIR_FONTS)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@ 

${DIR_BIN}/%.o:$(DIR_EPD)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@  -I $(DIR_Config)
   
${DIR_BIN}/%.o : main.c 
	$(CC) $(CFLAGS) -c  $< -o $@ $(LIB) -I $(DIR_GUI) -I $(DIR_Config) -I $(DIR_FONTS) -I $(DIR_EPD)

clean :
	rm $(DIR_BIN)/*.* 
	rm $(TARGET) 
